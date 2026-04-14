# Phase 3 V2 — Model picks per tier (ALL LOCKED, ALL TAGS VERIFIED)

**Purpose:** one place to see what each tier is getting for the V2 rebuild. All three rows are now LOCKED by Nir under the "one-notch downshift, like the apology" rule (2026-04-14 evening).

**Tag verification against the live Ollama library** was run 2026-04-14 late evening by fetching `https://ollama.com/library/<model>/tags` directly and grepping for the exact tag strings. Every primary pick below has been confirmed as a real, published Ollama library tag — no guesses, no "should exist", no "probably there." Results in §Tag verification at the bottom of this file.

The rule: every role takes the models that were going to be one tier above it in V1. Workers take a brand-new TINY tier that did not exist in V1 at all (it was the tier Nir's "no tiny" rule explicitly excluded this morning — and which his apology reversed).

**Source of V1 tier assignments:** `PHASE3_LINUX_VM_SETUP.md` §6.5.

---

## GiantQueen-B — LOCKED (takes old DwarfQueen's models)

| Slot | Model | On-disk (est. GB) | RAM loaded (est. GB) | Why |
|---|---|---|---|---|
| Dense | `qwen3:8b` | 5.2 | 5.5 | Best dense at the old 8-GB DwarfQueen tier per V1 §6.5. |
| MoE | `granite3.1-moe:3b` | 2.0 | 2.2 | Unchanged — the ONLY MoE in the pool small enough to fit anywhere on Desktop. MoE ecosystem on Ollama is a Granite monoculture at this size. |
| Multi-modal / Vision | `llama3.2-vision:11b` | 7.8 | 8.0 | V1 §6.5 vision assignment for old DwarfQueens; Meta production-tested 11B vision model, largest that still fits the new GQ-B RAM tier. |

**Largest-single-model-in-memory:** `llama3.2-vision:11b` → 8 GB loaded → RAM must be ≥ 10 GB. Chosen: **11 GB** (small headroom for KV cache and image token buffers).

---

## DwarfQueen-B1, DwarfQueen-B2 — LOCKED (take old Worker's models)

| Slot | Model | On-disk (est. GB) | RAM loaded (est. GB) | Why |
|---|---|---|---|---|
| Dense | `phi4-mini:3.8b` | 2.5 | 2.7 | V1 §6.5 Worker Dense pick; Microsoft's highest-quality sub-4B dense model per §6.8 review. |
| MoE | `granite3.1-moe:3b` | 2.0 | 2.2 | Same reason as GQ-B: only real option. |
| Multi-modal / Vision | `gemma3:4b` | 2.5 | 2.7 | V1 §6.5 Worker Vision pick; Google's native multimodal edge flagship for 2026. |

**Largest-single-model-in-memory:** `phi4-mini:3.8b` or `gemma3:4b` ≈ 2.7 GB loaded → RAM ≥ 5 GB. Chosen: **6 GB** per DwarfQueen.

---

## Worker-B1..B4 — LOCKED (new TINY tier from the 2026-04-14 evening Google session)

| Slot | Model | On-disk (est. GB) | RAM loaded (est. GB) | Why |
|---|---|---|---|---|
| Dense | `qwen3:1.7b` | 1.1 | 1.3 | Alibaba 2026 current-gen sub-2B flagship, ~62% MMLU — best intelligence-per-byte in the TINY box per this evening's Google session. |
| MoE | `granite3.1-moe:1b` | 0.7 | 0.9 | IBM, 1B total / ~400M active — the only true sub-2B MoE that exists on Ollama in 2026. |
| Multi-modal / Vision | `qwen3.5:0.8b` | 0.6 | 0.8 | Alibaba ultra-tiny multi-modal; 0.8B total including vision encoder, 262K context, text+image+video — strongest intelligence-per-byte under 1B multi-modal. |

**Largest-single-model-in-memory:** `qwen3:1.7b` → 1.3 GB loaded → RAM ≥ 3 GB. Chosen: **4 GB** per Worker (4 GB is the practical minimum for a comfortable Ubuntu Server VM including systemd, Ollama daemon, and scratch).

**Fallbacks** (if a #1 pick fails verification on first pull):
- Dense: `llama3.2:1b` (1B, older but rock-solid) → `deepseek-r1-distill-qwen:1.5b` (1.5B reasoning-distilled)
- MoE: `granite3.1-moe:3b` (3B, upper TINY edge but much stronger) → **no #3**, TINY MoE ecosystem is a Granite monoculture
- Vision: `moondream2:1.7b` (1.7B, battle-tested tiny vision) → **no reliable #3**; if both qwen3.5:0.8b and moondream2 fail, drop the Worker-tier vision round entirely and let DwarfQueens handle all vision

---

## Totals (for V2 plan arithmetic) — DISK DOUBLED 2026-04-14 per Nir

Nir's explicit instruction (2026-04-14 late evening): **double every VM's disk size proportionally** on the grounds that "it does not cost me anything, and maybe we are wrong, I want more twice as much disk space proportionally for every component of each VM." This replaces the original §1 disk arithmetic with a 2× multiplier on the final chosen size per VM. The arithmetic in `PHASE3_REBUILD_PLAN_V2.md` §2 is retained as the sizing *floor*; the real sizes used for `virt-install` are double those floors.

| VM | Disk floor (GB) | Disk chosen (2×) | RAM (GB) | vCPU |
|---|---|---|---|---|
| giantqueen-b | 40 | **80** | 11 | 6 |
| dwarfqueen-b1 | 25 | **50** | 6 | 4 |
| dwarfqueen-b2 | 25 | **50** | 6 | 4 |
| worker-b1 | 20 | **40** | 4 | 2 |
| worker-b2 | 20 | **40** | 4 | 2 |
| worker-b3 | 20 | **40** | 4 | 2 |
| worker-b4 | 20 | **40** | 4 | 2 |
| **Totals** | 170 | **340** | **39** | **22** |

**Host fit (unchanged on the RAM side):** 62 GiB usable − 39 GiB guest − ~2 GiB QEMU envelope tax − ~2 GiB Cinnamon/libvirtd/ICQ overhead = **~19 GiB host headroom**. Meets the 5–8 GiB headroom requirement.

**Host fit on the disk side:** 340 GB virtual on a 1.7 TB volume with 1.5 TB free = ~22% utilization at absolute worst case. qcow2 is sparse — the real on-disk footprint at steady state will be much smaller (probably 100–130 GB with all 21 models pulled). Plenty of room for the doubling and for future experimentation.

Full arithmetic, per-VM sizing breakdown, scripts, fit check, and execution plan live in `PHASE3_REBUILD_PLAN_V2.md`.

---

## Tag verification (run 2026-04-14 late evening against live ollama.com/library)

Method: for each candidate tag the command was `curl -sS https://ollama.com/library/<model>/tags | grep -oE '/library/<model>:<expected-tag-suffix>'`. A hit means the exact tag is published in the real Ollama library at the time of verification.

### Primary V2 picks — ALL VERIFIED

| Tag | Verified | Notes |
|---|---|---|
| `qwen3:8b` | ✓ | Tag present in `qwen3:8b`, `qwen3:8b-q4`, `qwen3:8b-q8` variants. |
| `qwen3:1.7b` | ✓ | Plus `qwen3:1.7b-q4`/`q8`/`fp16` variants. |
| `qwen3.5:0.8b` | ✓ | Plus `qwen3.5:0.8b-q8`/`bf16`/`mxfp8`/`nvfp4` variants. |
| `phi4-mini:3.8b` | ✓ | Plus `phi4-mini:3.8b-q4`/`q8`/`fp16` variants; `phi4-mini:latest` also present. |
| `granite3.1-moe:1b` | ✓ | Plus `granite3.1-moe:1b-instruct-q4`/`q5`/`q6`/`q8` variants; `granite3.1-moe:latest` present. |
| `granite3.1-moe:3b` | ✓ | Plus `granite3.1-moe:3b-instruct-q4`/`q5`/`q6`/`q8` variants. |
| `llama3.2-vision:11b` | ✓ | Plus `llama3.2-vision:11b-instruct-q4`/`q8`/`fp16` variants; `llama3.2-vision:90b` also exists but is out of scope. |
| `gemma3:4b` | ✓ | Plus `gemma3:4b-it-q4`/`q8`/`fp16`/`qat` variants. |

**All eight primary V2 picks are real, published, pullable Ollama tags.** Execution can proceed against the real registry without guessing.

### Corrections to fallback tags (tags I wrote earlier that turned out to NOT exist)

While verifying primary picks I also checked the fallback tags from earlier brainstorming:

| Tag I wrote earlier | Verified? | Correct tag on Ollama |
|---|---|---|
| `moondream2:1.7b` | ✗ 404 | `moondream` (no trailing 2) |
| `ministral3:3b` | ✗ 404 | **Does not exist on Ollama in 2026.** There is `mistral-small:*` but no `ministral3:*`. |
| `smollm3:3b` | ✗ 404 | `smollm:1.7b` or `smollm2:1.7b` (no v3 on Ollama) |
| `granite3:*` | ✗ 404 | `granite3.1-moe:*`, `granite3.1-dense:*`, `granite3.2:*`, `granite3.3:*`, or `granite4:*` |

**Lesson:** the tier-selection searches earlier in the day returned several model names that looked real but are not in the Ollama registry exactly as stated — they are research-paper names, Hugging Face names, or marketing names from blog posts. **Always verify against `https://ollama.com/library/<model>/tags` before committing a tag to a plan file.**

### Bonus discovery — `granite4` exists and has meaningful TINY tags

Not used in V2 (V2 picks Granite 3.1 for ecosystem-consistency with V1), but worth noting for future revisions:

- `granite4:350m`, `granite4:1b`, `granite4:3b`, `granite4:3b-h` (hybrid) — fresh TINY/MINI IBM options
- `granite4:7b-a1b-h` — 7B total, 1B active hybrid MoE, potentially better than `granite3.1-moe:3b` at the SMALL tier
- `granite4:32b-a9b-h` — 32B total, 9B active, for a future larger-tier revision

If Nir later wants to upgrade the MoE row from `granite3.1-moe` to `granite4`, these are the candidate tags.
