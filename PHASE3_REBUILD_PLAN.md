# Phase 3 — Desktop Rebuild Plan (corrected sizing)

**Author:** Desktop Linux Claude (Opus 4.6)
**Date:** 2026-04-14 (evening, after first build failed disk sizing on Dense-round pull)
**Supersedes:** the sizing sections of `PHASE3_LINUX_VM_SETUP.md` and `PHASE3_DESKTOP_BUILD_FIELDNOTES.md`. The first build procedure (fresh autoinstalls from the seed at `/home/nir/vm/desktop-template/seed/`, on the `killerbee` libvirt pool at `/home/killerbee-images/`, via the `scripts/autoinstall_one.sh` + `scripts/full_cycle_one.sh` + `scripts/full_cycle_remaining6.sh` drivers) is unchanged and still correct. **Only the disk/RAM/vCPU numbers change.**
**Status:** PLAN. Not executed. Awaiting Nir review before any `virt-install` runs.
**Trigger for this plan:** `qwen3:14b` pull on `giantqueen-b` failed at 71% with `Error: write ...partial: no space left on device`. The 15 GiB VM root FS was at 100% usage — Ubuntu base ~5 GB + Ollama partial blob ~6.2 GB + the rest of the 9.3 GB download that would not fit. Root cause: the first build used a uniform 15 GiB disk inherited from the template, and the template was sized when the only visible host partition was the 92 GB root — not against the workload that each VM actually has to hold. This plan fixes that by starting from the workload.

---

## 0. Ground truth about the host and the workload

### 0.1 Host hardware (re-measured 2026-04-14 evening)

| Resource | Value |
|---|---|
| CPU | Intel Core i9-13900KF, 32 logical CPUs |
| RAM (physical) | 62 GiB usable (64 GB reported by BIOS minus small reserve) |
| Swap | 61 GiB (sufficient, but VM sizing should NOT rely on swap) |
| Big volume | `/dev/sda4` ext4 at `/home`, 1.7 TB total, **1.5 TB free** after cleanup |
| Root FS (not used for VMs) | `/dev/sda2` ext4 at `/`, 92 GB, ~46% used |
| Bridge | `br0`, 10.0.0.5/24 on the real LAN |
| libvirt pool | `killerbee` at `/home/killerbee-images`, active, autostart |

`nproc` = 32, `free -h` shows 62 GiB Mem total.

### 0.2 The workload — three models per VM, not rotated

Per `PHASE3_LINUX_VM_SETUP.md` §6, the KillerBee cluster runs **three independent test rounds** over the same 15 VMs: Dense, MoE (mixture of experts), and Multi-modal/Vision. The original §6 plan said *"between rounds, `ollama rm` the previous round's models and `ollama pull` the next round's models"* — i.e., rotate models between rounds so only one model lives on disk at a time.

**This plan changes that.** Nir's explicit instruction this evening: *"do a good job once instead of again and again."* That means **each VM holds all three models on disk at once**, so there is no re-pull between rounds, no wasted download bandwidth, no re-warming of page caches. The sizing math below is for all-three-models-resident at steady state, plus headroom for one download at a time.

If Nir wants to revert to rotating models to save disk, that is a simple override — smaller disks are fine. But the default below is all-three-resident.

Inference still loads one model at a time (Ollama does not pre-load them), so **RAM sizing is for the largest single model plus OS plus inference overhead**, not for the sum of all three.

### 0.3 Model catalogue — source of truth for sizes

The three models per VM are the ones Nir and Desktop Claude locked together in `PHASE3_LINUX_VM_SETUP.md` §6.5 (commits `d45369c`, `6d67e3e`, `5176ab7`, `f6fbf3d`, `3bf30ec`). For each model below, the on-disk size is the estimate from §6.5 (which Nir reviewed). These numbers are **estimates at q4_K_M** — the actual `ollama pull` will be within ±15% of these values. Any model that comes back more than 20% larger than the estimate during Step 3.8 execution is a halt-and-re-review condition.

