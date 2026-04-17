# Phase 3 Laptop Build — Locked Roster

**Locked:** 2026-04-17 by Nir via Laptop Claude.
**Host:** Laptop Linux (Debian 13 Trixie), 62 GiB RAM, RTX 5090, 10.0.0.8.
**Guest OS for ALL Laptop VMs:** Debian 13 Trixie netinst (NOT Ubuntu).
**Status:** Planned. Not yet built. KVM stack not yet installed on Laptop.

---

## Roster

All models downgraded one notch from the original flagship plan per `claude-memory/KILLERBEE_DOWNGRADE_2026-04-14.md`. Vision model for both GiantQueens is set to the measured-and-verified `qwen3-vl:8b` (see `PHASE3_RAM_MEASUREMENT_LOG.md`), matching the newly swapped Desktop giantqueen-b.

| VM | IP slot | RAM | vCPU | Dense | MoE | Vision | STT |
|---|---|---|---|---|---|---|---|
| rajabee | 10.0.0.11 | 16 GB | 6 | qwen3:14b | granite3.1-moe:3b | **qwen3.5:9b** | whisper large-v3-turbo |
| giantqueen-a | 10.0.0.12 | 12 GB | 6 | qwen3:8b | granite3.1-moe:3b | **qwen3-vl:8b** | whisper small |
| dwarfqueen-a1 | 10.0.0.13 | 6 GB | 4 | phi4-mini:3.8b | granite3.1-moe:3b | gemma3:4b | whisper tiny |
| dwarfqueen-a2 | 10.0.0.14 | 6 GB | 4 | phi4-mini:3.8b | granite3.1-moe:3b | gemma3:4b | whisper tiny |
| worker-a1 | 10.0.0.15 | 4 GB | 2 | qwen3:1.7b | granite3.1-moe:1b | qwen3.5:0.8b | whisper tiny |
| worker-a2 | 10.0.0.16 | 4 GB | 2 | qwen3:1.7b | granite3.1-moe:1b | qwen3.5:0.8b | whisper tiny |
| worker-a3 | 10.0.0.17 | 4 GB | 2 | qwen3:1.7b | granite3.1-moe:1b | qwen3.5:0.8b | whisper tiny |
| worker-a4 | 10.0.0.18 | 4 GB | 2 | qwen3:1.7b | granite3.1-moe:1b | qwen3.5:0.8b | whisper tiny |

**Total guest RAM:** 16 + 12 + 6 + 6 + 4 x 4 = 56 GB on 62 GiB host → 6 GB host headroom (matches downgrade brief rule of 5-8 GB minimum host headroom).

**Total vCPU:** 6 + 6 + 4 + 4 + 2 x 4 = 26 vCPU on 24 CPUs host. Slight overcommit OK since KillerBee inference is model-bound and not all VMs saturate CPUs simultaneously.

## Vision choices per tier

