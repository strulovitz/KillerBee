# Phase 3 STT + Multimedia Tooling — 2026-04-15 v2

**Author:** Desktop Claude (Opus 4.6, 1M context), Linux Mint 22.2 host on i9-13900KF
**Source brief:** `WaggleDance/DESKTOP_KILLERBEE_STT_AND_TOOLING_BRIEF_2026-04-15_v2.md`
**Replaces:** `KillerBee/PHASE3_STT_RESEARCH_2026-04-15.md` and `KillerBee/PHASE3_STT_NIR_SEARCH_QUERIES_2026-04-15.md` (both now carry SUPERSEDED banners; kept in git as historical reference)
**Companion files:**
- `KillerBee/PHASE3_STT_VERIFICATION_LOG_2026-04-15_v2.md` — per-model audit trail (live HF fetches, 2026-04-15)
- `KillerBee/PHASE3_PROVISION_VM.sh` — runnable tier-aware provisioning script

**Status:** Research + plan + provisioning script. V3/V4 rebuild remains ON HOLD pending Nir review.

---

## Section 1 — Context and scope

The v1 STT research round got the wrong framing. Nir's actual constraints are: **CPU-only, English-only, no license filter, no mesh, no single-value sensors, no SALM fusion, Whisper is the bronze fallback not the default, sequential load/unload at every tier.** The v1 files inverted most of this, treating Whisper as the ladder and multilingual as the top priority. They have been marked SUPERSEDED in place; their ladders no longer apply.

**Chapters read before writing this file** (all in `TheDistributedAIRevolution`):

- **Chapter 11** (single-value sensors) — read for completeness. The VM test bench cannot test gradient fields without physical sensors. **Out of scope.**
- **Chapter 12** (sound and image, sub-sampling, offset-grid cut) — the architectural backbone of what the test bench actually exercises. The cut-and-pass-text arc for audio and images is exactly what every tier runs on this hardware. **In scope and central.**
- **Chapter 14** (vector mesh) — read for completeness. The test bench cannot test a mesh because the drones do not exist. **Out of scope.** No faiss, chromadb, sentence-transformers, or embedding runtime on any VM.
- **Chapter 15** (The Octopus Is Slippery) — including the new section *"One more slippery point — what you can test on a desk, and what you cannot"* which explicitly draws the in-scope / out-of-scope line the v2 brief enforces.

**What the test bench validates (in scope):**
1. Hierarchy itself (workers → DwarfQueens → GiantQueens → RajaBee) on CPU VMs.
2. Sequential load/unload dance at every tier — vision → unload → STT → unload → reasoner → unload.
3. Cut-and-pass-text arc for synthetic audio and image files.
4. Per-tier gestalt + children's-details integration at every level.

**What the test bench explicitly does NOT validate:**
1. The vector mesh / RAG-over-reality (Chapter 14) — no embeddings on any VM.
2. Single-value sensors (Chapter 11) — no fake thermometers.
3. Real 3D/4D mapping, Faraday-bunker argument, stigmergy — all physical-world.
4. SALM fusion at the RajaBee — Canary Qwen 2.5B is explicitly off the ladder.

## Section 2 — Hard rules (copied verbatim from brief for on-page enforcement)

1. **CPU-only everywhere.** No GPU, no VRAM, no CUDA. Every runtime, wheel, binary targets x86_64 + AVX2/FMA.
2. **English only.** No multilingual filtering. English-only models are preferred because they are smaller/faster.
3. **No license filter.** Apache 2.0 / MIT / CC-BY-4.0 are all acceptable. CC-BY-NC is absent from this ladder anyway.
4. **No fabrication.** Every number below was read off a live HF card on 2026-04-15. See the verification log for the audit trail.
5. **Sequential load/unload at every tier.** No simultaneous resident models on any VM. Peak per-VM RAM is bounded by the single largest loaded model at any moment.
6. **RajaBee text reasoner unchanged from V3.** STT and text reasoning are separate models at separate moments in the cycle. **Canary Qwen 2.5B SALM is OFF.**
7. **No vector mesh. No faiss / chromadb / sentence-transformers / any embedding runtime.** The Chapter 14 mesh is out of scope for the test bench per the new Chapter 15 section.
8. **No single-value sensors.** No `random.uniform()` stand-ins. Chapter 11 is out of scope.
9. **No Ollama for STT.** Ollama stays in the plan for text-reasoning LLMs (unchanged from V3). STT routes through whisper.cpp / faster-whisper / ONNX Runtime CPU / Moonshine native / qwen3-asr.cpp / HF Transformers CPU depending on the bracket.

