# Phase 3 Rebuild Status — 2026-04-16

**Status: 7/7 VMs UP — ALL MODELS PULLED — CLUSTER VERIFIED**

---

## Cluster Map

| VM | IP | RAM | vCPU | Dense | MoE | Vision |
|---|---|---|---|---|---|---|
| giantqueen-b | 10.0.0.16 | 12 GB* | 6 | qwen3:8b (5.2 GB) | granite3.1-moe:3b (2.0 GB) | qwen2.5vl:7b (6.0 GB) |
| dwarfqueen-b1 | 10.0.0.20 | 6 GB | 4 | phi4-mini:3.8b (2.5 GB) | granite3.1-moe:3b (2.0 GB) | gemma3:4b (3.3 GB) |
| dwarfqueen-b2 | 10.0.0.21 | 6 GB | 4 | phi4-mini:3.8b (2.5 GB) | granite3.1-moe:3b (2.0 GB) | gemma3:4b (3.3 GB) |
| worker-b1 | 10.0.0.22 | 4 GB | 2 | qwen3:1.7b (1.4 GB) | granite3.1-moe:1b (1.4 GB) | qwen3.5:0.8b (1.0 GB) |
| worker-b2 | 10.0.0.7 | 4 GB | 2 | qwen3:1.7b (1.4 GB) | granite3.1-moe:1b (1.4 GB) | qwen3.5:0.8b (1.0 GB) |
| worker-b3 | 10.0.0.6 | 4 GB | 2 | qwen3:1.7b (1.4 GB) | granite3.1-moe:1b (1.4 GB) | qwen3.5:0.8b (1.0 GB) |
| worker-b4 | 10.0.0.23 | 4 GB | 2 | qwen3:1.7b (1.4 GB) | granite3.1-moe:1b (1.4 GB) | qwen3.5:0.8b (1.0 GB) |

*giantqueen-b bumped from 8 to 12 GB because qwen2.5vl:7b needs 12.5 GiB for vision inference.

**Totals:** 7 VMs, 40 GB guest RAM, 22 vCPU, 21 models

## Host Resources (all 7 VMs running)

- RAM: 31 GB used / 62 GB total → **30 GB free**
- Disk: 178 GB used / 1.7 TB → **1.4 TB free**
- CPU: 22 vCPU allocated / 32 logical → 10 free

## How It Was Built

- **giantqueen-b:** Built via autoinstall (Ubuntu 24.04.4 Server, virt-install with CIDATA seed). This was the only VM built from scratch.
- **All other VMs:** Cloned from giantqueen-b's disk via `qcow2` copy + hostname/machine-id fix. Much faster and 100% reliable vs. the autoinstall which was inconsistent (~50% success rate on config application).
- **Models:** giantqueen-b's models removed on clones, correct tier models pulled via Ollama on each VM.

## Build Method: Clone Script

After discovering Ubuntu 24.04 autoinstall was unreliable (applied config on giantqueen-b but not on dwarfqueen-b1/b2), we switched to cloning:

1. Build ONE working VM via autoinstall (giantqueen-b)
2. Shut it down
3. For each remaining VM: copy qcow2, mount via qemu-nbd, change hostname + regenerate machine-id, define via virt-install --import
4. Boot, wait for SSH, swap/pull models

Total build time for 6 cloned VMs: ~15 minutes (vs. 30+ min each for autoinstall).

## Known Issues Fixed During Build

1. **Ubuntu 24.04 autoinstall ~5 min startup delay** — disk stays at ~12MB before install begins. Not stuck, just slow.
2. **`shutdown: poweroff` doesn't fire** — VM sits running after install. Fixed with `virsh shutdown` from host.
3. **`late-commands` silently skipped** — sudoers not created. Fixed with qemu-nbd mount post-install.
4. **Israeli apt mirror unreliable** — switched all VMs to `de.archive.ubuntu.com`.
5. **Autoinstall config not reliably applied** — ~50% of VMs got default config. Fixed by switching to clone approach.

## Verification

All 7 VMs verified on 2026-04-16:
- SSH access with phase3_ed25519 key ✅
- Correct hostname on each VM ✅
- Unique machine-id on each VM ✅
- Passwordless sudo for user nir ✅
- Ollama installed, bound to 0.0.0.0:11434 ✅
- Correct 3 models per tier ✅
- Ollama API responding from host via curl ✅
- 4 GB swap on each VM ✅

## What's Next

- [ ] STT provisioning (PHASE3_PROVISION_VM.sh) — ffmpeg, whisper.cpp, Moonshine, Pillow, etc.
- [ ] Helper scripts — slice_audio.py, slice_image.py, run_stt.py, run_reasoner.py, integrate_children.py
- [ ] Smoke tests — real audio through STT, real image through vision, text through reasoner
- [ ] Full hierarchy test — end-to-end RajaBee → GiantQueen → DwarfQueens → Workers

---

*Canonical. Edit in place. Git is the time machine.*

## Smoke Test Results — 2026-04-16

### Text Reasoners (Dense)
| VM | Model | Prompt | Answer | Status |
|---|---|---|---|---|
| giantqueen-b | qwen3:8b | Capital of France? | Paris | ✅ |
| dwarfqueen-b1 | phi4-mini:3.8b | Capital of France? | Paris | ✅ |
| worker-b1 | qwen3:1.7b | Capital of France? | Paris | ✅ |

### MoE Models
| VM | Model | Prompt | Answer | Status |
|---|---|---|---|---|
| giantqueen-b | granite3.1-moe:3b | Three primary colors? | Red, blue, yellow | ✅ |
| dwarfqueen-b1 | granite3.1-moe:3b | Three primary colors? | Red, blue, yellow | ✅ |
| worker-b1 | granite3.1-moe:1b | Three primary colors? | Red, blue, yellow | ✅ |

### Vision Models
Test image: white background, red rectangle, blue circle, "Hello Hive" text.
| VM | Model | Saw rectangle | Saw circle | Saw text | Status |
|---|---|---|---|---|---|
| giantqueen-b | qwen2.5vl:7b | ✅ | ✅ | ✅ | ✅ |
| dwarfqueen-b1 | gemma3:4b | ✅ | ✅ | ✅ | ✅ |
| worker-b1 | qwen3.5:0.8b | ✅ | ✅ | ✅ | ✅ |

### STT (whisper.cpp)
JFK inaugural address excerpt — all 7 VMs transcribed correctly. See PHASE3_STT_VERIFICATION_LOG.md.

### RAM Fix
giantqueen-b bumped from 8 GB to 12 GB — qwen2.5vl:7b needs 12.5 GiB for vision inference.
New host RAM usage: ~35 GB / 62 GB = ~27 GB free.
