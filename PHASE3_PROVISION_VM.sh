#!/usr/bin/env bash
# PHASE3_PROVISION_VM.sh — KillerBee Phase 3 V4 per-VM provisioning
#
# Usage:  sudo bash PHASE3_PROVISION_VM.sh <tier>
#   tier ∈ { worker | dwarfqueen | giantqueen | rajabee }
#
# Idempotent: safe to re-run. Each step is guarded so partial failures do not
# require a clean re-provision. Installs STT + multimedia tooling per the v2
# ladder in PHASE3_STT_AND_TOOLING_2026-04-15_v2.md.
#
# Scope rules enforced (per v2 brief):
#   - CPU-only everywhere. No onnxruntime-gpu. No CUDA. No flash-attn. No vllm.
#   - No vector mesh. No faiss / chromadb / sentence-transformers.
#   - No single-value sensors. No SALM fusion at the rajabee.
#   - Sequential load/unload discipline is a runtime concern, not a provisioning concern.

set -euo pipefail

TIER="${1:-}"
if [[ -z "$TIER" ]]; then
    echo "usage: sudo bash $0 <tier>"
    echo "  tier ∈ { worker | dwarfqueen | giantqueen | rajabee }"
    exit 2
fi

case "$TIER" in
    worker|dwarfqueen|giantqueen|rajabee) ;;
    *)
        echo "error: unknown tier '$TIER'"
        exit 2
        ;;
esac

KB_ROOT="/opt/killerbee"
VENV_DIR="$KB_ROOT/venv"
SRC_DIR="$KB_ROOT/src"
TIER_MARKER="$KB_ROOT/.tier"

log() { echo "[provision:$TIER] $*"; }

require_root() {
    if [[ $EUID -ne 0 ]]; then
        echo "error: this script must be run as root (sudo)"
        exit 1
    fi
}

# --- Step 1: apt-install system packages ---------------------------------
install_system_packages() {
    log "step 1: system packages"
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -qq
    apt-get install -y --no-install-recommends \
        ffmpeg \
        build-essential \
        cmake \
        pkg-config \
        git \
        curl \
        wget \
        python3 \
        python3-pip \
        python3-venv \
        python3-dev \
        libsndfile1
}

# --- Step 2: create layout + venv ----------------------------------------
ensure_layout() {
    log "step 2: /opt/killerbee layout"
    mkdir -p "$KB_ROOT" "$SRC_DIR"
    if [[ ! -d "$VENV_DIR" ]]; then
        log "  creating venv at $VENV_DIR"
        python3 -m venv "$VENV_DIR"
    else
        log "  venv already exists, reusing"
    fi
    # shellcheck disable=SC1091
    source "$VENV_DIR/bin/activate"
    pip install --upgrade pip setuptools wheel --quiet
}

# --- Step 3: tier-specific pip installs ----------------------------------
# Every tier gets the base stack (numpy, soundfile, Pillow, whisper.cpp fallback).
# Higher tiers add onnxruntime, torch CPU, transformers, etc.
pip_install_base() {
    log "  pip: base stack (numpy, soundfile, Pillow, pytest, requests, huggingface_hub)"
    pip install --quiet \
        numpy \
        soundfile \
        Pillow \
        pytest \
        requests \
        huggingface_hub
}

pip_install_moonshine() {
    log "  pip: useful-moonshine (git install per model card)"
    # May fail if git is unreachable; log and continue — worker can still use whisper.cpp fallback.
    pip install --quiet \
        "useful-moonshine @ git+https://github.com/usefulsensors/moonshine.git" \
        || log "  WARN: useful-moonshine install failed; worker will use whisper.cpp bronze fallback"
}

pip_install_onnx_cpu() {
    log "  pip: onnxruntime (CPU-only wheel)"
    pip install --quiet onnxruntime
}

pip_install_torch_cpu() {
    log "  pip: torch (CPU-only wheel from pytorch.org)"
    pip install --quiet torch --index-url https://download.pytorch.org/whl/cpu
}

pip_install_transformers_stack() {
    log "  pip: transformers + deps for Cohere Transcribe / Qwen3-ASR CPU fallback"
    pip install --quiet \
        "transformers>=5.4.0,<6" \
        librosa \
        sentencepiece \
        protobuf
}

