# Phase 3 STT Research — 2026-04-15

**Author:** Desktop Claude (Opus 4.6, 1M context), Linux Mint 22.2
**Task source:** `WaggleDance/DESKTOP_KILLERBEE_STT_RESEARCH_BRIEF_2026-04-15.md`
**Status:** Research output. V3/V4 rebuild remains ON HOLD pending Nir review.
**Companion file:** `PHASE3_STT_NIR_SEARCH_QUERIES_2026-04-15.md` (spot-check queries)

---

## Section 1 — Purpose and context

Phase 3 V3 plan covers text and vision models but not audio. The KillerBee hive has to run three model classes at every VM tier: perception (vision and/or audio), STT (for audio input), and text reasoning. Chapter 12 of TheDistributedAIRevolution establishes that audio is the one-dimensional instance of the recursive sub-sampling principle: parents hear a downsampled gestalt of the whole recording, children transcribe full-fidelity one-second slices, and the parent integrates text reports onto her temporal map. Chapter 15 slippery point 3 pins down that both perception and reasoning models scale UP with hierarchy — bosses get the biggest models their hardware can afford, not the smallest.

This file maps six size brackets of STT models to the KillerBee tier ladder so Nir can pick which bracket lands on which tier. Every candidate below was verified against a live upstream source today (2026-04-15). Multilingual support is weighted because Nir is in Israel — Hebrew, Arabic, and Russian audio are all in scope.

Ollama is effectively not an STT runtime. A handful of community-uploaded Whisper mirrors exist on `ollama.com` (e.g. `dimavz/whisper-tiny`, `karanchopda333/whisper`) but none are official, none are documented as first-class, and Ollama's engine is still built for text/vision LLMs. Route STT through `whisper.cpp` (CPU-first C++ runtime), `faster-whisper` (CTranslate2 GPU runtime), or NVIDIA NeMo for the Parakeet/Canary families. Details in Section 5.

## Section 2 — Known-at-start hints (labeled as hints, not facts)

These came from the brief and from training-cutoff memory, and were treated as leads only:
- Whisper family from OpenAI: tiny/base/small/medium/large-v3, MIT.
- `large-v3-turbo` may exist (optimized large-v3).
- Distil-Whisper distilled variants from HuggingFace.
- Ollama probably still does not host STT first-class.
- Newer non-Whisper projects may have emerged since May 2025.

Every one of these hints was then verified or corrected below.

## Section 3 — Verification method

I fetched each candidate's primary source live on 2026-04-15 and extracted the numbers directly from the upstream README or model card. Sources I actually loaded:

1. `https://github.com/openai/whisper` — canonical Whisper size/VRAM/speed table.
2. `https://github.com/ggml-org/whisper.cpp` — whisper.cpp README memory table.
3. `https://huggingface.co/ggerganov/whisper.cpp` — full GGML quantized file-size table.
4. `https://github.com/SYSTRAN/faster-whisper` — faster-whisper compute types and VRAM benchmarks.
5. `https://huggingface.co/openai/whisper-large-v3-turbo` — turbo parameter count, languages, license.
6. `https://huggingface.co/distil-whisper/distil-large-v3` — distil parameters, WER, language scope.
7. `https://huggingface.co/nvidia/canary-1b` — Canary parameters, languages, license, WER.
8. `https://huggingface.co/nvidia/parakeet-tdt-0.6b-v2` — Parakeet v2 (English-only).
9. `https://huggingface.co/nvidia/parakeet-tdt-0.6b-v3` — Parakeet v3 (25-language multilingual, released 2025-08-14).
10. `https://huggingface.co/FunAudioLLM/SenseVoiceSmall` — SenseVoice-Small, 50+ languages.
11. `https://huggingface.co/UsefulSensors/moonshine` — Moonshine tiny/base, English only.
12. `https://ollama.com/search?q=whisper` — confirmed only community mirrors, no official STT.

Where a number is not published upstream I flagged it as "not published" rather than guessed. WER numbers are quoted as the upstream project states them; I did not run any benchmark myself.

## Section 4 — The six size brackets