| Model tag | On-disk (est. GB) | RAM loaded (est. GB) | Notes |
|---|---|---|---|
| `qwen3:14b` | 9.3 | 9.5 | Measured live from the failed giantqueen-b pull — 9.3 GB confirmed by Ollama's own progress bar at "9.3 GB" total. |
| `qwen3:8b` | 5.2 | 5.5 | Per §6.5 estimate ("~5 GB at q4"). |
| `phi4-mini:3.8b` | 2.5 | 2.7 | Per §6.5 estimate ("~2.5 GB at q4"). |
| `granite3.1-moe:3b` | 2.0 | 2.2 | Estimate from `params × 0.6 GB/B` rule with MoE overhead — to be verified on first pull. |
| `qwen3-vl:8b` | 5.0 | 5.3 | Per §6.5 ("~5 GB at q4", replaces qwen3-vl:9b which does not exist). |
| `llama3.2-vision:11b` | 7.8 | 8.0 | Per §6.5 estimate ("~7 GB at q4", bumped to 7.8 to be safe). |
| `gemma3:4b` | 2.5 | 2.7 | Per §6.5 estimate ("~2.5 GB at q4"). |

---

## 1. Per-VM sizing — one table per tier, with arithmetic shown

The general formula (Laptop brief §3.4.b):

```
disk = OS_base + sum(model_sizes) + download_scratch + log_tmp + rotation_headroom
```

- `OS_base` = 5 GB. Measured from the first giantqueen-b build: `df -h /` inside the VM showed 14/15 GB used with Ollama's 6.2 GB of partial blobs, so OS + packages + logs accounted for ~7.8 GB; 5 GB is a fair isolated OS footprint.
- `download_scratch` = `2 × largest_single_model_size` (partial blob + final file during rename; Ollama writes to a `.partial` file then renames). This is transient — only needed while the largest pull is running.
- `log_tmp` = 2 GB for journald, /tmp, systemd state.
- `rotation_headroom` = room to experiment, swap a model, try a bigger quant. Set per tier below.

### 1.1 giantqueen-b (GiantQueen-B)

| Component | GB |
|---|---|
| OS base | 5.0 |
| Dense model: `qwen3:14b` | 9.3 |
| MoE model: `granite3.1-moe:3b` | 2.0 |
| Vision model: `qwen3-vl:8b` | 5.0 |
| Sum models | 16.3 |
| Steady-state (OS + models + log_tmp) | 5 + 16.3 + 2 = **23.3** |
| Peak during largest pull (qwen3:14b) | (5 + 7.0 already-resident + 2×9.3 partial+final + 2 logs) = **32.6** |
| Rotation headroom (1× an extra 18-20 GB model for experiments, e.g. `gpt-oss:20b` or `gemma4:31b`-quant) | 20.0 |
| **Required** | max(32.6, 23.3+20) = **43.3** |
| **Chosen disk size** | **50 GB** (round up to a clean number, leaves ~7 GB untouched headroom) |

### 1.2 dwarfqueen-b1 and dwarfqueen-b2 (two identical DwarfQueens)

| Component | GB |
|---|---|
| OS base | 5.0 |
| Dense: `qwen3:8b` | 5.2 |
| MoE: `granite3.1-moe:3b` | 2.0 |
| Vision: `llama3.2-vision:11b` | 7.8 |
| Sum models | 15.0 |
| Steady-state | 5 + 15 + 2 = **22.0** |
| Peak during largest pull (llama3.2-vision:11b) | (5 + 7.2 + 2×7.8 + 2) = **29.8** |
| Rotation headroom (1× extra ~8 GB experimental model) | 8.0 |
| **Required** | max(29.8, 22+8) = **30.0** |
| **Chosen disk size** | **40 GB** (10 GB unused headroom) |

### 1.3 worker-b1, worker-b2, worker-b3, worker-b4 (four identical Workers)

| Component | GB |
|---|---|
| OS base | 5.0 |
| Dense: `phi4-mini:3.8b` | 2.5 |
| MoE: `granite3.1-moe:3b` | 2.0 |
| Vision: `gemma3:4b` | 2.5 |
| Sum models | 7.0 |
| Steady-state | 5 + 7 + 2 = **14.0** |
| Peak during largest pull (2.5 GB) | (5 + 4.5 + 2×2.5 + 2) = **16.5** |
| Rotation headroom (1× extra 4 GB experimental model) | 4.0 |
| **Required** | max(16.5, 14+4) = **18.0** |
| **Chosen disk size** | **25 GB** (7 GB unused headroom — small footprint, cheap to round generously) |