## Section 3 — The verified STT ladder (gold + silver per bracket)

**Every candidate was re-verified today against its live HF model card. Full per-model audit trail in `PHASE3_STT_VERIFICATION_LOG_2026-04-15_v2.md`.**

### Bracket 1 — tiny (worker tier, lowest in the tree)

| Rank | Model | Params | License | Runtime (CPU) | Languages | Footprint |
|---|---|---|---|---|---|---|
| **GOLD** | `UsefulSensors/moonshine` — tiny variant (`moonshine/tiny`) | 27 M | MIT | `useful-moonshine` pip package (Keras backend = PyTorch CPU), or `moonshine-onnx` ONNX path | English only | ~30 MB ONNX (measure at download) |
| **SILVER** | `Qwen/Qwen3-ASR-0.6B` | 0.9 B actual | Apache 2.0 | `qwen3-asr.cpp` (GGML, CPU backend on Linux) OR HF Transformers CPU with BF16→FP32 cast | English (uses one of 30 supported) | ~1 GB at INT4 quant (exact filename from HF files tree at download) |

**Pick rationale:** Moonshine Tiny is purpose-built for memory-constrained edge CPUs and has the smallest footprint on the entire ladder. The Qwen3-ASR-0.6B silver is there because (a) it is actively maintained, (b) it has 17 quantized variants on HF, (c) it comes with a C++ CPU runtime via `qwen3-asr.cpp`, and (d) at the worker tier we would only invoke it at INT4 quant to keep RAM under 1 GB. **Silver risk flagged:** `qwen3-asr.cpp` has 7 commits and Metal-first documentation — see verification log entry 8.

### Bracket 2 — small

| Rank | Model | Params | License | Runtime (CPU) | Languages | Footprint |
|---|---|---|---|---|---|---|
| **GOLD** | `UsefulSensors/moonshine` — base variant (`moonshine/base`) | 61 M | MIT | `useful-moonshine` / `moonshine-onnx` | English only | ~80 MB ONNX (measure at download) |
| **SILVER** | `nvidia/parakeet-tdt-0.6b-v3` | 0.6 B | CC-BY-4.0 | ONNX Runtime CPU (if ONNX export available — see risk below) OR NeMo CPU | 25 European incl. en | ~600 MB FP32, ~200 MB INT8 if ONNX export succeeds |

**Pick rationale:** Moonshine Base preserves the tiny-model latency advantage with more capacity. Parakeet v3 0.6B is the silver because its 6.34% average WER on the HF Open ASR Leaderboard is meaningfully better than Moonshine Base at the cost of ~7× the disk footprint. **Silver risk flagged:** v2 brief assumes an ONNX Runtime CPU path for Parakeet; the HF card does not publish an ONNX artifact. Will be verified at download time — if ONNX export via NeMo tooling fails, fall back to NeMo CPU inference or re-promote Moonshine to both tiers.

### Bracket 3 — medium-small (DwarfQueen tier)

| Rank | Model | Params | License | Runtime (CPU) | Languages | Footprint |
|---|---|---|---|---|---|---|
| **GOLD** | `nvidia/parakeet-tdt-0.6b-v3` | 0.6 B | CC-BY-4.0 | ONNX Runtime CPU *if* ONNX available, else NeMo CPU | 25 European incl. en | ~600 MB FP32 / ~200 MB INT8 |
| **SILVER** | `Qwen/Qwen3-ASR-0.6B` | 0.9 B | Apache 2.0 | `qwen3-asr.cpp` | 30 langs incl. en | ~1–2 GB depending on quant |

