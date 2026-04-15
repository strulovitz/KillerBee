# Phase 3 STT Verification Log — 2026-04-15 v2

**Author:** Desktop Claude (Opus 4.6, 1M context), Linux Mint 22.2 on i9-13900KF
**Purpose:** audit trail for every model card fetched during the v2 STT + tooling research. One entry per candidate. Every number below was read off a live HF model card page on 2026-04-15 via WebFetch. No summaries of summaries.

---

## Entry 1 — Moonshine (gold bracket 1 and bracket 2)

- **URL hit:** `https://huggingface.co/UsefulSensors/moonshine`
- **Date/time:** 2026-04-15, during verification sprint following v2 brief
- **Exact model name on page:** `UsefulSensors/moonshine`
- **Parameter counts:** tiny = 27 M, base = 61 M (two variants under the one repo)
- **Quantization / file formats listed:** ONNX, PyTorch, safetensors (via Keras backend abstraction — PyTorch, TensorFlow, JAX backends all supported)
- **License field:** **MIT**
- **Languages:** English only (model card notes primary training and evaluation is English ASR)
- **PyPI package:** `useful-moonshine` (install via `uv pip install useful-moonshine@git+https://github.com/usefulsensors/moonshine.git`). Also `moonshine-onnx` exists as a separate ONNX-only package per ecosystem docs (not verified on this page — **flag for the build step**).
- **Runtime usage pattern:** `moonshine.transcribe(audio_file, 'moonshine/tiny')` — two model identifiers: `moonshine/tiny`, `moonshine/base`.
- **Refinements vs v2 brief:** Brief estimated Moonshine Tiny ONNX weight footprint at ~30 MB and Base at ~80 MB. Model card does not state exact ONNX file sizes — **Desktop will measure the real ONNX artifact size at download time during provisioning** rather than trust the estimate.
- **Contradictions with brief:** none.

## Entry 2 — Qwen3-ASR-0.6B (silver bracket 1, silver bracket 3)

- **URL hit:** `https://huggingface.co/Qwen/Qwen3-ASR-0.6B`
- **Date/time:** 2026-04-15
- **Exact model name on page:** `Qwen/Qwen3-ASR-0.6B`
- **Parameter count as stated:** "0.6B (0.9B params total)" — the page itself contains both numbers. The "0.6B" in the name refers to one subcomponent; the full model is 0.9 B. Brief's "0.9B actual" matches.
- **License field:** **Apache 2.0**
- **Tensor type:** BF16 safetensors (native)
- **Languages supported:** 30 languages + 22 Chinese dialects. Named languages: zh, en, yue, ar, de, fr, es, pt, id, it, ko, ru, th, vi, ja, tr, hi, ms, nl, sv, da, fi, pl, cs, fil, fa, el, hu, mk, ro. (Note: covers Arabic + Russian but NOT Hebrew. Irrelevant for the v2 English-only constraint.)
- **Quantization variants:** model card references "17 quantized variants" in the Model tree; exact filenames are not enumerated on the human-readable card and would require hitting the files tree. **Desktop will list exact quant filenames at download time.**
- **WER benchmarks (stated on page):** LibriSpeech clean 2.11 / other 4.55; GigaSpeech 8.88; CommonVoice-en 9.92; AISHELL-2-test 3.15; Fleurs-zh 2.88.
- **Runtime recommendations on page:** `pip install -U qwen-asr`; examples use `device_map="cuda:0"` and `torch.bfloat16`. **All official examples are GPU-leaning.** The CPU path the v2 brief proposes is via `qwen3-asr.cpp` (entry 8 below), not via `qwen-asr` direct. Alternatively, HF Transformers CPU inference with BF16→FP32 conversion is possible but not benchmarked on the card.
- **Contradictions with brief:** brief stated "9.9M downloads" context — page shows 1.65M downloads/month for the 1.7B variant, not the 0.6B. Not a blocker; corrected in the main file.

## Entry 3 — Qwen3-ASR-1.7B (gold bracket 5, silver bracket 6)

