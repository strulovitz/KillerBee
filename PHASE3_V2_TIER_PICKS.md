# Phase 3 V2 — Model picks per tier (ALL LOCKED)

**Purpose:** one place to see what each tier is getting for the V2 rebuild. All three rows are now LOCKED by Nir under the "one-notch downshift, like the apology" rule (2026-04-14 evening).

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

## Totals (for V2 plan arithmetic)

| VM | Disk (GB) | RAM (GB) | vCPU |
|---|---|---|---|
| giantqueen-b | 40 | 11 | 6 |
| dwarfqueen-b1 | 25 | 6 | 4 |
| dwarfqueen-b2 | 25 | 6 | 4 |
| worker-b1 | 20 | 4 | 2 |
| worker-b2 | 20 | 4 | 2 |
| worker-b3 | 20 | 4 | 2 |
| worker-b4 | 20 | 4 | 2 |
| **Totals** | **170** | **39** | **22** |

**Host fit:** 62 GiB usable − 39 GiB guest − ~2 GiB QEMU envelope tax − ~2 GiB Cinnamon/libvirtd/ICQ overhead = **~19 GiB host headroom**. Meets the 5–8 GiB headroom requirement from the downgrade brief with comfortable margin.

Full arithmetic, per-VM sizing breakdown, scripts, fit check, and execution plan live in `PHASE3_REBUILD_PLAN_V2.md`.
