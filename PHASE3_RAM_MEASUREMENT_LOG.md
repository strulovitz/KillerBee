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

# Session 2 — qwen3:14b measurement (Dense LLM for RajaBee)

**Date:** 2026-04-17 (same day, later).
**Purpose:** Measure real CPU-only loaded RAM of `qwen3:14b` before planning RajaBee (16 GB VM on Laptop). This is the dense text reasoning model for the top tier of the downgraded hierarchy.

## COMMITMENT — DELETE AFTER MEASUREMENT

**Test model to delete:** `qwen3:14b`

**Host models to PRESERVE:** `llama2-uncensored:70b`, `hf.co/bartowski/L3-70B-Euryale-v2.1-GGUF:Q5_K_M`, `llama3.2:3b`

## Method

1. `free -h` baseline
2. `ollama pull qwen3:14b` (approximately 9 GB download at q4_K_M)
3. Inference via API with `options.num_gpu=0` and a short reasoning prompt
4. `free -h` again to capture delta; `ollama ps` to capture Ollama's claimed size
5. Unload (`keep_alive: 0`) and `ollama rm qwen3:14b`
6. Record results below

## Results — 2026-04-17 session 2

Measured on Laptop host with `num_gpu: 0` for CPU-only. Prompt: `"What is the capital of France? Answer in one sentence."` (short reasoning task for a dense text model — no image since qwen3:14b is not multimodal).

| Model | Disk (q4) | `free -h` delta (real) | `ollama ps` claimed | Context | CPU inference time | Response |
|---|---|---|---|---|---|---|
| qwen3:14b | 9.0 GB | **~9.0 GB** | 10 GB | 4K | 53s | "Paris is the capital of France." (correct) |

### Verdict for RajaBee 16 GB VM

- Real loaded RAM: 9.0 GB
- Plus OS: ~1 GB
- Plus inference KV cache + activations: ~1.5 GB
- **Total in-VM use: ~11.5 GB** in 16 GB VM
- **Headroom: ~4.5 GB** — very comfortable, no swap spill risk

Since Ollama lazy-loads one model at a time per tier, the biggest single resident is qwen3:14b (9 GB loaded). Other RajaBee residents (qwen3-vl:8b at 6.1 GB, granite3.1-moe:3b at ~2-3 GB, whisper large-v3-turbo a few hundred MB) each load separately and are all smaller than qwen3:14b, so they also fit comfortably.

### Formula check — updated for dense text models

`qwen3:14b` loaded 9 GB per 14B params = **0.64 GB per 1B params** — very close to the classic `params x 0.6` rule. Dense text models follow the classic formula closely. Vision models (as noted in session 1) load 15-40% bigger than this formula predicts because of the vision encoder + image-token KV cache.

Takeaway: `params x 0.6 GB` is reliable for dense text, not reliable for vision. Always measure vision models before committing.

## Deletion log — COMPLETED 2026-04-17

- [x] `ollama rm qwen3:14b` — DONE

### Post-deletion `ollama list`:

```
NAME                                               ID              SIZE      MODIFIED
llama2-uncensored:70b                              bdd0ec2f5ec5    38 GB     5 months ago
hf.co/bartowski/L3-70B-Euryale-v2.1-GGUF:Q5_K_M    1c651cddf488    49 GB     5 months ago
llama3.2:3b                                        a80c4f17acd5    2.0 GB    5 months ago
```

Only the 3 pre-existing host models remain. **Promise kept.**

---

# Session 3 — gemma4:e4b measurement (Vision for GiantQueen tier)

**Date:** 2026-04-17 (same day, later still).
**Purpose:** Measure real CPU-only loaded RAM of `gemma4:e4b` (Google, April 2026, confirmed 52.6% MMMU Pro) as a potential upgrade for BOTH GiantQueens (Desktop giantqueen-b and Laptop giantqueen-a, both 12 GB VMs). Currently those VMs plan / run `qwen3-vl:8b` at 6.1 GB loaded. If gemma4:e4b fits comfortably at similar RAM, it is a pure quality upgrade — 52.6% MMMU Pro vs qwen3-vl:8b's "competitive with gemma3" claim.