### 1.4 Disk totals

| VM | Disk (GB) |
|---|---|
| giantqueen-b | 50 |
| dwarfqueen-b1 | 40 |
| dwarfqueen-b2 | 40 |
| worker-b1 | 25 |
| worker-b2 | 25 |
| worker-b3 | 25 |
| worker-b4 | 25 |
| **Total virtual disk** | **230 GB** |
| **Big volume free** | 1500 GB |
| **Utilization** | 15% of `/home` |

Since qcow2 is sparse, the actual on-disk allocation starts at a few hundred MB per VM (the EFI stub + OS footprint) and grows up to the steady-state ~22-32 GB per VM as models get pulled. Even at peak, the total real allocation stays under 200 GB, which leaves over a terabyte free on `/home`.

---

## 2. RAM sizing

Formula (Laptop brief §3.4.c):

```
ram = OS_overhead + largest_single_model_in_memory + inference_overhead
```

- `OS_overhead` ≈ 1 GB for Ubuntu server + systemd + Ollama daemon idle.
- `largest_single_model_in_memory` = the largest of the three models at runtime (≈ on-disk size for q4_K_M).
- `inference_overhead` ≈ 1.5 GB for KV cache, context window, GGML activation buffers. Scales with context length — for 8K context this is conservative, for 32K+ context it may need more.

**Assumption:** Ollama loads one model at a time. If Nir later wants simultaneous multi-model serving, RAM must be recomputed. Flagging explicitly.

### 2.1 Per-VM RAM

| VM | Largest model | OS | Model | Inference | Sum | **Chosen RAM** |
|---|---|---|---|---|---|---|
| giantqueen-b | qwen3:14b (9.5) | 1.0 | 9.5 | 1.5 | 12.0 | **12 GB** |
| dwarfqueen-b1 | llama3.2-vision:11b (8.0) | 1.0 | 8.0 | 1.5 | 10.5 | **12 GB** (1.5 GB real headroom) |
| dwarfqueen-b2 | llama3.2-vision:11b (8.0) | 1.0 | 8.0 | 1.5 | 10.5 | **12 GB** |
| worker-b1..b4 | phi4-mini or gemma3 (2.7) | 1.0 | 2.7 | 1.5 | 5.2 | **6 GB** each |

### 2.2 RAM totals and host fit

```
GiantQueen-B    : 12
DwarfQueen-B1   : 12
DwarfQueen-B2   : 12
Worker-B1       :  6
Worker-B2       :  6
Worker-B3       :  6
Worker-B4       :  6
                --
Total guest RAM : 60 GB
```

Host has 62 GiB usable. `62 - 60 = 2 GB` for the Mint Cinnamon desktop + libvirt + any app Nir runs on the host while a test is in progress. **That is very tight.** If Nir is running anything else simultaneously (a browser, VS Code, WaggleDance ICQ terminal), the host may start swapping or OOM-killing. Two options:

- **Option R1 (tight, matches the Option C-quant target from the original plan):** 12/12/6 = 60 GB. As above. Works only if the host stays mostly idle during tests.
- **Option R2 (safer, trades Worker size):** 12/12/5 = 58 GB. Workers drop to 5 GB. phi4-mini (2.5 GB) + gemma3 (2.5 GB) + OS 1 + inference 1.5 still fits a 5 GB VM — barely. Worker RAM becomes the tightest part of the system.
- **Option R3 (comfortable, trades DwarfQueen size):** 12/10/6 = 56 GB. DwarfQueens drop to 10 GB. llama3.2-vision:11b at 7.8 GB loaded + OS 1 + inference ≤ 1.2 fits exactly, zero headroom; any inference-overhead spike OOMs. **Not recommended** — too close to the edge for the vision model.

**My recommendation:** **Option R1 (12/12/6)** — the one in the table — and ask Nir to keep the host idle (or at least do not keep a browser + VS Code + heavy apps open) during actual test runs. It matches the already-agreed Option C-quant RAM budget from §4 of the setup doc and gives every tier enough room to run its vision-round model without OOM.

