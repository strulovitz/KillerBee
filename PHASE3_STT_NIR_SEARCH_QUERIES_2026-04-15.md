**SUPERSEDED by KillerBee/PHASE3_STT_AND_TOOLING_2026-04-15_v2.md — DO NOT USE, KEPT AS HISTORICAL REFERENCE.**

# Phase 3 STT — Spot-Check Search Queries for Nir — 2026-04-15

**Purpose:** high-signal search queries Nir can paste into Google / DuckDuckGo / HuggingFace / GitHub to independently verify the claims in `PHASE3_STT_RESEARCH_2026-04-15.md`. Every query is copy-paste ready. Under each query is a one-line note saying *what Nir should find when he runs it* — so the spot-check is a direct yes/no, not a guessing game.

---

## Group A — Landscape / what exists in 2026

1. `open source speech to text model 2026 benchmark`
   *Should surface: Whisper derivatives, NVIDIA Parakeet v3, distil-whisper, SenseVoice, Moonshine. If anything bigger and more recent shows up, we may have missed it.*

2. `whisper alternative multilingual 2026 open weights`
   *Should surface: Parakeet TDT v3, Canary, SenseVoice. Confirms there is no "Whisper killer" for Hebrew/Arabic yet.*

3. `open asr leaderboard huggingface`
   *Should land on `hf-audio/open-asr-leaderboard`. Confirms the WER numbers quoted for distil-large-v3 (7.52 mean) and parakeet-tdt-0.6b-v3 (6.34 mean).*

## Group B — Whisper family verification

4. `whisper.cpp README memory requirements site:github.com`
   *Should land on `ggml-org/whisper.cpp`. Verifies the disk/RAM table: tiny 75 MiB / ~273 MB, base 142 MiB / ~388 MB, small 466 MiB / ~852 MB, medium 1.5 GiB / ~2.1 GB, large 2.9 GiB / ~3.9 GB.*

5. `ggerganov/whisper.cpp huggingface large-v3-turbo q5_0`
   *Should land on `huggingface.co/ggerganov/whisper.cpp`. Verifies large-v3-turbo-q5_0 = 547 MiB, large-v3-turbo-q8_0 = 834 MiB.*

6. `openai whisper large-v3-turbo 809M parameters site:huggingface.co`
   *Should confirm 809 M parameters, 99 languages, MIT license, ~1.6 GB safetensors.*

7. `faster-whisper int8 VRAM benchmark large-v2`
   *Should confirm int8 large-v2 on RTX 3070 Ti = 2926 MB VRAM standard, 4500 MB at batch 8. Anchors the RajaBee GPU budget.*

## Group C — Distil-Whisper and English-only options

8. `distil-whisper/distil-large-v3 WER English only site:huggingface.co`
   *Should confirm 756 M params, English only, 9.7% short-form WER, 6.3x faster than large-v3. Flags the "no Hebrew" blocker.*

9. `moonshine useful sensors 27M parameters english`
   *Should confirm Moonshine tiny = 27 M, base = 61 M, English only, MIT, released Oct 2024.*

## Group D — NVIDIA NeMo family (Parakeet, Canary)

10. `nvidia/parakeet-tdt-0.6b-v3 languages list site:huggingface.co`
    *Should land on the v3 model card and list exactly these 25 languages: bg, hr, cs, da, nl, en, et, fi, fr, de, el, hu, it, lv, lt, mt, pl, pt, ro, sk, sl, es, sv, ru, uk. Confirms NO Hebrew, NO Arabic. Release date 2025-08-14.*

11. `nvidia/canary-1b license CC-BY-NC`
    *Should confirm CC-BY-NC-4.0 (non-commercial). This is why Canary is eliminated regardless of its excellent 1.48% LibriSpeech-clean WER.*

12. `parakeet-tdt-0.6b-v3 open asr leaderboard 6.34`
    *Should confirm average WER 6.34% on the HF Open ASR leaderboard. Anchors the "Parakeet beats Whisper on leaderboard but drops HE/AR" tradeoff.*

## Group E — SenseVoice and non-Whisper multilingual

13. `FunAudioLLM/SenseVoiceSmall language list hebrew arabic`
    *Should confirm SenseVoice covers Chinese/Cantonese/English/Japanese/Korean and 50+ total but does NOT explicitly list Hebrew or Arabic.*

14. `SenseVoiceSmall license terms github`
    *Should land on the FunAudioLLM repo. Nir should read the LICENSE file directly — the model card says "model-license" which is not a named OSI license.*

## Group F — Ollama STT hosting check

15. `ollama library whisper speech to text official`
    *Should confirm there is no first-class Ollama STT entry. Any hits are community mirrors (dimavz, karanchopda333, sendmeaiohyeah, anagram).*

16. `ollama supports audio input 2026 roadmap`
    *Should confirm Ollama's engine is still text/vision LLM-focused. If Ollama has shipped first-class STT since April 2026 this query will surface the announcement.*

## Group G — Hebrew / Arabic Whisper performance

17. `whisper large-v3 hebrew WER benchmark`
    *Should surface third-party Hebrew evaluations. OpenAI does not publish per-language WER. Used to sanity-check that Whisper large-v3 on Hebrew is usable before committing the ladder.*

18. `whisper large-v3 arabic dialect WER`
    *Same as above for Arabic. MSA vs dialect matters — Nir should expect dialect WER to be significantly worse than MSA.*

## Group H — Quantization sanity

19. `whisper.cpp quantization q5_0 q8_0 accuracy degradation`
    *Should confirm Q5_0 is the standard "cheap with minimal quality loss" quantization for whisper.cpp. Anchors the Q5_0 defaults in brackets 3-5.*

20. `faster-whisper int8_float16 vs float16 accuracy`
    *Should confirm int8_float16 is the standard mixed-precision path on faster-whisper and gives a latency win with a small accuracy cost. Anchors the alternate path for GPU tiers where VRAM is tight.*

---

**How to use this file:** Nir, pick 4-6 queries across at least three of the groups (A, B/C, D, F recommended at minimum) and run them yourself. If any query returns a result that contradicts what's in `PHASE3_STT_RESEARCH_2026-04-15.md`, that's a fabrication bug and you should tell Laptop Claude to have Desktop Claude fix and re-push. If all queries return the expected signals, the research is reliable and V3 can become V4 with the recommended STT ladder integrated.