**Pick rationale:** Parakeet v3 0.6B is the speed king in this class on the HF ASR leaderboard (LibriSpeech 1.93 / 3.59). Qwen3-ASR 0.6B is a close second on LibriSpeech (2.11 / 4.55) and has 17 quant variants for flexibility at the DwarfQueen tier where RAM budgets start to allow more headroom. **Same ONNX-export risk on the gold** as bracket 2; same fallback path (NeMo CPU, or promote the silver).

### Bracket 4 — medium

| Rank | Model | Params | License | Runtime (CPU) | Languages | Footprint |
|---|---|---|---|---|---|---|
| **GOLD** | `nvidia/parakeet-tdt-1.1b` | 1.1 B | CC-BY-4.0 | ONNX Runtime CPU *if* ONNX available, else NeMo CPU | **English only** (lowercase alphabet) | ~1.1 GB FP32 (no ONNX path confirmed) |
| **SILVER** | `openai/whisper-large-v3-turbo` | 809 M | MIT | `whisper.cpp` (CPU GGML) | 99 multilingual | 547 MiB q5_0 / 834 MiB q8_0 / 1.5 GiB FP16 |

**Pick rationale:** Parakeet 1.1B gives the best LibriSpeech WER on the entire ladder in its weight class (1.39 clean / 2.62 other). It is English-only, which matches v2 constraints perfectly. The whisper-large-v3-turbo silver is the universal bronze fallback promoted to silver at this bracket — it runs on `whisper.cpp` without any ONNX uncertainty. **Same ONNX risk on the gold as brackets 2 and 3.**

### Bracket 5 — medium-big (GiantQueen tier)

| Rank | Model | Params | License | Runtime (CPU) | Languages | Footprint |
|---|---|---|---|---|---|---|
| **GOLD** | `Qwen/Qwen3-ASR-1.7B` | 2 B | Apache 2.0 | `qwen3-asr.cpp` (GGML CPU backend) OR HF Transformers CPU | 30 langs + 22 Chinese dialects + en accents | ~4 GB BF16 native, ~1 GB INT4 quant |
| **SILVER** | `openai/whisper-large-v3-turbo` | 809 M | MIT | `whisper.cpp` | 99 multilingual | as above |

**Pick rationale:** Qwen3-ASR 1.7B has 1.65M downloads/month (most-downloaded STT on HF by a wide margin as of 2026-04-15) and best-in-class WER for its size (LibriSpeech 1.63 / 3.38). It has 10 quantized variants on HF. The GiantQueen has the RAM headroom to load it at INT4 under 2 GB. **Silver risk flagged:** `qwen3-asr.cpp` project maturity (7 commits). Fallback is HF Transformers CPU inference if the GGML build is not stable enough; or whisper-large-v3-turbo for the battle-tested route.

### Bracket 6 — big (RajaBee STT; text reasoner is separate and unchanged from V3)

| Rank | Model | Params | License | Runtime (CPU) | Languages | Footprint |
|---|---|---|---|---|---|---|
| **GOLD** | `CohereLabs/cohere-transcribe-03-2026` | 2 B | Apache 2.0 | HF Transformers native (`CohereAsrForConditionalGeneration`, `transformers>=5.4.0`) | 14 incl. en | ~2 GB Q4 quant / ~4 GB FP16 (exact filename from 24 variants at download) |
| **SILVER** | `Qwen/Qwen3-ASR-1.7B` | 2 B | Apache 2.0 | `qwen3-asr.cpp` | 30 + 22 dialects | as bracket 5 |

**Pick rationale:** Cohere Transcribe 03-2026 is **#1 on the HF Open ASR Leaderboard with 5.42% average WER** — the best documented open ASR system in its weight class as of the release date 2026-03-26. It uses HF Transformers native inference, so no extra C++ runtime build is needed on the RajaBee VM. 24 quant variants give flexibility. Qwen3-ASR 1.7B is the silver because it is the second-best candidate on this ladder at 2 B params and uses a completely different runtime path (`qwen3-asr.cpp`), so if Cohere's Transformers path has a `trust_remote_code` or dependency issue, the fallback is orthogonal and will not fail in the same way.

**Explicit non-goal at the big tier:** NO SALM fusion. Canary Qwen 2.5B (which bundles STT with Qwen3-1.7B as a fused language model) is off the ladder. Cohere Transcribe transcribes audio to text; the RajaBee's big text reasoner runs separately in its own load/run/unload slot.