run_pip_for_tier() {
    log "step 3: pip installs for tier '$TIER'"
    pip_install_base
    case "$TIER" in
        worker)
            pip_install_moonshine
            ;;
        dwarfqueen)
            pip_install_moonshine
            pip_install_onnx_cpu
            pip_install_torch_cpu
            pip_install_transformers_stack
            ;;
        giantqueen)
            pip_install_onnx_cpu
            pip_install_torch_cpu
            pip_install_transformers_stack
            ;;
        rajabee)
            pip_install_torch_cpu
            pip_install_transformers_stack
            ;;
    esac
}

# --- Step 4: compile C++ binaries (once, guarded) ------------------------
clone_and_build() {
    local repo_url="$1"
    local dir_name="$2"
    local build_cmd="$3"
    local target_dir="$SRC_DIR/$dir_name"

    if [[ -d "$target_dir/.git" ]]; then
        log "  $dir_name already cloned, pulling latest"
        git -C "$target_dir" pull --quiet || log "  WARN: git pull failed for $dir_name"
    else
        log "  cloning $repo_url"
        git clone --quiet --depth 1 "$repo_url" "$target_dir" \
            || { log "  WARN: clone failed for $dir_name; skipping build"; return 0; }
    fi

    log "  building $dir_name"
    (cd "$target_dir" && eval "$build_cmd") \
        || log "  WARN: build failed for $dir_name; continuing (fallback path may still work)"
}

build_binaries_for_tier() {
    log "step 4: C++ binaries for tier '$TIER'"
    # whisper.cpp: universal bronze fallback, every tier
    clone_and_build \
        "https://github.com/ggerganov/whisper.cpp.git" \
        "whisper.cpp" \
        "make -j$(nproc)"

    case "$TIER" in
        dwarfqueen|giantqueen|rajabee)
            # llama.cpp already in V3 text reasoner stack; reuse its binary if present
            if [[ ! -x "$SRC_DIR/llama.cpp/main" ]]; then
                clone_and_build \
                    "https://github.com/ggerganov/llama.cpp.git" \
                    "llama.cpp" \
                    "make -j$(nproc)"
            else
                log "  llama.cpp binary already present from V3, reusing"
            fi
            ;;
    esac

    case "$TIER" in
        giantqueen|dwarfqueen)
            # qwen3-asr.cpp: GGML CPU backend for Qwen3-ASR silvers/golds
            # NOTE: this repo is young (7 commits as of 2026-04-15). Build failure is non-fatal;
            # fallback to HF transformers CPU inference is installed via the pip step.
            clone_and_build \
                "https://github.com/predict-woo/qwen3-asr.cpp.git" \
                "qwen3-asr.cpp" \
                "mkdir -p build && cd build && cmake -DCMAKE_BUILD_TYPE=Release .. && cmake --build . -j$(nproc)"
            ;;
    esac
}

# --- Step 5: write tier marker -------------------------------------------
write_tier_marker() {
    log "step 5: tier marker"
    {
        echo "tier=$TIER"
        echo "provisioned_at=$(date -Iseconds)"
        echo "provisioner_version=PHASE3_PROVISION_VM.sh/v2-2026-04-15"
        echo "host=$(hostname)"
    } > "$TIER_MARKER"
}

# --- Step 6: summary ------------------------------------------------------
print_summary() {
    log "step 6: summary"
    # shellcheck disable=SC1091
    source "$VENV_DIR/bin/activate"
    echo "----- installed pip packages (top-level) -----"
    pip list --format=columns 2>/dev/null | grep -Ei \
        "numpy|soundfile|Pillow|onnxruntime|torch|transformers|moonshine|librosa|sentencepiece|protobuf|huggingface|pytest|requests" \
        || true
    echo "----- built C++ binaries -----"
    ls -la "$SRC_DIR" 2>/dev/null || true
    echo "----- tier marker -----"
    cat "$TIER_MARKER" 2>/dev/null || true
    log "done."
}

# --- Main ----------------------------------------------------------------
main() {
    require_root
    install_system_packages
    ensure_layout
    run_pip_for_tier
    build_binaries_for_tier
    write_tier_marker
    print_summary
}

main "$@"
