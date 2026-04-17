# Phase 3 RAM Measurement Session — 2026-04-17

**Host:** Laptop Linux (Debian 13), 62 GiB RAM, 58 GiB available at session start.
**Purpose:** Measure the real loaded RAM footprint of 3 candidate vision models for Laptop VM planning, because the `params x 0.6 GB` formula underestimated `qwen2.5vl:7b` by 2.8x on Desktop (expected ~4.5 GB, actual 12.5 GiB).

---

## COMMITMENT — DELETE ALL TEST MODELS AFTER MEASUREMENT

This file is the public record of the promise. If the log at the bottom does not show three deletion confirmations, the session is NOT complete.

**Test models to delete when measurement is done:**
- `minicpm-v:8b`
- `qwen3-vl:8b`
- `gemma3:12b`

**Host models to PRESERVE (were on host before session, must stay):**
- `llama2-uncensored:70b`
- `hf.co/bartowski/L3-70B-Euryale-v2.1-GGUF:Q5_K_M`
- `llama3.2:3b`

---

## Method

For each candidate model:
1. `free -h` baseline
2. `ollama pull <model>`
3. `ollama run <model>` with a real PNG test image prompt ("describe this image")
4. While loaded, run `free -h` and `ollama ps` to capture peak memory
5. `ollama stop <model>` to unload
6. Record observations

Done sequentially, one model at a time, smallest first (minicpm-v:8b at 5.7 GB disk), then qwen3-vl:8b (6.1 GB), then gemma3:12b (8.1 GB).

---

## Results — 2026-04-17 measurements

All measured on Laptop host with `num_gpu: 0` flag to force CPU-only inference (matching what VMs will experience, since §4.0 mandates no GPU passthrough). Same test image: 512x512 PNG with red square, blue circle, "Hello Hive" text. Prompt: "describe this image briefly".

| Model | Disk (q4) | `free -h` delta (real loaded RAM) | `ollama ps` claimed | Context | CPU inference time | Vision quality |
|---|---|---|---|---|---|---|
| minicpm-v:8b | 5.7 GB | **~5.6 GB** | 5.4 GB | 4K | 33s | Good — saw rect, circle, "Hello Hive" |
| qwen3-vl:8b | 6.1 GB | **~6.1 GB** | 11 GB | 8K | 53s | Best — colors + composition + full text + background |
| gemma3:12b | 8.1 GB | **~10.1 GB** | 10 GB | 4K | 66s | Good — verbose, accurate |

### Interpretation

- **Real loaded RAM** (`free -h` delta) is the honest number for VM planning.
- `ollama ps` can report higher than actual use when context window is large (qwen3-vl had 8K ctx and claimed 11 GB but only used 6.1 GB in reality) — appears to reserve context buffer speculatively.
- gemma3:12b's `ollama ps` (10 GB) matched real use (10.1 GB) — no speculation gap, because its context is only 4K.

### Verdict for a 12 GB VM (real RAM + ~1 GB OS + ~1.5 GB inference overhead)

- **minicpm-v:8b** — 5.6 + 2.5 = 8.1 GB used → 3.9 GB headroom — comfortable
- **qwen3-vl:8b** — 6.1 + 2.5 = 8.6 GB used → 3.4 GB headroom — comfortable
- **gemma3:12b** — 10.1 + 2.5 = 12.6 GB used → 0.6 GB over ceiling — same bad-tight as the current qwen2.5vl:7b gold

### Formula lesson learned

Old formula: `params x 0.6 GB per 1B = loaded size`. For these vision models:
- minicpm-v 8B: 0.7 GB per 1B (cleaner than expected)
- qwen3-vl 8B: 0.76 GB per 1B
- gemma3 12B: 0.84 GB per 1B

Vision models are ~15-40% larger loaded than the text formula predicts, and bigger models are disproportionately bigger. Future plans should measure before committing.

---

## Deletion log — COMPLETED 2026-04-17

All 3 test models successfully removed. Verified with `ollama list` showing only the pre-existing host models remain.

- [x] `ollama rm minicpm-v:8b` — DONE
- [x] `ollama rm qwen3-vl:8b` — DONE
- [x] `ollama rm gemma3:12b` — DONE

### Post-deletion `ollama list` (proof):

```
NAME                                               ID              SIZE      MODIFIED
llama2-uncensored:70b                              bdd0ec2f5ec5    38 GB     5 months ago
hf.co/bartowski/L3-70B-Euryale-v2.1-GGUF:Q5_K_M    1c651cddf488    49 GB     5 months ago
llama3.2:3b                                        a80c4f17acd5    2.0 GB    5 months ago
```

Only the 3 pre-existing host models remain. Test image `/tmp/test_vision.png` also deleted.

**Promise kept.**

---

*Canonical. Edit in place. Git is the time machine.*