If Nir wants more host headroom, pick R3 and accept that DwarfQueens cannot hold `llama3.2-vision:11b` comfortably (it will swap or OOM on inference). If he wants to keep DwarfQueens at 12 but reduce Workers, R2 is the shrink path.

---

## 3. vCPU sizing

Host has 32 logical CPUs (i9-13900KF: 8 P-cores × 2 threads + 16 E-cores × 1 thread = 32 logical).

CPU-only Ollama inference benefits from multiple threads up to a memory-bandwidth plateau. Rough rule: the plateau for llama.cpp-style inference on DDR5 is around 6-8 threads per model, beyond which adding threads hits memory-bandwidth saturation and stops helping.

### 3.1 Per-VM vCPU

| VM | Model max params | Threads helpful | **Chosen vCPU** | Rationale |
|---|---|---|---|---|
| giantqueen-b | 14B (qwen3:14b) | 6-8 | **6** | Big dense model benefits most from cores, but we do not want to crowd out the DwarfQueens during joint runs. |
| dwarfqueen-b1 | 11B (llama3.2-vision:11b) | 4-6 | **4** | Mid-sized model, 4 threads is close to the plateau. |
| dwarfqueen-b2 | 11B | 4-6 | **4** | Same. |
| worker-b1..b4 | ~4B | 2-3 | **2** each | Small models saturate at 2-3 threads; 2 is enough. |

### 3.2 vCPU totals and host fit

```
GQ-B         : 6
2× DQ-B      : 8
4× W-B       : 8
              --
Total vCPU   : 22 (of 32 logical host CPUs = 69% allocation)
Overcommit   : 0 (no overcommit)
```

Leaves 10 logical CPUs for the host, libvirt overhead, and any other workload on the host (Mint desktop, browser, ICQ, Claude Code sessions). Comfortable. No overcommit, no vCPU contention on the scheduler.

If KillerBee tests later reveal that inference is actually bottlenecked on vCPU count (unlikely — memory bandwidth hits first), we can raise `giantqueen-b` to 8 vCPU with `virsh setvcpus --config` on the offline VM. Current plan is conservative-comfortable.

---

## 4. Tier mapping — what each VM does, and why it gets those models

