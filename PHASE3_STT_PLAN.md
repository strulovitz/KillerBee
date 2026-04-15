# KillerBee Phase 3 — STT + Multimedia Tooling Plan

**Canonical source of truth.** Edit this file in place when things change. Do not add version suffixes. Do not keep SUPERSEDED banners of old files — delete obsolete content and let commit messages explain the change. Git history is the time machine; the working tree holds only the current truth.

---

## Context

The KillerBee VM hive is a hierarchical AI swarm running on one Linux Mint 22.2 host (Intel i9-13900KF, 24 cores / 32 threads, 64 GB RAM, 1.5 TB free disk, **no GPU, CPU-only everywhere**, AVX2 + FMA + AVX-VNNI + F16C present, no AVX-512). The hive runs in 8 virtual machines organized as a tree: one RajaBee at the top, GiantQueens below her, DwarfQueens below them, workers at the bottom. Every VM runs a vision model, an audio STT model, and a text-reasoning LLM — but only one at a time, sequential load/unload — because the host does not have RAM for simultaneous residency of all models everywhere.

This plan specifies the **STT (speech-to-text) layer** and the **multimedia tooling** that every VM needs. The text-reasoning LLM layer (Ollama with qwen3 / llama3 / mistral) and the vision layer (Ollama with qwen2.5-vl / moondream) are covered in `PHASE3_REBUILD_PLAN_V3.md` and are NOT changed here.

**Read these book chapters in `TheDistributedAIRevolution/` before touching this plan:**

- `chapter_11.md` — single-value sensors, *"information is a property of communication"*, Pi+Arduino cortex+spine hardware framing. (Out of scope for the VM test bench, but read for the architectural framing.)
- `chapter_12.md` — sound and image, sub-sampling principle, quadrant + offset-grid cut, give-the-boss-a-low-resolution-view insight. **This is the chapter the VM experiment tests.** Read closely.
- `chapter_13.md` — 3D and 4D mapping, drone-swarm-in-a-bunker story. Out of scope for the VM test bench.
- `chapter_14.md` — the vector mesh, RAG over reality, many nets over one world. Out of scope for the VM test bench.
- `chapter_15.md` — *The Octopus Is Slippery* FAQ. Especially the section *"One more slippery point — what you can test on a desk, and what you cannot"* which explicitly defines the test bench scope.

---

## Hard rules

1. **CPU-only everywhere.** No GPU, no VRAM, no CUDA. Every Python wheel is the CPU build. `onnxruntime` not `onnxruntime-gpu`. `torch` from `https://download.pytorch.org/whl/cpu`. All compiled binaries target x86_64 with AVX2/FMA.
2. **English only.** No multilingual filtering. English-only models are preferred when they are smaller.
3. **No license filter.** Every model in this plan is MIT or Apache 2.0 anyway, but never dismiss a candidate based on license.
4. **No fabrication.** Every model name, quantization filename, and disk size in this plan is verified against the live Hugging Face model card before committing. If a number cannot be verified, say "unverified" next to it.
5. **Sequential load/unload at every tier.** The VMs cannot afford simultaneous resident models. Load vision → run → unload → load STT → run → unload → load reasoner → run → unload. Every tier.
6. **RajaBee keeps her big text reasoner unchanged from V3.** Do NOT fuse STT with the reasoner at the top tier via a SALM. Canary Qwen 2.5B and every other SALM are explicitly OFF the ladder because they cap the reasoner's LLM backbone at a size far smaller than the RajaBee needs.
7. **No vector mesh. No faiss. No chromadb. No sentence-transformers. No embedding model of any kind on any VM.** The Chapter 14 mesh is explicitly out of scope — the mesh requires real physical sensors converging on real anchor points of meaning in real space, and synthetic file data cannot test it. See chapter 15 for the full reasoning.
8. **No single-value sensors.** No simulated temperature, no fake gas detectors, no `random.uniform()` standing in for a CO2 chip. Chapter 11 is out of scope for the VM test bench.
9. **No Ollama for STT.** Ollama stays as the runtime for text reasoners (from V3) and vision (from V3). STT runs on `moonshine-onnx`, `whisper.cpp`, or HF Transformers CPU only.
10. **Only the RajaBee writes to any shared store.** Lower tiers pass text reports upward and do not write to any database. This rule is theoretical for now because the mesh is out of scope for the test bench, but honor it in the architecture.
11. **Sequential one-by-one VM provisioning.** Do NOT run provisioning on multiple VMs concurrently even though the 24-core i9 could easily handle it. One VM at a time, end to end. Fix any bug on VM 1 immediately by editing `PHASE3_PROVISION_VM.sh` in place so every subsequent VM picks up the fix. Reason: human debuggability under time pressure, not machine capacity.

