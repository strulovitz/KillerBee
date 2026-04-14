# Phase 3 Rebuild Plan V2 — Downshifted sizing

**Author:** Desktop Linux Claude (Opus 4.6)
**Date:** 2026-04-14 (late evening)
**Status:** PLAN. Not executed. Awaiting Nir review before any `virt-install` runs.
**Supersedes:** `PHASE3_REBUILD_PLAN.md` (commit `3e8fbf9`, the V1 plan). V1 is retained as historical record per the iteration-history rule.
**Trigger for V2:** V1 plan failed the host-fit check after the QEMU envelope tax and Cinnamon/libvirtd/ICQ overhead were honestly accounted for — V1 left only 0–2 GB host headroom. Nir owned the framing error in his apology (in `claude-memory/KILLERBEE_DOWNGRADE_2026-04-14.md`) and asked for everyone to drop one notch, with Workers moving to a brand-new TINY tier researched together on Google this evening.
**Tier selections:** locked in `KillerBee/PHASE3_V2_TIER_PICKS.md` (commit `2b1ef22` plus this commit's update).
**Build procedure:** unchanged from V1. Same autoinstall seed, same `killerbee` libvirt pool on `/home/killerbee-images`, same `br0` bridge, same three build scripts (`scripts/autoinstall_one.sh`, `scripts/full_cycle_one.sh`, `scripts/full_cycle_remaining6.sh`) with only the per-VM disk/RAM/vCPU parameters changing.

---

## 0. Ground truth (unchanged from V1 §0, re-asserted for completeness)

| Resource | Value |
|---|---|
| CPU | Intel Core i9-13900KF, 32 logical CPUs |
| RAM (physical) | 62 GiB usable |
| Big volume | `/dev/sda4` ext4 at `/home`, 1.7 TB total, **1.5 TB free** |
| libvirt pool | `killerbee` at `/home/killerbee-images`, active, autostart |
| Bridge | `br0`, host IP 10.0.0.5/24 |
| SSH key | `/home/nir/.ssh/phase3_ed25519` |
| Autoinstall seed | `/home/nir/vm/desktop-template/seed/{user-data,meta-data}` |
| Install ISO | `/home/killerbee-images/isos/ubuntu-24.04.4-live-server-amd64.iso` |
| Current VM state | **0 production VMs.** The 7 V1 VMs were destroyed before this plan was drafted (per the downgrade brief Step 3.3). `desktop-template` shut off remains. |

---

## 1. Model catalogue and tier assignment (the core change from V1)

Per the one-notch downshift from the apology:

| VM | Tier after shift | Dense | MoE | Vision |
|---|---|---|---|---|
| giantqueen-b | was GiantQueen, now DwarfQueen-class | `qwen3:8b` (5.2 GB) | `granite3.1-moe:3b` (2.0 GB) | `llama3.2-vision:11b` (7.8 GB) |
| dwarfqueen-b1 | was DwarfQueen, now Worker-class | `phi4-mini:3.8b` (2.5 GB) | `granite3.1-moe:3b` (2.0 GB) | `gemma3:4b` (2.5 GB) |
| dwarfqueen-b2 | was DwarfQueen, now Worker-class | `phi4-mini:3.8b` (2.5 GB) | `granite3.1-moe:3b` (2.0 GB) | `gemma3:4b` (2.5 GB) |
| worker-b1 | was Worker, now TINY | `qwen3:1.7b` (1.1 GB) | `granite3.1-moe:1b` (0.7 GB) | `qwen3.5:0.8b` (0.6 GB) |
| worker-b2 | was Worker, now TINY | `qwen3:1.7b` | `granite3.1-moe:1b` | `qwen3.5:0.8b` |
| worker-b3 | was Worker, now TINY | `qwen3:1.7b` | `granite3.1-moe:1b` | `qwen3.5:0.8b` |
| worker-b4 | was Worker, now TINY | `qwen3:1.7b` | `granite3.1-moe:1b` | `qwen3.5:0.8b` |

All seven VMs hold **all three models on disk simultaneously** (no `ollama rm` between rounds). This matches Nir's explicit "do a good job once instead of again and again" direction.

All size estimates carry a ±20% verification halt-condition: at first pull, `ollama show <model>` must report a size within 20% of the estimate above. Anything more than 20% larger halts that VM and triggers a plan review, not a silent retry.

---

## 2. Per-VM disk sizing

Formula (unchanged from V1 §1):

```
disk = OS_base + sum(model_sizes) + download_scratch + log_tmp + rotation_headroom
```

- `OS_base` = 5 GB (measured from the first V1 build).
- `download_scratch` = `2 × largest_model` (Ollama partial file + final rename).
- `log_tmp` = 2 GB for journald / /tmp / systemd state.
- `rotation_headroom` = 1× extra model at the current tier's max size, for experiments and swap-outs.

### 2.1 giantqueen-b

| Component | GB |
|---|---|
| OS base | 5.0 |
| Dense `qwen3:8b` | 5.2 |
| MoE `granite3.1-moe:3b` | 2.0 |
| Vision `llama3.2-vision:11b` | 7.8 |
| Sum models | 15.0 |
| Steady-state (OS + models + log_tmp) | 5 + 15 + 2 = **22.0** |
| Peak during largest pull (llama3.2-vision:11b, 7.8 GB) | 5 + (5.2 + 2) + 2×7.8 + 2 = **29.8** |
| Rotation headroom | 8.0 |
| **Required** | max(29.8, 22 + 8) = **30.0** |
| **Chosen disk size** | **40 GB** |

### 2.2 dwarfqueen-b1, dwarfqueen-b2

| Component | GB |
|---|---|
| OS base | 5.0 |
| Dense `phi4-mini:3.8b` | 2.5 |
| MoE `granite3.1-moe:3b` | 2.0 |
| Vision `gemma3:4b` | 2.5 |
| Sum models | 7.0 |
| Steady-state | 5 + 7 + 2 = **14.0** |
| Peak during largest pull (2.5 GB) | 5 + 4.5 + 2×2.5 + 2 = **16.5** |
| Rotation headroom | 4.0 |
| **Required** | max(16.5, 14 + 4) = **18.0** |
| **Chosen disk size** | **25 GB** |

### 2.3 worker-b1, worker-b2, worker-b3, worker-b4

| Component | GB |
|---|---|
| OS base | 5.0 |
| Dense `qwen3:1.7b` | 1.1 |
| MoE `granite3.1-moe:1b` | 0.7 |
| Vision `qwen3.5:0.8b` | 0.6 |
| Sum models | 2.4 |
| Steady-state | 5 + 2.4 + 2 = **9.4** |
| Peak during largest pull (1.1 GB) | 5 + 1.3 + 2×1.1 + 2 = **10.5** |
| Rotation headroom | 5.0 |
| **Required** | max(10.5, 9.4 + 5) = **14.4** |
| **Chosen disk size** | **20 GB** (rounded up from 15 GB to give one full extra TINY model of headroom and because 15 GB proved too tight in V1) |

### 2.4 Disk totals

| VM | Disk (GB) |
|---|---|
| giantqueen-b | 40 |
| dwarfqueen-b1 | 25 |
| dwarfqueen-b2 | 25 |
| worker-b1 | 20 |
| worker-b2 | 20 |
| worker-b3 | 20 |
| worker-b4 | 20 |
| **Total virtual disk** | **170 GB** |
| **Big volume free** | 1500 GB |
| **Utilization** | ~11% of `/home` |

qcow2 files are sparse; real on-disk allocation will grow toward the steady-state ~15–22 GB per VM as models are pulled.

---

## 3. Per-VM RAM sizing

Formula (unchanged from V1 §2):

```
ram = OS_overhead + largest_single_model_in_memory + inference_overhead
```

### 3.1 Per-VM RAM

| VM | Largest model in memory | OS | Model | Inference | Sum | **Chosen RAM** |
|---|---|---|---|---|---|---|
| giantqueen-b | `llama3.2-vision:11b` (~8.0) | 1.0 | 8.0 | 1.5 | 10.5 | **11 GB** |
| dwarfqueen-b1 | `phi4-mini:3.8b` or `gemma3:4b` (~2.7) | 1.0 | 2.7 | 1.5 | 5.2 | **6 GB** |
| dwarfqueen-b2 | same as b1 | 1.0 | 2.7 | 1.5 | 5.2 | **6 GB** |
| worker-b1..b4 | `qwen3:1.7b` (~1.3) | 1.0 | 1.3 | 1.0 | 3.3 | **4 GB** each |

### 3.2 RAM totals and honest host-fit check

```
GiantQueen-B       : 11
DwarfQueen-B1      :  6
DwarfQueen-B2      :  6
Worker-B1          :  4
Worker-B2          :  4
Worker-B3          :  4
Worker-B4          :  4
                  ---
Total guest RAM    : 39 GB
```

**Host commit accounting (required per downgrade brief §5):**

| Bucket | GiB |
|---|---|
| Physical usable RAM | 62.0 |
| Guest RAM allocation | 39.0 |
| QEMU process envelope tax (7 VMs × ~300 MB for qemu overhead, virtio queues, device models, memfd backing structures) | 2.1 |
| Cinnamon desktop + systemd + libvirtd + ICQ agent + host ollama daemon idle + buff/cache floor | 2.0 |
| **Expected peak host commit** | **43.1** |
| **Remaining host headroom** | **18.9** |

**Headroom target from the downgrade brief:** 5–8 GiB free. **Achieved:** ~19 GiB free. **PASS with comfortable margin.**

That remaining 19 GiB covers: Claude Code sessions on the host, a browser with a few tabs, a text editor, any in-progress build compilation, the WaggleDance ICQ agent terminal, and general Mint Cinnamon animations. Nir can work on the host during tests without fear of the VMs OOMing.

---

## 4. Per-VM vCPU sizing

Host has 32 logical CPUs. Sizing unchanged from V1 (which passed vCPU fit cleanly even at the larger tier):

| VM | vCPU | Rationale |
|---|---|---|
| giantqueen-b | 6 | Largest dense + largest vision model; benefits most from more threads up to memory-bandwidth plateau. |
| dwarfqueen-b1 | 4 | Mid-sized phi4-mini / gemma3 / granite; 4 threads near plateau for 3–4B models. |
| dwarfqueen-b2 | 4 | Same. |
| worker-b1..b4 | 2 | Sub-2B models saturate at 2 threads on CPU. |

Total: 6 + 8 + 8 = **22 vCPU on 32 logical** (69% allocation, no overcommit). 10 logical CPUs remain for the host + libvirt overhead + any host workload.

---

## 5. Summary table (the single page Nir reads)

| VM | Tier | Disk (GB) | RAM (GB) | vCPU | Dense | MoE | Vision |
|---|---|---|---|---|---|---|---|
| giantqueen-b | old-DQ | **40** | **11** | **6** | `qwen3:8b` | `granite3.1-moe:3b` | `llama3.2-vision:11b` |
| dwarfqueen-b1 | old-Worker | **25** | **6** | **4** | `phi4-mini:3.8b` | `granite3.1-moe:3b` | `gemma3:4b` |
| dwarfqueen-b2 | old-Worker | **25** | **6** | **4** | `phi4-mini:3.8b` | `granite3.1-moe:3b` | `gemma3:4b` |
| worker-b1 | NEW TINY | **20** | **4** | **2** | `qwen3:1.7b` | `granite3.1-moe:1b` | `qwen3.5:0.8b` |
| worker-b2 | NEW TINY | **20** | **4** | **2** | `qwen3:1.7b` | `granite3.1-moe:1b` | `qwen3.5:0.8b` |
| worker-b3 | NEW TINY | **20** | **4** | **2** | `qwen3:1.7b` | `granite3.1-moe:1b` | `qwen3.5:0.8b` |
| worker-b4 | NEW TINY | **20** | **4** | **2** | `qwen3:1.7b` | `granite3.1-moe:1b` | `qwen3.5:0.8b` |
| **Totals** |   | **170 GB** | **39 GB** | **22** |   |   |   |

### Fit check

| Resource | Allocated | Host has | Remaining | Verdict |
|---|---|---|---|---|
| Disk (virtual, `/home`) | 170 GB | 1500 GB free | 1330 GB | Plenty. Real sparse use will be ~100 GB once all 21 models pulled. |
| RAM (including QEMU tax + host overhead) | 43.1 GB | 62 GiB | 18.9 GB | **PASS** — meets 5–8 GB headroom target with ~2.5× margin. |
| vCPU | 22 | 32 | 10 | Plenty, no overcommit. |

---

## 6. Explicit acknowledgements (per downgrade brief §5 bullets)

- **MoE round status:** **ALIVE.** `granite3.1-moe:1b` (Workers) and `granite3.1-moe:3b` (DwarfQueens + GiantQueen-B) both exist on Ollama as of 2026-04-14. Full seven-VM coverage.
- **Vision round status:** **ALIVE.** All seven VMs get a real multi-modal model (`qwen3.5:0.8b` for Workers, `gemma3:4b` for DwarfQueens, `llama3.2-vision:11b` for GiantQueen-B).
- **Acknowledgement that V2 is SLOWER and DUMBER than V1.** Yes, it is. The V1 plan had `qwen3:14b` on GiantQueen and `qwen3:8b` on DwarfQueens. V2 drops those to `qwen3:8b` and `phi4-mini:3.8b`. Token generation on these smaller models will be faster (fewer weights to read per token), but the reasoning quality per token will be meaningfully lower. Nir explicitly accepted that trade in his apology: *"we need to be realistic, to downgrade everything ... I asked an impossible request, you gave me an impossible solution."* The goal of Phase 3 is to watch the KillerBee hive-consensus architecture WORK, not to win a benchmark — dumber models will still exhibit the aggregation / escalation / consensus behavior the test is about.
- **RAM budget leaves 19 GB host headroom**, not 0–2 GB like V1 did. Honest accounting for QEMU envelope tax + Cinnamon + libvirtd + ICQ.
- **MINI tier was considered and rejected** for the "one-notch" interpretation because Nir wrote "like in the apology" and the apology's §3 table is a strict two-step mapping (GQ→DQ, DQ→Worker, Worker→TINY), not a three-step mapping. If Nir later decides MINI should exist as an intermediate rung, that is a different plan and a different commit.

---

## 7. Execution plan (when Nir green-lights this file)

Script parameterization change: the existing `scripts/autoinstall_one.sh` hard-codes `size=15` inside the `--disk` flag. Before execution, the script will be updated to accept a `<disk-GB>` third argument and interpolate it into the `--disk` flag. Same for `scripts/full_cycle_one.sh`. The driver will become a loop over `(name, ram-MB, disk-GB, vcpu)` quadruples.

Execution sequence (one VM at a time, no parallelism):

1. `full_cycle_one.sh giantqueen-b 11264 40 6`
2. `ollama pull qwen3:8b && ollama pull granite3.1-moe:3b && ollama pull llama3.2-vision:11b` on giantqueen-b
3. Verify with `ollama list` and from the host with `curl http://<ip>:11434/api/tags`
4. `full_cycle_one.sh dwarfqueen-b1 6144 25 4`, pull its three models, verify
5. `full_cycle_one.sh dwarfqueen-b2 6144 25 4`, pull its three models, verify
6. `full_cycle_one.sh worker-b1 4096 20 2`, pull its three models, verify
7. `full_cycle_one.sh worker-b2 4096 20 2`, same
8. `full_cycle_one.sh worker-b3 4096 20 2`, same
9. `full_cycle_one.sh worker-b4 4096 20 2`, same
10. Full cluster verification (SSH each VM, `hostname && cat /etc/machine-id && ollama list`; from host `curl /api/tags` on each).
11. Telegraph ICQ to Laptop: `"V2 rebuild complete, 7 VMs up, 21 models pulled, host headroom X GB. File: KillerBee/PHASE3_REBUILD_STATUS_V2.md commit <hash>."`

Estimated total wall clock: **~2 hours**.
- 7 × ~4 min autoinstall = 28 min
- 7 × ~1 min post-install = 7 min
- 21 model pulls, total ~45 GB at ~80 MB/s avg = ~10 min transfer plus processing ≈ **45 min**
- Sanity checks + logging = 10 min

---

## 8. Foreseeable failure modes

1. **`granite3.1-moe:1b` does not exist or was renamed.** IBM's `granite3.1-moe` tags are `:1b` and `:3b` per the V1 §6.7 search, but the naming conventions around `granite3` vs `granite3.1` vs `granite4` have shifted multiple times and Ollama occasionally re-tags. Mitigation: before pulling, `ollama show granite3.1-moe:1b` — if the tag is not found, fall back to `granite3.1-moe:3b` on Workers (upper TINY edge, still fits 4 GB RAM), and flag the incident in a file.
2. **`qwen3.5:0.8b` vision inference OOMs at 4 GB.** The multi-modal variant carries a vision encoder that can spike memory during image token preprocessing. If a Worker OOMs on first image inference, bump that Worker's RAM to 5 GB via `virsh setmem --config` (requires VM offline) — the RAM budget in §3.2 has enough headroom to absorb 4× bump by 1 GB = 4 GB extra, which still leaves ~15 GB host headroom.
3. **`llama3.2-vision:11b` loaded memory is larger than the 8 GB estimate.** Vision models have larger activation buffers than the rule-of-thumb for text-only predicts. If GiantQueen-B OOMs on vision inference, bump to 12 or 13 GB RAM and re-check host fit (still fits with ~17 GB headroom).
4. **Worker TINY multi-modal round is useless because the models are too small to distinguish cat from dog.** Sub-1B vision models are an ongoing research frontier, not a proven production capability. If the KillerBee vision round on Workers produces gibberish or refuses images, drop the Worker-tier vision round and let DwarfQueens handle all vision — document the failure in `EXPERIMENT_LOG.md` and continue.
5. **Total disk allocation jumps past 170 GB because ±20% on 15 GB of models gives +3 GB, and repeated rotation tests fill `/tmp` and systemd-journald.** Low risk — `/home` has 1.5 TB. If it ever gets tight, the headroom slice in each VM's disk sizing is the first place to shrink (drop rotation_headroom from 8 GB → 4 GB on GiantQueen, from 4 GB → 2 GB on DwarfQueens, from 5 GB → 2 GB on Workers).

---

## 9. Concerns / disagreements with the brief (per Laptop rule 4.4)

None. The downgrade brief explicitly asked for:

- Shift every tier one notch down → done, per the apology's §3 table (strict one-step map).
- TINY tier for Workers → done, `qwen3:1.7b` / `granite3.1-moe:1b` / `qwen3.5:0.8b` from this evening's Google session.
- Honest host-fit math with QEMU tax + overhead → done, §3.2 shows 19 GB headroom.
- 5–8 GB minimum host headroom → exceeded (19 GB).
- Explicit MoE and Vision round status lines → done in §6.
- Explicit acknowledgement that V2 is slower/dumber than V1 → done in §6.
- Telegraph-style ICQ only → will do when this plan is signaled.

One small observation: this plan preserves the `llama3.2-vision:11b` choice for GiantQueen-B despite the model being on the edge of what the 11 GB RAM allocation can hold. If Nir prefers a larger safety margin, the fallback is to swap GiantQueen-B vision to `qwen3-vl:8b` (~5 GB loaded, RAM drops to 8 GB, host headroom jumps to ~22 GB). That is a Nir call — both are honest, neither is strictly wrong. Default in this plan is llama3.2-vision:11b because it matches the "take old-DwarfQueen's model" rule from the apology.

---

## 10. Waiting state

This plan is committed and pushed. No VMs are being rebuilt. The 7 V1 VMs are destroyed and gone. The autoinstall seed, `killerbee` pool, `br0` bridge, build scripts, and template are all untouched and ready for V2 execution.

Desktop Claude is now waiting for Nir to either approve this plan, request inline changes, or kill it.

— Desktop Linux Claude, 2026-04-14 late evening