**Universal bronze fallback (any bracket, any failure):** `openai/whisper-large-v3-turbo` on `whisper.cpp` at q5_0 or q8_0 quant. It is MIT, runs on every CPU, is supported by every STT runtime in existence, and has a multi-year production track record. If anything in the ladder falls over during the rebuild, this is the universal escape hatch.

## Section 4 — Multimedia tooling (every VM, same set)

### System-level packages (apt)

| Package | Approx disk | Purpose |
|---|---|---|
| `ffmpeg` | ~60 MB | Audio downsampling for the parent's gestalt, audio slicing for workers, format conversion to 16 kHz mono WAV (input format every STT runtime expects) |
| `build-essential` | ~300 MB | Compiling whisper.cpp / llama.cpp / qwen3-asr.cpp from source |
| `cmake`, `git`, `curl`, `wget`, `pkg-config` | ~150 MB | Build toolchain |
| `python3`, `python3-pip`, `python3-venv`, `python3-dev` | ~130 MB | Base interpreter + venv support + headers for some wheels |
| `libsndfile1` | ~2 MB | Runtime dep for `soundfile` Python wheel |

Mint 22.2 ships Python 3.12 as default `python3`. All pins below target py3.12.

### Python packages (inside each per-VM venv)

| Package | Approx disk | Purpose |
|---|---|---|
| `numpy` (latest) | ~50 MB | Transitive dep for everything else |
| `soundfile` | ~10 MB | WAV read/write from Python |
| `Pillow` | ~15 MB | Image downsampling (half-resolution gestalt for parents), quadrant cutting, **Chapter 12 offset-grid second cut** |
| `onnxruntime` (CPU wheel only, **not** `onnxruntime-gpu`) | ~250 MB | For Parakeet TDT *if ONNX export is available* (see risk in Section 3) |
| `torch` (CPU wheel: `--index-url https://download.pytorch.org/whl/cpu`) | ~200 MB | For Cohere Transcribe, Qwen3-ASR fallback path, any HF-hosted STT CPU inference |
| `transformers>=5.4.0` | ~30 MB | HF model loader (required by Cohere Transcribe per model card) |
| `huggingface_hub` | ~10 MB | Weight downloads, files-tree enumeration |
| `librosa` | ~40 MB | Required by Cohere Transcribe install list |
| `sentencepiece`, `protobuf` | ~20 MB | Tokenizer deps for Cohere Transcribe |
| `useful-moonshine` (git install per Moonshine model card) | ~50 MB | Moonshine native runtime |
| `pytest` | ~10 MB | Unit-testing the `slice_audio.py` / `slice_image.py` helpers |
| `requests` | ~5 MB | HTTP for drone-to-drone comms (may already be in V3 base) |

**Not installed (explicit omissions):**
- `onnxruntime-gpu` — no GPU
- `faiss`, `chromadb`, `sentence-transformers`, `langchain` — no vector mesh on the test bench
- `vllm`, `flash-attn` — GPU-first, irrelevant on CPU-only VMs
- `nemo_toolkit` — only if the Parakeet ONNX fallback path forces us to run NeMo CPU inference. Optional per-tier install, not in the base image. **If Parakeet ONNX works, NeMo does not need to be installed at all, saving ~2 GB per DwarfQueen/GiantQueen VM.**

### Compiled-from-source binaries (built once, copied to tiers that need them)

| Binary | Source | Tiers that need it |
|---|---|---|
| `whisper.cpp` (~20 MB compiled) | `github.com/ggerganov/whisper.cpp` | Every VM (universal bronze fallback) |
| `llama.cpp` (~80 MB compiled) | `github.com/ggerganov/llama.cpp` | Already in V3 for text reasoners; reuse |
| `qwen3-asr.cpp` (~30 MB compiled) | `github.com/predict-woo/qwen3-asr.cpp` | Only GiantQueen (bracket 5) and optionally bracket 3 DwarfQueens if they run the Qwen3-ASR silver |

### Custom helper scripts (written during the V4 rebuild, kept in `KillerBee` repo)