---

## The STT ladder (final, verified against Hugging Face)

Three model families. Two-and-a-half runtimes.

| Bracket | GOLD | SILVER | Params | License | Runtime |
|---|---|---|---|---|---|
| **tiny (worker)** | Moonshine Tiny | Whisper tiny | 27M / 39M | MIT / MIT | `moonshine-onnx` / `whisper.cpp` |
| **small (worker)** | Moonshine Base | Whisper base | 61M / 74M | MIT / MIT | `moonshine-onnx` / `whisper.cpp` |
| **medium-small (DwarfQueen)** | Whisper small | Whisper base | 244M | MIT | `whisper.cpp` |
| **medium (DwarfQueen higher)** | Whisper medium | Whisper small | 769M | MIT | `whisper.cpp` |
| **medium-big (GiantQueen)** | Whisper Large v3 Turbo | Whisper medium | 809M | MIT | `whisper.cpp` |
| **big (RajaBee STT — reasoner stays separate and unchanged)** | Cohere Transcribe 03-2026 | Whisper Large v3 (non-turbo) | 2B / 1.55B | Apache 2.0 / MIT | HF Transformers CPU / `whisper.cpp` |

**Model URLs (verified on Hugging Face):**

- `huggingface.co/UsefulSensors/moonshine` — Moonshine Tiny (27M) and Base (61M). MIT. English only. **Only those two variants exist — there is no "Medium Streaming 245M" despite what Google AI Overview may claim.** Verified by direct URL fetch.
- `huggingface.co/ggerganov/whisper.cpp` — canonical source for Whisper `ggml-*.bin` files that `whisper.cpp` consumes. Verify exact filenames (e.g., `ggml-small.bin`, `ggml-medium.bin`, `ggml-large-v3-turbo-q5_0.bin`, `ggml-large-v3.bin`) at provisioning time with the `models/download-ggml-model.sh` script in the whisper.cpp repo.
- `huggingface.co/CohereLabs/cohere-transcribe-03-2026` — 2B params, Apache 2.0, 14 languages including English, **#1 on HF Open ASR Leaderboard (5.42% avg WER, RTFx 524.88 on GPU)**, native `transformers` library CPU inference per the model card, **24 quantized variants** available on the model tree. Verified by direct URL fetch.

**Models explicitly dropped (do not revisit without new evidence):**

- **Parakeet TDT 0.6B v3 and 1.1B** — No ONNX artifacts published on the HF model cards. Runtime options were NeMo CPU (heavy, unproven) or self-export (engineering risk). Dropped entirely.
- **Qwen3-ASR 0.6B and 1.7B** — The tight C++ runtime `qwen3-asr.cpp` has only 7 commits, no releases, and Metal-first docs. HF Transformers CPU path works but is slow and creates a second transformers install on the non-RajaBee tiers. Dropped to keep the ladder simple.
- **Canary Qwen 2.5B SALM** — SALM fusion would cap the RajaBee reasoner at Qwen3-1.7B which is far too small. Dropped.

---

## Multimedia tooling — every VM needs this

### System packages (apt)