## COMMITMENT — DELETE AFTER MEASUREMENT

**Test model to delete:** `gemma4:e4b`

**Host models to PRESERVE:** `llama2-uncensored:70b`, `hf.co/bartowski/L3-70B-Euryale-v2.1-GGUF:Q5_K_M`, `llama3.2:3b`

## Method

Same as sessions 1 and 2: baseline `free -h`, pull, load with the same 512x512 PNG test image (red square + blue circle + "Hello Hive" text) via API with `num_gpu: 0`, measure `free -h` delta + `ollama ps`, unload + delete.

## Results — 2026-04-17 session 3

Required an Ollama upgrade from 0.12.10 to 0.21.0 on the Laptop host first (gemma4 is too new for 0.12.x). Existing config preserved, existing three host models intact.

| Model | Disk (q4) | `free -h` delta (real) | `ollama ps` claimed | Context | CPU inference time | Vision output |
|---|---|---|---|---|---|---|
| gemma4:e4b | 9.6 GB | **~10.2 GB** | 11 GB | 32K | 148s | Identified shapes correctly, but hallucinated the "Hello Hive" text as appearing in two locations (it is only in one) |

### Verdict

**gemma4:e4b is NOT a better fit for either GiantQueen (12 GB VMs).**

Fit analysis for 12 GB VM: 10.2 GB model + 1 GB OS + 1.5 GB inference = 12.7 GB used → **0.7 GB overflow** → same bad-tight swap-spill pattern we just removed from Desktop giantqueen-b. The model won the benchmark paper race (52.6% MMMU Pro) but loses the apartment fit, and also hallucinated more than qwen3-vl:8b did on the same test image (gemma4:e4b saw "Hello Hive" twice — the image has it only once; qwen3-vl:8b counted it correctly during session 1).

### Decisions locked by measurement

- **Both GiantQueens (Desktop giantqueen-b and Laptop giantqueen-a): KEEP `qwen3-vl:8b`** (6.1 GB measured, fits 12 GB VM with ~3.4 GB headroom, counted correctly on the test).
- **RajaBee: KEEP `gemma3:12b`** (10.1 GB measured, fits 16 GB VM with ~3.4 GB headroom).
- **No changes to `PHASE3_LAPTOP_ROSTER_LOCKED.md`.**

### Lesson learned for future vision measurements

Default context size matters a lot. gemma4's 32K default context inflated its KV cache vs qwen3-vl's 8K or gemma3's 4K. If we ever reconsider gemma4:e4b, we should test it with explicit `num_ctx: 4096` to see the minimum RAM — but the inference-speed-on-CPU gap (148s vs 53s) is probably not worth re-investigating regardless.

## Deletion log — COMPLETED 2026-04-17

- [x] `ollama rm gemma4:e4b` — DONE

### Post-deletion `ollama list`:

```
NAME                                               ID              SIZE      MODIFIED
llama2-uncensored:70b                              bdd0ec2f5ec5    38 GB     5 months ago
hf.co/bartowski/L3-70B-Euryale-v2.1-GGUF:Q5_K_M    1c651cddf488    49 GB     5 months ago
llama3.2:3b                                        a80c4f17acd5    2.0 GB    5 months ago
```

Only the 3 pre-existing host models remain. Test image `/tmp/test_vision.png` also deleted. **Promise kept.**

### Side notes about this session

- Ollama upgraded from 0.12.10 to 0.21.0 (required for gemma4 family). `/etc/systemd/system/ollama.service.d/override.conf` preserved, all GPU + context settings intact.
- NOPASSWD sudo rule installed at `/etc/sudoers.d/99-nir-temp` during this session to allow autonomous sudo for future Phase 3 Laptop build work (KVM stack install, br0 bridge, etc.). To revoke later: `sudo rm /etc/sudoers.d/99-nir-temp`.

---

*Canonical. Edit in place. Git is the time machine.*