| VM | Tier | What it does | Why these models |
|---|---|---|---|
| `giantqueen-b` | GiantQueen-B | The single highest-capacity node on the Desktop host. In the KillerBee hive it orchestrates DwarfQueens directly and escalates to RajaBee (on Laptop, post-OS-swap) for very hard queries. Biggest model, highest RAM, most vCPU on the Desktop side. | Dense: `qwen3:14b` (flagship dense at 12 GB tier). MoE: `granite3.1-moe:3b` (only small MoE available that fits, per §6.7 of setup doc). Vision: `qwen3-vl:8b` (largest qwen-VL that fits the 12 GB RAM tier, per §6.5). |
| `dwarfqueen-b1`, `dwarfqueen-b2` | DwarfQueen-B1/B2 | Mid-tier coordinators. Each DwarfQueen aggregates Worker outputs and either answers or escalates to its parent GiantQueen. DwarfQueens run bigger-than-Worker models so their consensus has real weight. | Dense: `qwen3:8b` (best-in-class dense at 8 GB tier). MoE: `granite3.1-moe:3b` (same small MoE as everyone, ecosystem is thin). Vision: `llama3.2-vision:11b` (Meta's production-tested 11B vision model, largest that fits the new 12 GB RAM tier). |
| `worker-b1`, `worker-b2`, `worker-b3`, `worker-b4` | Worker-B1..B4 | Leaf-level workers, 4 of the 8 total Worker-tier slots across the whole KillerBee cluster. Each worker answers fast/narrow queries and votes into DwarfQueen consensus. Small, fast, cheap. | Dense: `phi4-mini:3.8b` (highest quality sub-4B dense model per §6.8). MoE: `granite3.1-moe:3b` (only small MoE). Vision: `gemma3:4b` (Google native multimodal, only tiny VLM with strong image grounding). |

---

## 5. Summary table and fit check

| VM | Tier | Disk (GB) | RAM (GB) | vCPU | Dense | MoE | Vision |
|---|---|---|---|---|---|---|---|
| giantqueen-b | GiantQueen-B | **50** | **12** | **6** | qwen3:14b | granite3.1-moe:3b | qwen3-vl:8b |
| dwarfqueen-b1 | DwarfQueen-B1 | **40** | **12** | **4** | qwen3:8b | granite3.1-moe:3b | llama3.2-vision:11b |
| dwarfqueen-b2 | DwarfQueen-B2 | **40** | **12** | **4** | qwen3:8b | granite3.1-moe:3b | llama3.2-vision:11b |
| worker-b1 | Worker-B1 | **25** | **6** | **2** | phi4-mini:3.8b | granite3.1-moe:3b | gemma3:4b |
| worker-b2 | Worker-B2 | **25** | **6** | **2** | phi4-mini:3.8b | granite3.1-moe:3b | gemma3:4b |
| worker-b3 | Worker-B3 | **25** | **6** | **2** | phi4-mini:3.8b | granite3.1-moe:3b | gemma3:4b |
| worker-b4 | Worker-B4 | **25** | **6** | **2** | phi4-mini:3.8b | granite3.1-moe:3b | gemma3:4b |
| **Totals** | | **230 GB** | **60 GB** | **22** | | | |

### Fit check

| Resource | Allocated | Host has | Remaining | Verdict |
|---|---|---|---|---|
| Disk (virtual, `/home`) | 230 GB | 1500 GB | 1270 GB | Plenty. qcow2 is sparse, real use will be ~150 GB once all 21 models pulled. |
| RAM | 60 GB | 62 GiB | 2 GB | **Tight.** Host will be at ~97% memory allocation while all 7 VMs are running. Acceptable only if Nir keeps the host otherwise idle. See §2.2 Options R1/R2/R3 for alternatives. |
| vCPU | 22 | 32 logical | 10 | Comfortable. No overcommit. |

---

## 6. Execution plan (for reference — not to be executed until Nir green-lights this file)

When Nir says go, Desktop Claude will:

1. Run `scripts/autoinstall_one.sh giantqueen-b 12288` with `size=50` in the first `--disk` flag.
2. After autoinstall, run `scripts/full_cycle_one.sh`-style post-install (Ollama install + bind to 0.0.0.0:11434 + verify) — the existing script can be re-used as-is because post-install is unchanged.
3. Pull all three models into giantqueen-b: `ollama pull qwen3:14b && ollama pull granite3.1-moe:3b && ollama pull qwen3-vl:8b`. Verify each with `ollama list`.
4. Only after giantqueen-b is fully green, move to dwarfqueen-b1 with `size=40`, RAM 12288, vCPU 4. Repeat steps 1-3 with its three models.
5. Repeat for dwarfqueen-b2.
6. Repeat for each of the 4 workers with `size=25`, RAM 6144, vCPU 2.
7. Final verification: `curl http://<ip>:11434/api/tags` from the host for each VM, parse JSON, confirm each has exactly its three models with non-zero sizes.
8. Telegraph ICQ pointer to Laptop: `"Rebuild done per plan, 7 VMs up, 21 models pulled. File: KillerBee/PHASE3_REBUILD_STATUS.md commit <hash>."`

The scripts need a small parameterization change: `autoinstall_one.sh` currently hard-codes `size=15` inside the `--disk` flag. A new argument `<disk-GB>` will be added, passed through to the virt-install line. Same for `full_cycle_one.sh`. The driver loop for the 6 remaining VMs will become a name/ram/vcpu/disk quadruple per VM instead of a name/ram pair.

Estimated total wall-clock for the rebuild:

- 7 × ~4 min autoinstall = 28 min
- 7 × ~1 min Ollama install + config + verify = 7 min
- 21 model pulls = variable, but rough math: 21 × ~45 s per GB at 100 MB/s and an average model size of ~5 GB = 80 min
- Total: **~2 hours wall clock** for a clean rebuild from now to all-21-models-verified.

If any single model pull fails, halt that VM, note the incident in a file, ICQ the pointer, and wait for direction.

---

## 7. Foreseeable failure modes (per Laptop brief §3.4.g)

### 7.1 A model is larger at the actual registry than the §6.5 estimate

The seven size estimates in §0.3 came from the earlier §6.5 planning doc and are not fresh `curl registry.ollama.ai` measurements. If any model turns out to be more than 20% larger than estimated, the peak-during-pull numbers in §1 may overflow the chosen disk size. **Mitigation:** before pulling any model during Step 3.8, run `ollama show <model>` inside the target VM first — it reports the declared size. If it does not match the plan within 20%, halt and re-review this plan.

### 7.2 A model tag is deprecated or renamed

`qwen3-vl:8b` and `granite3.1-moe:3b` are the two tags I am least sure exist exactly as written. §6.5 itself notes that `qwen3-vl:9b` does not exist and the 8b was picked as the closest available. If during pull Ollama returns "model not found", **halt** that VM's pull, ICQ the incident as a one-line pointer to a new incident file, and wait. Do not substitute silently.

### 7.3 Ollama registry is slow or down

During the first build I saw ~100 MB/s on the giantqueen-b pull. If the registry slows to <20 MB/s, the 21 pulls will take hours instead of ~80 minutes and virt-install's `--wait -1` on the post-install phase will time out some SSH retries. **Mitigation:** each pull is its own step, and the post-install scripts already split autoinstall → boot → ssh → ollama install → bind → verify, so a slow pull only delays that VM, not the others. The pulls are sequential per-VM, so no contention.

### 7.4 DwarfQueen runs llama3.2-vision:11b tighter than expected

12 GB RAM with a 7.8 GB model + OS + inference overhead + 8K context is a good theoretical fit, but vision models often have bigger activation buffers than pure-text models of the same parameter count because they carry image token embeddings alongside text tokens. **Mitigation:** if the DwarfQueens OOM on first vision-round inference, drop to an 8K context window explicitly via Ollama model parameters, or bump RAM to 14 GB (which requires `virsh setmem --config` while the VM is off and re-checking total-host RAM fit).

### 7.5 Host RAM tightness trips over a stray process

At 60 GB guest + 2 GB host, any host process that grabs 3+ GB (a Chromium tab with many subframes, a VS Code workspace loading typescript, a WaggleDance ICQ auto-type Python process that leaks memory) will push the host into swap or OOM-kill something. **Mitigation:** Nir is explicitly warned in §2.2 that the RAM budget assumes the host stays mostly idle during tests. If a swap spiral starts, `virsh suspend worker-b4` to free ~6 GB of guest RAM instantly, then investigate.

---

## 8. Concerns / disagreements with the brief (per Laptop rule 4.4)

None substantive. Two small notes the reviewer may want to adjust:

1. **Rotation vs all-three-resident.** The brief says "plan for all three models resident." The older `PHASE3_LINUX_VM_SETUP.md` §6 said rotate. I picked all-three-resident per the newer instruction, but if Nir prefers rotate (to save disk and allow quickly trying a larger-tier model in some slot), all the disk numbers in §1 can drop by roughly 2/3 because only one model lives on disk at a time. Easy to revise.

2. **DwarfQueen RAM bump from 8 → 12.** This plan raises the DwarfQueen RAM from the original §4 Option C-quant allocation of 8 GB to 12 GB, because 8 GB does not fit `llama3.2-vision:11b` + OS. This pushes the total guest RAM commit from 44 GB (old) to 60 GB (new). The host can do it but it is tight. If Nir wants to stay at 44 GB total host allocation, we need a smaller vision model on DwarfQueens — e.g. `qwen3-vl:8b` (5 GB) in place of `llama3.2-vision:11b`, which would let DQ stay at 8 GB RAM. That is a model-choice change, not a sizing change, and it needs Nir's explicit call.

Both points are flagged so Nir can correct them before execution.

---

## 9. Waiting state

This plan is committed and pushed. No VMs are being rebuilt. The 7 old VMs are destroyed and their qcow2 files are gone. The `desktop-template.qcow2`, the autoinstall seed, the `killerbee` libvirt pool, the `br0` bridge, and the build scripts are all untouched and ready to be re-used.

Desktop Claude is now **waiting** for Nir to either:

- Approve this plan as-is → Desktop Claude executes Step 3.8 of the Laptop brief (rebuild + model pulls).
- Request changes → Nir writes the changes (ideally inline-edit this file or reply in a comment/ICQ pointer to a change file) → Desktop Claude applies changes → re-pushes → re-signals → waits again.
- Kill the plan → Desktop Claude stops.

— Desktop Linux Claude, 2026-04-14 evening