| Package | Disk | Purpose |
|---|---|---|
| `ffmpeg` | ~60 MB | **The single most important tool.** Audio downsampling (boss's gestalt), audio slicing (worker chunks), video frame extraction if we ever add that, format conversion. Every STT runtime expects 16 kHz mono WAV and ffmpeg produces it. |
| `build-essential`, `cmake`, `git`, `curl`, `wget` | ~450 MB | Build toolchain for `whisper.cpp`. |
| `python3` + `python3-pip` + `python3-venv` | ~130 MB | Per-VM isolated Python environments. |

### Python packages (per-VM venv at `/opt/killerbee/venv/`)

| Package | Approx disk | Purpose |
|---|---|---|
| `numpy` | ~50 MB | Required transitively by everything |
| `soundfile` | ~10 MB | Read/write WAV files in Python |
| `Pillow` | ~15 MB | Image downsampling (boss gestalt), quadrant cutting (children slices), offset-grid second-cut trick from Ch 12 |
| `moonshine-onnx` (verify exact PyPI package name at install time — might be `useful-moonshine`) | ~50 MB + ~250 MB ONNX Runtime transitive dep | Moonshine native runtime for worker tiers |
| `transformers` + `torch` (CPU-only wheels, **RajaBee tier only**) | ~900 MB combined | Cohere Transcribe inference. Install via `pip install torch --index-url https://download.pytorch.org/whl/cpu` then `pip install transformers`. |
| `pytest` | ~10 MB | Unit-test the slicing helpers so we catch broken cuts before live tests use them |
| `requests` | ~5 MB | HTTP side of drone-to-drone communication, likely already pulled in by the GiantHoneyBee wrappers from V3 |

### Compiled-from-source binaries

| Binary | Source | Built size | Needed on |
|---|---|---|---|
| `whisper.cpp` | `github.com/ggerganov/whisper.cpp` | ~20 MB | every tier except workers that use Moonshine only; also as universal silver on every VM |
| `llama.cpp` | `github.com/ggerganov/llama.cpp` | ~80 MB | already in V3 for text reasoners — reuse existing install, do not rebuild |

### Custom helper scripts (Desktop writes these, tracked in KillerBee repo)

| Script | Purpose |
|---|---|
| `slice_audio.py` | Input: one WAV file and a config. Output: one downsampled full-duration gestalt file for the parent, plus N full-quality chunk files for the workers. Uses `ffmpeg` under the hood. |
| `slice_image.py` | Input: one image and a config. Output: one downsampled full-area gestalt image for the parent, plus N full-resolution tile files for the workers, plus optionally a second offset-grid set of tiles for the Chapter 12 boundary-recovery trick. Uses `Pillow`. |
| `run_stt.py` | Loads the current tier's STT model, runs it on one audio file, prints transcription to stdout. Each tier has its own config naming the STT model and runtime. Handles load/unload discipline internally. |
| `run_reasoner.py` | Loads the current tier's text reasoner LLM (via Ollama), takes a prompt built from child reports plus the tier's own gestalt observations, prints integrated paragraph to stdout. |
| `integrate_children.py` | Takes all child reports for this tier plus this tier's own gestalt observation, constructs a prompt, calls `run_reasoner.py`, returns the integrated paragraph for this tier. |

---

## Per-tier disk budget (tooling + model weights)

| Tier | Tooling | STT weight | Total (STT layer only) |
|---|---|---|---|
| Worker (Moonshine Tiny) | ~400 MB (Python + ffmpeg + Pillow + soundfile + numpy + moonshine-onnx + venv) | ~30 MB | **~430 MB** |
| Worker (Moonshine Base) | same | ~80 MB | **~480 MB** |
| DwarfQueen (Whisper small) | ~480 MB (previous + whisper.cpp binary) | ~250 MB (ggml-small.bin) | **~730 MB** |
| DwarfQueen (Whisper medium) | same | ~750 MB (ggml-medium.bin) | **~1.2 GB** |
| GiantQueen (Whisper Large v3 Turbo) | same | ~800 MB quantized or ~1.6 GB FP16 | **~1.3–2.1 GB** |
| RajaBee STT (Cohere Transcribe 2B) | ~1.3 GB (previous + transformers + torch CPU wheels) | ~2 GB Q4 or ~4 GB FP16 | **~3.3–5.3 GB** |

**Plus** the V3-allocated disk for the text reasoner (Ollama + LLM weight at each tier) and vision models — those numbers do not change and are covered in `PHASE3_REBUILD_PLAN_V3.md`.

**Total STT + tooling footprint across 8 VMs:** rough worst case **~10–12 GB**, fits easily in the 1.5 TB free on the host.

**RAM impact:** sequential load/unload means peak RAM per VM is bounded by whichever single model is currently loaded at that moment. Cohere Transcribe 2B in Q4 ≈ ~2 GB RAM. Whisper Large v3 Turbo quantized ≈ ~1 GB. Moonshine Tiny ≈ under 100 MB. None of these exceed the V3-allocated RAM per tier because sequential discipline prevents two models from being resident simultaneously.

---

## Provisioning strategy — SEQUENTIAL, one VM at a time

**Why not parallelized:** Nir's explicit rule. Desktop needs full attention to debug one VM at a time. If 7 VMs hit errors simultaneously, Desktop has to prioritize under time pressure and is more likely to miss or paper over a real bug. The i9-13900KF could handle 4–8 concurrent provisions easily, but we choose slower-and-safer over faster-and-confusing.

**Expected wall-clock time:** ~10–15 minutes per VM × 8 VMs = **~80–120 minutes** for the full hive. This is the honest budget.

**Rule:** Provision VM 1 end to end. Apt → pip → builds → model weight fetch → integration test → one real STT pass on a real audio file. Only when VM 1 is fully green, move to VM 2. Fix any bug in `PHASE3_PROVISION_VM.sh` in place as soon as you find it — every subsequent VM picks up the fix from the current script, not from an earlier broken version.

**Provisioning script outline** (full version lives at `KillerBee/PHASE3_PROVISION_VM.sh`, to be written/rewritten by Desktop as the canonical file):

```bash
#!/usr/bin/env bash
# Usage: ./PHASE3_PROVISION_VM.sh <tier>
# tier ∈ {worker_tiny, worker_small, dwarfqueen_small, dwarfqueen_medium, giantqueen, rajabee}
set -euo pipefail

TIER="$1"

# 1. System packages
sudo apt update
sudo apt install -y ffmpeg build-essential cmake git curl wget python3 python3-pip python3-venv

# 2. Create per-VM venv
python3 -m venv /opt/killerbee/venv
source /opt/killerbee/venv/bin/activate
pip install --upgrade pip

# 3. Tier-specific Python packages
case "$TIER" in
  worker_tiny|worker_small)
    pip install numpy soundfile Pillow pytest requests moonshine-onnx
    ;;
  dwarfqueen_small|dwarfqueen_medium|giantqueen)
    pip install numpy soundfile Pillow pytest requests
    # whisper.cpp is compiled below
    ;;
  rajabee)
    pip install numpy soundfile Pillow pytest requests
    pip install torch --index-url https://download.pytorch.org/whl/cpu
    pip install transformers
    ;;
esac

# 4. Compile whisper.cpp (needed on every tier except pure Moonshine workers)
if [[ "$TIER" != "worker_tiny" && "$TIER" != "worker_small" ]]; then
  mkdir -p /opt/killerbee/src
  cd /opt/killerbee/src
  [ -d whisper.cpp ] || git clone https://github.com/ggerganov/whisper.cpp.git
  cd whisper.cpp && make -j"$(nproc)"
fi

# 5. Download the tier's STT model weight
case "$TIER" in
  worker_tiny) python -c "from moonshine_onnx import load; load('moonshine/tiny')" ;;
  worker_small) python -c "from moonshine_onnx import load; load('moonshine/base')" ;;
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
    python -c "from huggingface_hub import snapshot_download; snapshot_download('CohereLabs/cohere-transcribe-03-2026', local_dir='/opt/killerbee/models/cohere-transcribe')"
    ;;
esac

# 6. Run a smoke test on a known audio file
python /opt/killerbee/scripts/run_stt.py --tier "$TIER" --input /opt/killerbee/test/smoke_test.wav
```

*Adjust to actual PyPI package names (`moonshine-onnx` vs `useful-moonshine`) and actual `download-ggml-model.sh` tag names (`large-v3-turbo` may be named differently in the whisper.cpp repo) at implementation time. This outline is a starting point, not a frozen specification.*

---

## Canonical deliverables in this repo

Three files — no version suffixes, edit in place:

1. **`PHASE3_STT_PLAN.md`** (this file) — the canonical STT plan.
2. **`PHASE3_STT_VERIFICATION_LOG.md`** — per-model verification log: URL hit, date+time of verification, exact model name, license, parameter count, quantization variants actually on the HF page, exact filenames for Whisper `ggml-*.bin` artifacts, anything that contradicts this plan. One entry per model in the ladder. Update in place when models are re-verified later.
3. **`PHASE3_PROVISION_VM.sh`** — runnable provisioning script, tier-aware, idempotent, sequential discipline. Updated in place when bugs are fixed during VM 1 shakedown.

**Deleted (git history preserves them):** all `*_2026-04-15*.md` and `*_v2*.md` STT files from earlier research rounds. Do not recreate them. Do not add version suffixes to new files.

---

## Out of scope (the test bench cannot faithfully test these)

See `TheDistributedAIRevolution/chapter_15.md` section *"One more slippery point — what you can test on a desk, and what you cannot"* for the full reasoning. Quick list:

- Ch 14 vector mesh (requires real physical sensors + real anchor points of meaning)
- Ch 11 distributed single-value sensors (requires real physical gas/temperature/light sensors)
- Real 3D/4D physical mapping (no drones, no cameras moving through physical space)
- Stigmergy / pheromone trails (no real environment)
- Faraday-bunker demonstration (no radio-hostile environment)
- Multi-drone physical communication mesh (our "drones" are VMs sharing a local network)

*The untestable parts are untestable only because Nir does not own any drones — not because the architecture is wishful. They stay in the book as architecture for a real-world build with real hardware.*

---

*Canonical plan. Edit in place when things change. Git is the time machine.*
