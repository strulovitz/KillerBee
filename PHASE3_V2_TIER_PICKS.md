# Phase 3 V2 — Model picks per tier (living document)

**Purpose:** lock the model choices for the V2 rebuild (the downshifted plan from `claude-memory/KILLERBEE_DOWNGRADE_2026-04-14.md`), one row at a time, as Nir approves each tier. Once all three rows are locked, this file feeds directly into `PHASE3_REBUILD_PLAN_V2.md`.

**Status key:** **LOCKED** = Nir has explicitly approved. **PENDING** = awaiting Nir decision.

---

## Worker-B1..B4 (TINY tier) — LOCKED 2026-04-14 by Nir

| Slot | Model | Why |
|---|---|---|
| Dense | `qwen3:1.7b` | Alibaba 2026 current-gen sub-2B flagship, ~62% MMLU — best intelligence-per-byte in the whole TINY box. |
| MoE | `granite3.1-moe:1b` | IBM, 1B total / ~400M active — the only true sub-2B MoE that exists on Ollama in 2026. |
| Multi-modal / Vision | `qwen3.5:0.8b` | Alibaba ultra-tiny multi-modal, 0.8B total including vision encoder, 262K context — the strongest intelligence-per-byte in the sub-1B multi-modal bracket. |

**Alternatives considered** (kept as fallbacks if the #1 choices fail verification on first pull):
- Dense #2: `llama3.2:1b` (Meta 1B text, rock-solid, older)
- Dense #3: `deepseek-r1-distill-qwen:1.5b` (1.5B reasoning-distilled, unique chain-of-thought focus)
- MoE #2: `granite3.1-moe:3b` (3B, upper-edge of TINY, stronger but bigger)
- MoE #3: *does not exist* — TINY MoE is a Granite monoculture on Ollama in 2026
- Vision #2: `moondream2:1.7b` (1.7B, battle-tested image captioning, safe fallback)
- Vision #3: *flagged* — "llama3.2:1b-vision" appears in Google summaries but cannot be confirmed as a real Ollama tag; Meta's official Llama-3.2-Vision is 11B/90B only

---

## DwarfQueen-B1, DwarfQueen-B2 — PENDING

Awaiting Nir's D1-vs-D2 decision (see bottom of this file). Candidates depend on which downshift rule applies.

---

## GiantQueen-B — PENDING

Awaiting Nir's D1-vs-D2 decision (see bottom of this file). Candidates depend on which downshift rule applies.

---

## Open decision: one-notch downshift (D1) vs two-notch downshift (D2)

Both options lock Workers at TINY (as above). They differ in what the DwarfQueens and GiantQueen-B get.

### Option D1 — one-notch downshift (each role moves down exactly one tier)

| VM | Dense | MoE | Vision | RAM |
|---|---|---|---|---|
| GiantQueen-B | `phi4-mini:3.8b` (SMALL, ~2.5 GB) | `granite3.1-moe:3b` (~2 GB) | `gemma3:4b` (~2.5 GB) | 6 GB |
| DwarfQueen-B1/B2 | `gemma4:e2b` (MINI, 2.3 GB) | `granite3.1-moe:3b` (~2 GB) | `ministral3:3b` (~2.5 GB) *or* `moondream2:1.7b` (~1.7 GB) | 5 GB each |
| Worker-B1..B4 | `qwen3:1.7b` (~1.1 GB) | `granite3.1-moe:1b` (~0.7 GB) | `qwen3.5:0.8b` (~0.6 GB) | 4 GB each |
| **Totals** | | | | **32 GB guest, ~30 GB host headroom** |

### Option D2 — two-notch downshift (what we were about to do before Nir added the in-between tier)

| VM | Dense | MoE | Vision | RAM |
|---|---|---|---|---|
| GiantQueen-B | `qwen3:8b` (~5.2 GB) | `granite3.1-moe:3b` (~2 GB) | `llama3.2-vision:11b` (~7.8 GB) *or* `qwen3-vl:8b` (~5 GB) | 10 GB *or* 8 GB |
| DwarfQueen-B1/B2 | `phi4-mini:3.8b` (~2.5 GB) | `granite3.1-moe:3b` (~2 GB) | `gemma3:4b` (~2.5 GB) | 6 GB each |
| Worker-B1..B4 | `qwen3:1.7b` | `granite3.1-moe:1b` | `qwen3.5:0.8b` | 4 GB each |
| **Totals** | | | | **38 GB guest, ~20 GB host headroom** (11b vision) or **36 GB, ~22 GB** (8b vision) |

**Tradeoff:**
- **D1** gives more host headroom, smaller tier variance (GQ is only slightly bigger than DQ).
- **D2** keeps GiantQueen-B meaningfully bigger than DwarfQueens, preserving the hierarchy variance that makes the KillerBee hive test interesting.

**Open questions for Nir:**

1. **D1 or D2?**
2. **(Only if D2)** GiantQueen-B vision = `llama3.2-vision:11b` (stronger but 7.8 GB model, GQ RAM must be 10 GB) *or* `qwen3-vl:8b` (smaller 5 GB model, GQ RAM can stay at 8 GB)?

Once these are answered, this file gets the remaining rows filled in, then `PHASE3_REBUILD_PLAN_V2.md` gets drafted with full disk/RAM/vCPU/fit-check arithmetic.