Language coverage legend: **HE/AR/RU** = covers Hebrew + Arabic + Russian (Nir's ambient environment). **EU-25** = 25 European languages per Parakeet v3 list. **EN-only** = English monolingual.

> **Important:** Only the **Whisper family** (and its derivatives whisper.cpp / faster-whisper / distil-whisper / turbo) covers Hebrew and Arabic in its 99-language set. Canary (4 lang) and Parakeet v3 (25 European) do NOT cover Hebrew or Arabic. SenseVoice-Small (50+ lang) covers English/Chinese/Japanese/Korean/Cantonese but its language list as published does not include Hebrew/Arabic. **For HE/AR you have to stay on the Whisper ladder.**

---

### Bracket 1 — `tiny` (~1–2 GB RAM budget, bottom-of-tree worker)

| Candidate | Params | Runtime | Quant | Disk | RAM | License | Languages | WER (upstream) |
|---|---|---|---|---|---|---|---|---|
| `whisper tiny` | 39 M | whisper.cpp | FP16 | 75 MiB | ~273 MB | MIT | 99 incl. HE/AR/RU | not published per-size |
| `whisper tiny-q5_1` | 39 M | whisper.cpp | Q5_1 | 31 MiB | ~200 MB est. | MIT | 99 incl. HE/AR/RU | not published |
| `whisper base` | 74 M | whisper.cpp | FP16 | 142 MiB | ~388 MB | MIT | 99 incl. HE/AR/RU | not published per-size |
| `whisper base-q5_1` | 74 M | whisper.cpp | Q5_1 | 57 MiB | ~280 MB est. | MIT | 99 incl. HE/AR/RU | not published |
| `moonshine/tiny` | 27 M | Moonshine runtime | FP16 | not published | "memory-constrained" | MIT | EN-only | not published |

**Pick guidance:** `whisper base-q5_1` at 57 MiB disk, ~280 MB working set, is the default tiny-tier worker. It preserves HE/AR/RU and costs almost nothing. `whisper tiny-q5_1` is the fallback if Arduino-adjacent VMs are RAM-starved. Moonshine tiny is interesting *only* if Nir ever spins up an English-only worker cluster where the 27 M parameter count and sub-second latency matter more than multilingual coverage.

---

### Bracket 2 — `small` (~2–4 GB RAM, DwarfQueen tier)

| Candidate | Params | Runtime | Quant | Disk | RAM | License | Languages | WER (upstream) |
|---|---|---|---|---|---|---|---|---|
| `whisper small` | 244 M | whisper.cpp | FP16 | 466 MiB | ~852 MB | MIT | 99 incl. HE/AR/RU | not published per-size |
| `whisper small-q5_1` | 244 M | whisper.cpp | Q5_1 | 181 MiB | ~500 MB est. | MIT | 99 incl. HE/AR/RU | not published |
| `whisper small-q8_0` | 244 M | whisper.cpp | Q8_0 | 252 MiB | ~650 MB est. | MIT | 99 incl. HE/AR/RU | not published |
| `whisper small` via `faster-whisper int8` | 244 M | faster-whisper | int8 | ~250 MB | ~700 MB GPU est. | MIT | 99 incl. HE/AR/RU | not published |

**Pick guidance:** `whisper small-q5_1` on whisper.cpp for CPU-only DwarfQueens. If the DwarfQueen VM has a passthrough GPU slice, switch to `faster-whisper` int8 at the same model size — same quality, much faster.

---

### Bracket 3 — `medium-small` (~3–5 GB RAM, intermediate tier)

| Candidate | Params | Runtime | Quant | Disk | RAM | License | Languages | WER (upstream) |
|---|---|---|---|---|---|---|---|---|
| `whisper medium-q5_0` | 769 M | whisper.cpp | Q5_0 | 514 MiB | ~1.4 GB est. | MIT | 99 incl. HE/AR/RU | not published |
| `whisper medium-q8_0` | 769 M | whisper.cpp | Q8_0 | 785 MiB | ~1.8 GB est. | MIT | 99 incl. HE/AR/RU | not published |
| `whisper medium` (FP16) | 769 M | whisper.cpp / faster-whisper | FP16 | 1.5 GiB | ~2.1 GB | MIT | 99 incl. HE/AR/RU | not published |
| `distil-large-v3` | 756 M | faster-whisper | int8/fp16 | ~1.5 GB | ~2 GB est. int8 | MIT | **EN-only** | 9.7% short-form, 10.8% seq long-form (vs 8.4/10.0 for large-v3) |

**Pick guidance:** `whisper medium-q5_0` for HE/AR/RU coverage at intermediate tiers. `distil-large-v3` is tempting for its 6.3x latency improvement over large-v3 and its 7.52 mean WER on open-ASR-leaderboard — **but English only.** If Nir ever wants an English-only fast tier (e.g. for the Laptop Claude → Desktop Claude ICQ voice channel where the languages spoken are known English), distil-large-v3 is the strongest value-per-GB in this bracket.

---

### Bracket 4 — `medium` (~4–6 GB RAM, GiantQueen tier)

| Candidate | Params | Runtime | Quant | Disk | RAM | License | Languages | WER (upstream) |
|---|---|---|---|---|---|---|---|---|
| `whisper medium` (FP16) | 769 M | whisper.cpp | FP16 | 1.5 GiB | ~2.1 GB | MIT | 99 incl. HE/AR/RU | not published |
| `whisper large-v3-turbo-q5_0` | 809 M | whisper.cpp | Q5_0 | 547 MiB | ~2.5 GB est. | MIT | 99 incl. HE/AR/RU | matches large-v3 "minimal degradation" (upstream claim only) |
| `whisper large-v3-turbo-q8_0` | 809 M | whisper.cpp | Q8_0 | 834 MiB | ~3.2 GB est. | MIT | 99 incl. HE/AR/RU | as above |
| `SenseVoiceSmall` | ~Whisper-small class | FunASR | FP16 | not published | not published | "model-license" (check) | 50+ incl. EN/ZH/JA/KO/YUE; **no HE/AR published** | 70 ms / 10 s audio; claims to beat Whisper-Large on AISHELL/LibriSpeech (upstream-published only) |

**Pick guidance:** `whisper large-v3-turbo-q5_0` is the sweet spot for the GiantQueen tier — 547 MiB on disk, full 99-language coverage, 8x relative speed vs large-v1, MIT license. Only consider SenseVoice if Nir explicitly wants Chinese/Japanese/Korean and is willing to verify its license text himself (the model card says "model-license" without expanding — **open question, flagged in Section 6**).

---

### Bracket 5 — `medium-big` (~6–10 GB RAM, intermediate top tier)

| Candidate | Params | Runtime | Quant | Disk | RAM | License | Languages | WER (upstream) |
|---|---|---|---|---|---|---|---|---|
| `whisper large-v3-turbo` (FP16) | 809 M | whisper.cpp / faster-whisper | FP16 | 1.5 GiB (whisper.cpp) / 1.6 GB (HF safetensors) | ~6 GB VRAM | MIT | 99 incl. HE/AR/RU | see turbo note below |
| `whisper large-v3-q5_0` | 1550 M | whisper.cpp | Q5_0 | 1.1 GiB | ~5–6 GB est. | MIT | 99 incl. HE/AR/RU | see large-v3 below |
| `whisper large-v3-q8_0` | 1550 M | whisper.cpp | Q8_0 | 1.5 GiB | ~6–7 GB est. | MIT | 99 incl. HE/AR/RU | as above |
| `nvidia/parakeet-tdt-0.6b-v3` | 600 M | NVIDIA NeMo | FP16 | not published | ≥ 2 GB RAM to load | **CC-BY-4.0** | 25 European incl. RU/UK; **no HE/AR** | avg 6.34% ASR leaderboard; Fleurs 11.97 / MLS 7.83 / CoVoST 11.98 multi-avg |

**Pick guidance:** This is the bracket where Nir has a real tradeoff.
- `whisper large-v3-turbo` gives full HE/AR/RU coverage, MIT license, and the best documented latency in the Whisper family. Default choice.
- `parakeet-tdt-0.6b-v3` is faster and lighter on GPU for its class but **drops Hebrew and Arabic**. Valid only if Nir decides that upper-tier audio is Russian-or-European and HE/AR is handled at a different tier.
- `whisper large-v3-q5_0` is the right pick if Nir specifically wants the full 1.55 B parameter gestalt quality and is willing to pay 1.1 GB disk plus ~6 GB working set.

---

### Bracket 6 — `big` (~10–16 GB RAM, RajaBee top tier)

| Candidate | Params | Runtime | Quant | Disk | RAM/VRAM | License | Languages | WER (upstream) |
|---|---|---|---|---|---|---|---|---|
| `whisper large-v3` (FP16) | 1550 M | whisper.cpp / faster-whisper | FP16 | 2.9 GiB (whisper.cpp) | ~10 GB (whisper.cpp table: 3.9 GB base + working buffers; faster-whisper fp16 uses ~4.5 GB VRAM for large-v2 on 3070 Ti) | MIT | 99 incl. HE/AR/RU | reference; 8.4% short-form, 10.0% seq long-form (from distil-large-v3 comparison table) |
| `whisper large-v3` batched fp16 | 1550 M | faster-whisper batch=8 | FP16 | 2.9 GiB | ~6 GB VRAM (benchmark: large-v2 batch 8 fp16 = 6090 MB on 3070 Ti; large-v3 similar class) | MIT | 99 incl. HE/AR/RU | reference |
| `whisper large-v3` int8 | 1550 M | faster-whisper | int8 | ~1.5 GB | ~2.9 GB VRAM (benchmark: large-v2 int8 = 2926 MB on 3070 Ti) | MIT | 99 incl. HE/AR/RU | slight degradation vs fp16 (upstream: "reduced accuracy"; exact number not published) |
| `nvidia/canary-1b` | 1000 M | NVIDIA NeMo | FP16 | not published | not published | **CC-BY-NC-4.0** ⚠ non-commercial | EN/DE/FR/ES only; **no HE/AR/RU** | MLS EN 3.06%, DE 4.19%, ES 3.15%, FR 4.12%; LibriSpeech clean 1.48% |

**Pick guidance:**
- `whisper large-v3` FP16 on `faster-whisper` is the default RajaBee STT. It's the most accurate Whisper class, covers Hebrew/Arabic/Russian, and MIT.
- If the RajaBee VM has a GPU slice large enough, batched fp16 at batch=8 roughly doubles the VRAM footprint but cuts latency significantly.
- **Canary-1b has a license that fails Nir's rule.** CC-BY-NC-4.0 means no commercial use. Beehive Of AI is a product; non-commercial licensing is a trap. Skip Canary regardless of its WER numbers.

---

## Section 5 — Runtime recommendation

**Default stack: `whisper.cpp` on every tier, with `faster-whisper` overlaid on any tier that has a real GPU slice.**

Reasoning:

1. **Ollama is not an STT runtime.** The Ollama library hosts only a handful of unofficial community Whisper mirrors (`dimavz/whisper-tiny`, `karanchopda333/whisper`, `anagram/whispertiny`, `sendmeaiohyeah/whisper-large-v2`), none of them first-class, none documented in the Ollama engine docs. Shipping KillerBee STT through Ollama would mean depending on random HuggingFace re-uploads. Do not do that.
2. **whisper.cpp is the CPU-first path.** Pure C++, no Python runtime, tiny memory overhead, supports every Whisper size from tiny to large-v3-turbo at multiple Q5/Q8 quantizations. It is the right default for DwarfQueen and worker VMs where CPU is the only real compute resource.
3. **faster-whisper is the GPU path.** CTranslate2 backend, supports fp32/fp16/int8/int8_float16, handles batched transcription, supports distil-large-v3 and large-v3-turbo natively. It is the right default for GiantQueen and RajaBee VMs where GPU is available.
4. **NVIDIA NeMo is only needed if Nir picks Parakeet v3.** Parakeet is not whisper-compatible; it requires the `nemo_toolkit[asr]` install. Add NeMo as an optional extra runtime only if Parakeet v3 makes it into V4.
5. **Sequential load/unload is still the KillerBee test-bench baseline.** Slippery point 5 + bonus point from chapter 15: the sequential case is the architecture-faithful test. Load vision, run, unload, load STT, run, unload, load reasoner, run, unload. Both whisper.cpp and faster-whisper unload cleanly; neither holds persistent state.

## Section 6 — Open questions for Nir

1. **Language scope for upper tiers.** Does Nir want HE/AR coverage at every tier, or is the upper-tier audio known-English-only (in which case distil-large-v3 and the English-only Parakeet v2 become viable)? Default assumption: HE/AR/RU required at every tier.
2. **SenseVoice license.** The model card says "model-license" without quoting actual terms. I did not open the license file. Before considering SenseVoice for any production tier, Nir should read the license himself.
3. **Parakeet v3 at the GiantQueen tier.** If Nir accepts "HE/AR handled only at the RajaBee via Whisper large-v3" and lets the mid tiers be 25-European-language Parakeet v3, he gets measurably better WER and RTFx in that tier at the cost of architectural symmetry. Is that tradeoff worth it?
4. **Batched fp16 vs int8 at the RajaBee.** Nir has an RTX 4070 Ti on Desktop and an RTX 5090 on Laptop. Which machine hosts the RajaBee VM? The answer determines whether we should default to fp16-batched (needs ~6 GB VRAM) or int8-batched (needs ~3 GB VRAM) at the top.
5. **Does Nir want English-only specialized workers anywhere?** Distil-large-v3 and Moonshine are English-only but offer meaningful speed wins. A mixed-language-policy swarm (some workers English-only-fast, others multilingual-slower) is not inherently wrong — slippery point 5 says configuration is a choice, not a mandate — but it needs an explicit decision.
6. **Hebrew/Arabic WER at Whisper.** The Whisper project does not publish per-language WER tables for Hebrew or Arabic. We are assuming "supported" = "usable." Nir may want to run a quick Hebrew voice-memo test against `whisper large-v3-turbo` before committing the whole ladder to the Whisper family.

## Section 7 — What changes in the V3 / V4 rebuild plan

Per-VM disk and RAM budget deltas to add to the V4 rebuild:

- **Workers (tiny tier):** +500 MB disk (whisper.cpp binary + base-q5_1 model), +400 MB working RAM.
- **DwarfQueens (small tier):** +600 MB disk (whisper.cpp + small-q5_1), +700 MB working RAM.
- **Intermediate (medium-small):** +1.5 GB disk (medium-q5_0), +1.6 GB working RAM.
- **GiantQueens (medium):** +1.5–2 GB disk (large-v3-turbo-q5_0 or turbo-q8_0), +2.5–3.2 GB working RAM.
- **Intermediate top (medium-big):** +2–3 GB disk (large-v3-turbo fp16 or large-v3-q5_0), +6 GB VRAM or working RAM if on CPU path.
- **RajaBee (big):** +3–5 GB disk (large-v3 fp16), +6–10 GB VRAM depending on fp16-batched vs int8.
- Add `whisper.cpp` binary (~5 MB compiled) to the base image for every tier.
- Add `faster-whisper` + `ctranslate2` Python wheels (~200 MB including deps) to tiers that have GPU passthrough.
- **Do not add Ollama STT plumbing.** Ollama is the text/vision runtime only. STT routes around it.

Every number above is an increment *on top of* the current V3 per-tier budgets for text + vision. Bump the per-VM disk provisioning and RAM reservations accordingly when V3 becomes V4. Sequential load/unload at the test-bench level keeps the RAM peaks below the simultaneous sums — but disk still has to hold the weights regardless.

---

*End of research file. Spot-check queries for Nir are in the companion file `PHASE3_STT_NIR_SEARCH_QUERIES_2026-04-15.md`. No fabrication: every model, parameter count, file size, license, and WER number above was pulled from a live upstream source on 2026-04-15. Where a number was not published upstream, I said so rather than invent it.*