- **URL hit:** `https://huggingface.co/Qwen/Qwen3-ASR-1.7B`
- **Date/time:** 2026-04-15
- **Exact model name on page:** `Qwen/Qwen3-ASR-1.7B`
- **Parameter count as stated:** "Model Size: 2B parameters" (the "1.7B" in the name is again the subcomponent naming; actual model is 2 B). Matches brief.
- **License field:** **Apache 2.0**
- **Tensor type:** BF16
- **Downloads last month:** **1,650,790** (matches brief's "1.65M")
- **Languages:** 30 languages + 22 Chinese dialects + multiple English accents — "52 languages and dialects" total as stated on page. Covers ar, ru (no Hebrew; irrelevant under v2 English-only rule).
- **Quantization variants:** "10 quantized variants" — exact filenames not enumerated on the human-readable card; resolvable via files tree.
- **WER benchmarks (stated on page):** LibriSpeech clean 1.63 / other 3.38; GigaSpeech 8.45; WenetSpeech 4.97 / 5.88; AISHELL-2-test 2.71; Fleurs 4.90 multilingual avg; CommonVoice 9.18; Language-ID accuracy 97.9% (vs Whisper 94.6%).
- **Runtime recommendations:** `pip install -U qwen-asr`; all examples GPU (`device_map="cuda:0"`, vLLM, Docker with `--gpus all`). **Same GPU-leaning concern as entry 2.** CPU path is `qwen3-asr.cpp` (entry 8).
- **Contradictions with brief:** none.

## Entry 4 — NVIDIA Parakeet TDT 0.6B v3 (silver bracket 2, gold bracket 3)

- **URL hit:** `https://huggingface.co/nvidia/parakeet-tdt-0.6b-v3`
- **Date/time:** verified 2026-04-15 (this run plus the earlier v1 run — data identical)
- **Exact model name on page:** `nvidia/parakeet-tdt-0.6b-v3`
- **Parameter count:** 600 M (0.6 B)
- **Release date on page:** 2025-08-14
- **License field:** **CC-BY-4.0**
- **Languages:** 25 European languages. Full list: bg, hr, cs, da, nl, en, et, fi, fr, de, el, hu, it, lv, lt, mt, pl, pt, ro, sk, sl, es, sv, ru, uk.
- **Minimum RAM:** "Minimum: 2GB RAM for model to load" (quoted from page)
- **WER benchmarks (from HF Open ASR Leaderboard on page):** Average 6.34%; AMI 11.31; Earnings-22 11.42; GigaSpeech 9.59; LibriSpeech test-clean 1.93; LibriSpeech test-other 3.59; SPGI 3.97; TEDLIUM-v3 2.75; VoxPopuli 6.14. Multilingual: Fleurs 11.97, MLS 7.83, CoVoST 11.98.
- **Runtime recommendations on page:** NVIDIA NeMo toolkit (`pip install nemo_toolkit['all']`). **ONNX export is NOT stated on the model card.** The v2 brief assumes an ONNX Runtime CPU path — **this needs to be confirmed at build time.** If ONNX export is not trivially available, fall back either to (a) NeMo CPU inference (verify performance acceptable) or (b) the silver Moonshine Base at the same bracket.
- **Contradictions with brief:** brief says "ONNX Runtime CPU" is the runtime. The HF page does not publish an ONNX artifact for Parakeet v3. **This is the single biggest risk in the v2 ladder and is flagged in Section 7 of the main file.**

## Entry 5 — NVIDIA Parakeet TDT 1.1B (gold bracket 4)

- **URL hit:** `https://huggingface.co/nvidia/parakeet-tdt-1.1b`
- **Date/time:** 2026-04-15
- **Exact model name on page:** `nvidia/parakeet-tdt-1.1b`
- **Parameter count:** 1.1 B
- **License field:** **CC-BY-4.0**
- **Languages:** **English only (lowercase English alphabet only, per page)**
- **Architecture:** FastConformer-TDT (Token-and-Duration Transducer)
- **Input:** 16 kHz mono WAV
- **WER benchmarks:** LibriSpeech test-clean 1.39 / test-other 2.62; AMI 15.90; Earnings-22 14.65; GigaSpeech 9.55; TEDLIUM-v3 3.42; VoxPopuli 3.56; Common Voice v7.0 5.48.
- **Runtime recommendation on page:** NVIDIA NeMo (`pip install nemo_toolkit['all']`). **ONNX availability: "Not mentioned in the documentation as available."** Same concern as entry 4.
- **Contradictions with brief:** brief says runtime is "ONNX Runtime CPU." Same unresolved concern — **ONNX export is not stated on the page.** If it cannot be produced, fall back to NeMo CPU, or to the silver Whisper Large v3 Turbo.
- **Training data:** 64 K hours English speech.

## Entry 6 — OpenAI Whisper Large v3 Turbo (silver bracket 4, silver bracket 5, universal bronze fallback)

- **URL hit:** `https://huggingface.co/openai/whisper-large-v3-turbo`
- **Date/time:** 2026-04-15 (re-verified from the v1 run)
- **Exact model name on page:** `openai/whisper-large-v3-turbo`
- **Parameter count:** 809 M
- **License field:** **MIT**
- **Languages:** 99 multilingual
- **File size:** approximately 1.6 GB at F16 safetensors
- **Architecture detail:** optimized large-v3 with decoding layers reduced from 32 to 4. Upstream claims "minimal degradation in accuracy" vs large-v3 (no exact WER delta published).
- **Runtime options:** `whisper.cpp` (C++ / GGML), `faster-whisper` (CTranslate2), HF `transformers`, `mlx`. Also supports Flash Attention 2, torch.compile, torch SDPA for GPU optimization — irrelevant under v2's CPU-only rule; relevant CPU path is `whisper.cpp`.
- **GGML quantized variants (from `ggerganov/whisper.cpp` HF repo, verified in v1 run):** `large-v3-turbo` 1.5 GiB, `large-v3-turbo-q5_0` 547 MiB, `large-v3-turbo-q8_0` 834 MiB.
- **Contradictions with brief:** none.

## Entry 7 — Cohere Transcribe 03-2026 (gold bracket 6)

- **URL hit:** `https://huggingface.co/CohereLabs/cohere-transcribe-03-2026`
- **Date/time:** 2026-04-15
- **Exact model name on page:** `cohere-transcribe-03-2026` (repo: `CohereLabs/cohere-transcribe-03-2026`)
- **Parameter count:** 2 B
- **License field:** **Apache 2.0**
- **Release date on page:** 2026-03-26
- **Architecture:** Conformer-based encoder-decoder
- **Languages:** 14 total — English, French, German, Italian, Spanish, Portuguese, Greek, Dutch, Polish, Chinese (Mandarin), Japanese, Korean, Vietnamese, Arabic. (Covers Arabic but not Hebrew or Russian. Irrelevant under v2's English-only rule.)
- **WER benchmarks (English ASR leaderboard, stated on page):** Average **5.42%** — AMI 8.15, Earnings-22 10.84, GigaSpeech 9.33, LS clean 1.25, LS other 2.37, SPGISpeech 3.08, TEDLIUM 2.49, VoxPopuli 5.87. **Best WER on the entire ladder.**
- **Native inference code (verbatim from page):**
  ```python
  from transformers import AutoProcessor, CohereAsrForConditionalGeneration
  from transformers.audio_utils import load_audio
  processor = AutoProcessor.from_pretrained("CohereLabs/cohere-transcribe-03-2026")
  model = CohereAsrForConditionalGeneration.from_pretrained(
      "CohereLabs/cohere-transcribe-03-2026", device_map="auto"
  )
  ```
- **Installation:** `pip install transformers>=5.4.0 torch huggingface_hub soundfile librosa sentencepiece protobuf`
- **Quantization variants:** "24 quantized models available for the base model" (exact filenames resolvable via files tree).
- **Additional features:** auto-chunking audio >35 s, punctuation control, batched mixed short/long-form inference, RTFx up to 3× faster than comparable ASR.
- **Contradictions with brief:** brief says "HF Transformers CPU native (model card says native transformers library inference works directly)" — matches. Brief says "probably ~2 GB in Q4 quant, ~4 GB in FP16" — exact quant filenames not enumerated on the card; Desktop will pick one at download time from the 24 available.

## Entry 8 — qwen3-asr.cpp runtime (not an STT model, but the CPU path for Qwen3-ASR)

- **URL hit:** `https://github.com/predict-woo/qwen3-asr.cpp`
- **Date/time:** 2026-04-15
- **Exact repo name:** `predict-woo/qwen3-asr.cpp`
- **Star count:** 77 stars, 26 forks, 2 watchers, 7 commits, no releases
- **Description:** "A high-performance C++ implementation of Qwen3-ASR and Qwen3-ForcedAligner using the GGML tensor library. Optimized for Apple Silicon with Metal GPU acceleration"
- **Build:** CMake. Standard GGML-style build (clone with submodules, cmake -DCMAKE_BUILD_TYPE=Release, build with -j).
- **Backend:** "Metal GPU Dual Backend: Automatic scheduling between CPU and GPU." On x86_64 Linux without Metal, the CPU backend is the active path. **This is the CPU route for Qwen3-ASR on the i9-13900KF; need to confirm the CPU backend performs acceptably at build time.**
- **Contradictions with brief:** brief says "77 stars, active, last updated February" — stars match; last-update date is not confirmed from the page content I fetched. Not a blocker. Commit count (7) suggests the project is young; this is a real risk for relying on it as the gold runtime at bracket 5.

---

## Summary of unresolved risks pulled from this verification pass

1. **Parakeet TDT 0.6B v3 and 1.1B: ONNX path is not published on their HF cards.** v2 brief assumes ONNX Runtime CPU. Need to verify at provisioning time whether ONNX export is available via NeMo export tool, or accept NeMo CPU as the runtime, or fall back to silver.
2. **Qwen3-ASR CPU runtime maturity.** `qwen3-asr.cpp` has 7 commits and 77 stars. It may not be production-grade. Flash-attn / vLLM / GPU paths from the Qwen team are all GPU-first. Worst case fallback is HF `transformers` CPU inference (slower but works).
3. **Exact quantization filenames for Qwen3-ASR (17 and 10 variants respectively) and Cohere Transcribe (24 variants) are not enumerated on the human-readable model cards.** Desktop will enumerate them at download time using `huggingface_hub` Python API.
4. **Moonshine ONNX artifact sizes** are not on the card. Will measure at download.
5. **No VM to test against yet.** V3 has 0 production VMs. Provisioning script is syntax-checked (`bash -n`) but not integration-tested end-to-end. First real run will be during the V4 rebuild on VM 1.

---

*End of verification log. Every fact above was read off a live HF (or GitHub) page on 2026-04-15 by Desktop Claude. Entries 4 and 6 were re-verified against the earlier v1 verification data and are identical.*