**GiantQueens (both) — `qwen3-vl:8b`** (Nir's 2026-04-17 alignment decision):
- **giantqueen-b** (Desktop 10.0.0.16, 12 GB VM) — swapped on 2026-04-17 from qwen2.5vl:7b, see `PHASE3_VISION_SWAP_GIANTQUEEN.md` and commit 045b4cf
- **giantqueen-a** (Laptop 10.0.0.12, 12 GB VM) — planned (this file)
- Rationale: measured CPU-only loaded RAM of `qwen3-vl:8b` is 6.1-6.3 GB, fits 12 GB VM with ~3.4 GB headroom and zero swap spill. `gemma4:e4b` was tested as an alternative on 2026-04-17 and rejected: overflowed 12 GB VM by ~0.7 GB, 3x slower on CPU, and hallucinated the test image (session 3 in `PHASE3_RAM_MEASUREMENT_LOG.md`, commit 6aedf68).

**RajaBee — `qwen3.5:9b`** (locked 2026-04-17 after session 4 measurement):
- rajabee (Laptop 10.0.0.11, 16 GB VM)
- Rationale: `qwen3.5:9b` scores 69.2% on MMMU Pro vs `gemma3:12b`'s 50.3% and `qwen3-vl:8b`'s 56.6% — the strongest vision benchmark in our pool that still fits a 16 GB VM. Measured CPU-only loaded RAM is 8.1 GB (free -h delta), 9.6 GB (ollama ps conservative). In 16 GB VM: 10.6 GB used, 5.4 GB headroom, no swap spill risk. Slower inference (161s CPU vs 53s for qwen3-vl:8b) is acceptable at the top tier per §4.0 "quality over speed." Session 4 in `PHASE3_RAM_MEASUREMENT_LOG.md` (commit 38088fe).
- Why not for GiantQueens: same model in 12 GB VM would run 10.6 GB used with only 1.4 GB headroom (by free -h) or overflow by 0.1 GB (by ollama ps conservative reservation). Recreates the bad-tight pattern we removed from giantqueen-b this morning.

## Still-unmeasured models (risk surface)

These models are planned but not yet measured on CPU-only in any VM:

- `qwen3:14b` (RajaBee Dense) — estimated ~9-11 GB loaded at q4. 16 GB RajaBee VM should fit, but unmeasured.
- `qwen3:8b` (GiantQueen-A Dense) — Desktop has `qwen3:8b` working inside giantqueen-b per `PHASE3_REBUILD_STATUS.md` smoke test, so RAM fit is considered proven for the 12 GB tier.
- `phi4-mini:3.8b` (DwarfQueen Dense) — Desktop has this working inside dwarfqueen-b1 / b2.
- `gemma3:4b` (DwarfQueen Vision) — Desktop has this working.
- `granite3.1-moe:3b`, `granite3.1-moe:1b` (MoE at every tier) — all measured on Desktop.
- `qwen3:1.7b` (Worker Dense), `qwen3.5:0.8b` (Worker Vision) — all measured on Desktop.

**Recommended before RajaBee build:** measure `qwen3:14b` CPU-only on Laptop host using the same method as `PHASE3_RAM_MEASUREMENT_LOG.md`, confirm fit in a 16 GB VM (target: loaded RAM + OS + inference <= 14 GB, leaving ~2 GB VM headroom + ~6 GB host headroom).

## Prerequisites NOT YET DONE on Laptop

- KVM stack not installed (`qemu-kvm`, `libvirt-daemon-system`, `libvirt-clients`, `bridge-utils`, `virtinst`, `virt-manager`, `qemu-utils`, `genisoimage`)
- User `nir` not yet in `libvirt` or `kvm` groups
- No `br0` bridge on `enp129s0`
- No `/etc/sudoers.d/claude-kvm` or equivalent NOPASSWD rule for autonomous Claude work
- No `~/.ssh/phase3_ed25519` key pair
- No Debian 13 Trixie netinst ISO downloaded
- No Debian preseed file written (the existing scripts are Ubuntu-autoinstall, not Debian-d-i)
- No `killerbee` libvirt pool

## Build order (once prerequisites are done)

1. Build `rajabee` first (biggest VM, flushes out any bad assumptions early). Provision Ollama + STT tooling + model pulls. Full smoke test.
2. Clone `giantqueen-a` from rajabee or build fresh. Resize to 12 GB. Pull correct models. Smoke test.
3. Clone `dwarfqueen-a1`, `dwarfqueen-a2` sequentially. Resize to 6 GB. Pull correct models. Smoke test each.
4. Clone `worker-a1` through `worker-a4` sequentially. Resize to 4 GB. Pull correct models. Smoke test each.
5. Full cluster verification (all 8 VMs up, all models respond via `curl http://<ip>:11434/api/tags`).
6. End-to-end hierarchy smoke test: RajaBee -> GiantQueen-A -> DwarfQueens -> Workers on a real multimodal job.

---

*Canonical. Edit in place. Git is the time machine.*