| Script | Purpose |
|---|---|
| `slice_audio.py` | Input: WAV + config (chunk duration, overlap, target gestalt sample rate). Output: (a) one downsampled full-duration gestalt file for the parent, (b) N full-quality chunk files for workers. Uses ffmpeg under the hood. |
| `slice_image.py` | Input: image + config (grid size, optional offset grid). Output: (a) one downsampled full-area gestalt for the parent, (b) N full-resolution tiles for workers, (c) optionally a second offset-grid tile set for the Chapter 12 boundary-recovery trick. Uses Pillow. |
| `run_stt.py` | Thin wrapper: load tier's STT model → transcribe one audio file → print to stdout → unload. Per-tier config selects the model and runtime. Load/unload discipline lives in the wrapper, not the orchestrator. |
| `run_reasoner.py` | Thin wrapper for the tier's text reasoner LLM. Same load/run/unload discipline. |
| `integrate_children.py` | Takes children's reports + this tier's own gestalt observation → calls `run_reasoner.py` → emits integrated paragraph for this tier. |

## Section 5 — Per-tier disk and RAM budgets (recomputed from verified numbers)

### Tooling disk (weights NOT included)

| Tier | Tooling stack | Approx disk |
|---|---|---|
| Worker (Moonshine Tiny/Base) | ffmpeg + Pillow + soundfile + numpy + useful-moonshine + whisper.cpp bin + venv | ~400 MB |
| DwarfQueen (Parakeet 0.6B or Qwen3-ASR 0.6B) | Worker stack + onnxruntime + torch CPU + transformers + qwen3-asr.cpp bin (optional) | ~1.3 GB |
| GiantQueen (Qwen3-ASR 1.7B) | DwarfQueen stack + qwen3-asr.cpp bin (required) | ~1.4 GB |
| RajaBee (Cohere Transcribe 2B) | GiantQueen stack + librosa + sentencepiece + protobuf (all already in the transformers install chain) | ~1.5 GB |

### STT weight footprints (per tier, on top of tooling)

| Tier | Gold model | Weight footprint (approx) |
|---|---|---|
| Worker (bracket 1) | Moonshine Tiny ONNX | ~30 MB |
| Worker (bracket 2 variant) | Moonshine Base ONNX | ~80 MB |
| DwarfQueen (bracket 3) | Parakeet 0.6B v3 | ~200 MB INT8 / ~600 MB FP32 |
| DwarfQueen (bracket 4) | Parakeet 1.1B | ~1.1 GB FP32 (no INT8 path confirmed) |
| GiantQueen (bracket 5) | Qwen3-ASR 1.7B | ~1 GB INT4 / ~4 GB BF16 |
| RajaBee (bracket 6) | Cohere Transcribe 2B | ~2 GB Q4 / ~4 GB FP16 |

### RAM (sequential load/unload means peak = single largest resident model)

| Tier | Peak STT RAM | Context |
|---|---|---|
| Worker | ~200 MB | Moonshine under PyTorch CPU |
| DwarfQueen | ~300 MB – 1.5 GB | INT8 Parakeet on ORT CPU vs FP32 NeMo CPU (resolve at build time) |
| GiantQueen | ~1.5 – 2 GB | Qwen3-ASR 1.7B at INT4 |
| RajaBee | ~2 – 4 GB | Cohere Transcribe Q4 → FP16 depending on quant choice |

**Worst-case total tooling + weight disk across the v3 hive (8 VMs):** ~15 – 20 GB. Nir has 1.5 TB free on the Desktop drive; no pressure.

