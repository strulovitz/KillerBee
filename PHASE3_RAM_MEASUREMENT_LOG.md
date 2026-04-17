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

## Results

Will be filled in as measurements complete.

| Model | Disk (q4) | Loaded RAM (measured) | `ollama ps` size | Verdict for 12 GB VM |
|---|---|---|---|---|
| minicpm-v:8b | 5.7 GB | PENDING | PENDING | PENDING |
| qwen3-vl:8b | 6.1 GB | PENDING | PENDING | PENDING |
| gemma3:12b | 8.1 GB | PENDING | PENDING | PENDING |

---

## Deletion log

Will be filled in after each deletion as proof.

- [ ] `ollama rm minicpm-v:8b` — not yet executed
- [ ] `ollama rm qwen3-vl:8b` — not yet executed
- [ ] `ollama rm gemma3:12b` — not yet executed

---

*Canonical. Edit in place. Git is the time machine.*
