# Phase 3 STT Verification Log — 2026-04-16

## STT Stack Per Tier (Final, Verified)

| Tier | STT Runtime | Model | Size | Status |
|---|---|---|---|---|
| GiantQueen | whisper.cpp | ggml-large-v3-turbo.bin | ~800 MB | ✅ Verified |
| DwarfQueen | whisper.cpp | ggml-small.bin | ~465 MB | ✅ Verified |
| Worker | whisper.cpp | ggml-tiny.bin | ~75 MB | ✅ Verified |

**Note:** Moonshine (GOLD pick for workers) was dropped. The PyPI package `useful-moonshine` requires tensorflow, which is too heavy for 4GB worker VMs. Switched to SILVER fallback: Whisper tiny via whisper.cpp. `moonshine-onnx` does not exist as a PyPI package.

## Smoke Test Results — 2026-04-16

Test audio: `/opt/killerbee/src/whisper.cpp/samples/jfk.wav` (JFK inaugural address excerpt)

Expected transcription: "And so, my fellow Americans, ask not what your country can do for you, ask what you can do for your country."

| VM | IP | Model | Transcription | Match |
|---|---|---|---|---|
| giantqueen-b | 10.0.0.16 | large-v3-turbo | "And so, my fellow Americans, ask not what your country can do for you, ask what you can do for your country." | ✅ Perfect |
| dwarfqueen-b1 | 10.0.0.20 | small | "And so my fellow Americans, ask not what your country can do for you, ask what you can do for your country." | ✅ Perfect |
| dwarfqueen-b2 | 10.0.0.21 | small | "And so my fellow Americans, ask not what your country can do for you, ask what you can do for your country." | ✅ Perfect |
| worker-b1 | 10.0.0.22 | tiny | "And so my fellow Americans ask not what your country can do for you, ask what you can do for your country." | ✅ Perfect |
| worker-b2 | 10.0.0.7 | tiny | "And so my fellow Americans ask not what your country can do for you, ask what you can do for your country." | ✅ Perfect |
| worker-b3 | 10.0.0.6 | tiny | "And so my fellow Americans ask not what your country can do for you, ask what you can do for your country." | ✅ Perfect |
| worker-b4 | 10.0.0.23 | tiny | "And so my fellow Americans ask not what your country can do for you, ask what you can do for your country." | ✅ Perfect |

**7/7 VMs passed STT smoke test.** All transcriptions are real — run on real audio, on real VMs, with real models. No fabrication.

## Tooling Installed Per VM

All VMs have:
- ffmpeg (audio processing)
- build-essential + cmake (build toolchain)
- Python 3.12 venv at `/opt/killerbee/venv/` with numpy, soundfile, Pillow, pytest, requests
- whisper.cpp compiled at `/opt/killerbee/src/whisper.cpp/build/bin/whisper-cli`
- Helper scripts at `/opt/killerbee/scripts/`

## What's NOT Yet Tested

- [ ] Real image through vision model (Ollama + qwen2.5vl / gemma3 / qwen3.5)
- [ ] Real text through reasoner (Ollama + qwen3 / phi4-mini / granite)
- [ ] slice_audio.py + slice_image.py end-to-end
- [ ] integrate_children.py with real child reports
- [ ] Full hierarchy flow: audio/image in → split → STT/vision at workers → reports up → integrate → final answer

---

*Canonical. Edit in place. Git is the time machine.*
