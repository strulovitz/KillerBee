#!/usr/bin/env bash
# STT + multimedia provisioning for one KillerBee VM.
# Usage: ./PHASE3_PROVISION_VM.sh <tier>
# tier = worker_tiny, worker_small, dwarfqueen_small, dwarfqueen_medium, giantqueen, rajabee
set -euo pipefail
TIER="${1:?Usage: $0 <tier> (worker_tiny|worker_small|dwarfqueen_small|dwarfqueen_medium|giantqueen|rajabee)}"

echo "=== Provisioning STT+multimedia for tier: $TIER ==="

# 1. System packages
echo "--- Installing system packages ---"
sudo apt-get update -qq
sudo apt-get install -y -qq ffmpeg build-essential cmake git curl wget python3 python3-pip python3-venv

# 2. Create venv
echo "--- Creating Python venv ---"
sudo mkdir -p /opt/killerbee/venv /opt/killerbee/scripts /opt/killerbee/test /opt/killerbee/models
sudo chown -R "$(whoami):$(whoami)" /opt/killerbee
python3 -m venv /opt/killerbee/venv
source /opt/killerbee/venv/bin/activate
pip install --upgrade pip -q

# 3. Tier-specific Python packages
echo "--- Installing Python packages for $TIER ---"
case "$TIER" in
  worker_tiny|worker_small)
    pip install -q numpy soundfile Pillow pytest requests
    # moonshine-onnx: try both known package names
    pip install -q moonshine-onnx 2>/dev/null || pip install -q useful-moonshine 2>/dev/null || echo "WARN: moonshine package not found, will retry later"
    ;;
  dwarfqueen_small|dwarfqueen_medium|giantqueen)
    pip install -q numpy soundfile Pillow pytest requests
    ;;
  rajabee)
    pip install -q numpy soundfile Pillow pytest requests
    pip install -q torch --index-url https://download.pytorch.org/whl/cpu
    pip install -q transformers
    ;;
  *)
    echo "ERROR: unknown tier '$TIER'"
    exit 1
    ;;
esac

# 4. Compile whisper.cpp (skip for pure Moonshine workers)
if [[ "$TIER" != "worker_tiny" && "$TIER" != "worker_small" ]]; then
  echo "--- Compiling whisper.cpp ---"
  mkdir -p /opt/killerbee/src
  cd /opt/killerbee/src
  if [ ! -d whisper.cpp ]; then
    git clone --depth 1 https://github.com/ggerganov/whisper.cpp.git
  fi
  cd whisper.cpp
  make -j"$(nproc)" 2>&1 | tail -3
  echo "  whisper.cpp binary: $(ls -lh main 2>/dev/null || echo 'NOT FOUND')"
fi

# 5. Download STT model weight
echo "--- Downloading STT model for $TIER ---"
source /opt/killerbee/venv/bin/activate
case "$TIER" in
  worker_tiny)
    python3 -c "
try:
    from moonshine_onnx import MoonshineOnnxModel
    model = MoonshineOnnxModel(model_name='moonshine/tiny')
    print('Moonshine Tiny loaded OK')
except Exception as e:
    print(f'Moonshine Tiny load failed: {e}')
" ;;
  worker_small)
    python3 -c "
try:
    from moonshine_onnx import MoonshineOnnxModel
    model = MoonshineOnnxModel(model_name='moonshine/base')
    print('Moonshine Base loaded OK')
except Exception as e:
    print(f'Moonshine Base load failed: {e}')
" ;;
  dwarfqueen_small)
    cd /opt/killerbee/src/whisper.cpp
    bash ./models/download-ggml-model.sh small
    ;;
  dwarfqueen_medium)
    cd /opt/killerbee/src/whisper.cpp
    bash ./models/download-ggml-model.sh medium
    ;;
  giantqueen)
    cd /opt/killerbee/src/whisper.cpp
    bash ./models/download-ggml-model.sh large-v3-turbo
    ;;
  rajabee)
    pip install -q huggingface_hub
    python3 -c "
from huggingface_hub import snapshot_download
snapshot_download('CohereLabs/cohere-transcribe-03-2026', local_dir='/opt/killerbee/models/cohere-transcribe')
print('Cohere Transcribe downloaded OK')
" ;;
esac

echo ""
echo "=== Provisioning complete for tier: $TIER ==="
echo "  Venv: /opt/killerbee/venv"
echo "  Scripts: /opt/killerbee/scripts"
echo "  Models: /opt/killerbee/models or /opt/killerbee/src/whisper.cpp/models"