**Worst-case total RAM at any single moment on the Desktop host** (sum of all 8 VMs' peak STT RAM, which is already under sequential-load discipline at each VM individually): ~12 – 16 GB ballpark. The 13900KF host has more than enough.

## Section 6 — Provisioning script

A runnable, idempotent, tier-aware `PHASE3_PROVISION_VM.sh` is pushed alongside this file. Usage:

```bash
sudo bash PHASE3_PROVISION_VM.sh <tier>
# tier ∈ { worker | dwarfqueen | giantqueen | rajabee }
```

Script structure (full source in the standalone file):
1. apt-install system packages (ffmpeg, build tools, Python, libsndfile1).
2. Create `/opt/killerbee/venv` (idempotent — skips if already exists).
3. Install tier-appropriate pip requirements into the venv.
4. Clone + build the C++ binaries needed for the tier under `/opt/killerbee/src/`.
5. Write a tier marker file at `/opt/killerbee/.tier` so re-runs can detect what was previously provisioned.
6. Print a summary at the end (installed versions of every pinned package).

**Test status on Desktop:** syntax-checked with `bash -n`. **No integration test against a real VM yet** because V3 currently has 0 production VMs (see `project_phase3_v3_resume` memory). The first real integration test happens during the V4 rebuild, against VM 1 only, as the v2 brief specifies. The script is written defensively (every step guarded by an existence check) so a partial failure on the first VM does not require a clean re-provision.

## Section 7 — Open questions for Nir

1. **Parakeet ONNX export path (bracket 2 silver, bracket 3 gold, bracket 4 gold).** The HF model cards for Parakeet TDT 0.6B v3 and 1.1B do NOT publish an ONNX artifact. The v2 brief assumes ONNX Runtime CPU. At provisioning time we will try to export via NeMo's export tool. **Question for Nir:** if ONNX export fails or produces degraded accuracy, do you want us to (a) run Parakeet under NeMo CPU (full FP32, ~2 GB RAM per VM, unknown latency), (b) fall back to the silver in each affected bracket (Moonshine / Whisper-turbo / whisper.cpp), or (c) skip Parakeet entirely and re-promote Whisper-turbo to gold at brackets 2-4?

2. **`qwen3-asr.cpp` project maturity (brackets 1/3/5 silvers and bracket 5 gold).** The `predict-woo/qwen3-asr.cpp` repo has 77 stars, 7 commits, and Metal-first documentation. It compiles a GGML CPU backend but has no published stability guarantees. **Question for Nir:** acceptable to build and benchmark it on VM 1 during the rebuild? If the CPU backend is unusably slow or unstable, do you want us to fall back to HF `transformers` CPU inference for Qwen3-ASR (much simpler, slower) or replace the Qwen3-ASR brackets entirely with Whisper-turbo?

3. **Cohere Transcribe quantization choice (bracket 6 gold).** 24 quant variants exist. HF card does not enumerate them. **Default plan:** pick a Q4_K_M GGUF if Cohere publishes one, else the smallest FP16 safetensors. **Question for Nir:** any preference, or delegate the pick to build-time benchmarking on VM 8 (RajaBee)?

4. **Moonshine PyPI package name.** The model card shows `useful-moonshine` (git install); the ecosystem also mentions `moonshine-onnx`. **Question for Nir:** OK to try `useful-moonshine` first and only add `moonshine-onnx` if we need the ONNX path separately?

5. **`nemo_toolkit` on DwarfQueen/GiantQueen VMs.** It is a ~2 GB install and is ONLY needed if the Parakeet ONNX path fails. **Default plan:** do NOT install NeMo in the base image; install it lazily on tiers that need it after the ONNX export verdict. **Question for Nir:** accept this lazy path, or pre-install on every DwarfQueen/GiantQueen for determinism?

6. **Transformers version pin.** Cohere Transcribe requires `transformers>=5.4.0`. As of today, transformers 5.x is a recent major. **Question for Nir:** pin to `transformers==5.4.0` exactly, or use `transformers>=5.4.0,<6` to allow patch upgrades?

7. **Whether to keep `whisper.cpp` on every VM unconditionally** as the universal bronze fallback, or skip it on workers to save ~20 MB compiled binary plus ~140 MB source tree. **Default plan:** install on every VM — 160 MB is trivial and the fallback has no price if never invoked. **Question for Nir:** confirm or overrule.

---

*End of main file. Verification audit trail is in `PHASE3_STT_VERIFICATION_LOG_2026-04-15_v2.md`. Runnable provisioning script is in `PHASE3_PROVISION_VM.sh`. V3/V4 rebuild remains ON HOLD pending your review. When you approve, the next step is to merge this STT + tooling plan into the existing V3 plan, call the merged plan V4, and execute a single rebuild (no baseline-then-expand).*
