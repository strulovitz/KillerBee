# Phase 3 Rebuild Plan — KillerBee Hive on Linux Mint Desktop

**Canonical rebuild plan for the 7-VM KillerBee hive.** Edit in place when things change. No version suffixes. No SUPERSEDED banners. Git history is the time machine.

**Status:** PLAN. Not executed. Awaiting Nir approval before any `virt-install` runs. Current VM state: **0 production VMs** — the earlier build's 7 VMs were destroyed.

**Depends on:** `PHASE3_LINUX_VM_SETUP.md` (initial host setup — libvirt `killerbee` pool, `br0` bridge, autoinstall seed, SSH key pair, install ISO). That file is the one-time host infrastructure setup and is still valid; this rebuild plan assumes it has already been done.

**Companion plan:** `PHASE3_STT_PLAN.md` (the STT + multimedia tooling layer that bolts onto the same 7 VMs). Both plans together make up the full V4 experiment when Nir approves them and authorizes the rebuild.

---

## 0. Ground truth (host and infrastructure)

| Resource | Value |
|---|---|
| CPU | Intel Core i9-13900KF, 32 logical CPUs |
| RAM (physical) | 62 GiB usable |
| Big volume | `/dev/sda4` ext4 at `/home`, 1.7 TB total, **1.5 TB free** |
| libvirt pool | `killerbee` at `/home/killerbee-images`, active, autostart |
| Bridge | `br0`, host IP 10.0.0.5/24 on the real LAN |
| SSH key | `/home/nir/.ssh/phase3_ed25519` |
| Autoinstall seed | `/home/nir/vm/desktop-template/seed/{user-data,meta-data}` |
| Install ISO | `/home/killerbee-images/isos/ubuntu-24.04.4-live-server-amd64.iso` |
| Build scripts (in this repo) | `scripts/autoinstall_one.sh`, `scripts/full_cycle_one.sh`, `scripts/full_cycle_remaining6.sh` |
| Current VM state | **0 production VMs.** `desktop-template` shut off remains. |

**Doubling rule:** every per-VM disk size computed in §2 is **doubled** in the final plan per Nir's explicit instruction. The §2 arithmetic produces the absolute floor (minimum disk the workload demands); `virt-install` is called with 2× that floor. Disk is cheap, margin is not.

**Workload model:** each VM holds **all three models on disk simultaneously** (Dense + MoE + Vision). No `ollama rm` between rounds, no rotation. Nir's explicit direction: *"do a good job once instead of again and again."* Inference still loads one model at a time into RAM (Ollama lazy-loads), so RAM sizing is for the largest single resident model plus overhead, not the sum.

---

## 1. Model catalogue and tier assignment

After the "one-notch downshift" from the downgrade brief (see `claude-memory/KILLERBEE_DOWNGRADE_2026-04-14.md` for the full historical reasoning), the 7 VMs collapse into three tiers:

| VM | Tier | Dense | MoE | Vision |
|---|---|---|---|---|
| giantqueen-b | old-DwarfQueen class | `qwen3:8b` (5.2 GB) | `granite3.1-moe:3b` (2.0 GB) | `qwen2.5vl:7b` (4.2 GB) |
| dwarfqueen-b1 | old-Worker class | `phi4-mini:3.8b` (2.5 GB) | `granite3.1-moe:3b` (2.0 GB) | `gemma3:4b` (2.5 GB) |
| dwarfqueen-b2 | old-Worker class | `phi4-mini:3.8b` (2.5 GB) | `granite3.1-moe:3b` (2.0 GB) | `gemma3:4b` (2.5 GB) |
| worker-b1 | TINY | `qwen3:1.7b` (1.1 GB) | `granite3.1-moe:1b` (0.7 GB) | `qwen3.5:0.8b` (0.6 GB) |
| worker-b2 | TINY | `qwen3:1.7b` | `granite3.1-moe:1b` | `qwen3.5:0.8b` |
| worker-b3 | TINY | `qwen3:1.7b` | `granite3.1-moe:1b` | `qwen3.5:0.8b` |
| worker-b4 | TINY | `qwen3:1.7b` | `granite3.1-moe:1b` | `qwen3.5:0.8b` |

**Size estimates carry a ±20% verification halt-condition.** At first pull, `ollama show <model>` must report a size within 20% of the estimate above. Anything more than 20% larger halts that VM and triggers a plan review, not a silent retry.

**Fallback picks** (if a primary fails verification or inference):

| Role | Tier | Primary | Silver fallback | Bronze fallback |
|---|---|---|---|---|
| Dense | GiantQueen-B | `qwen3:8b` | `qwen3:4b` | drop to DwarfQueen pick |
| Dense | DwarfQueen | `phi4-mini:3.8b` | `qwen3:4b` | `llama3.2:3b` |
| Dense | Worker TINY | `qwen3:1.7b` | `llama3.2:1b` | `deepseek-r1-distill-qwen:1.5b` |
| MoE | all tiers | `granite3.1-moe:3b` / `granite3.1-moe:1b` | `granite4:3b-h` (if granite3.1 missing) | no third fallback — Granite monoculture for TINY MoE |
| Vision | GiantQueen-B | `qwen2.5vl:7b` | `gemma3:4b` | `moondream` |
| Vision | DwarfQueen | `gemma3:4b` | `qwen2.5vl:7b` | `moondream` |
| Vision | Worker TINY | `qwen3.5:0.8b` | `moondream` | **drop vision round entirely on Workers, let DwarfQueens carry all vision** |

---

## 2. Per-VM disk sizing

Formula:

```
disk = OS_base + sum(model_sizes) + download_scratch + log_tmp + rotation_headroom
```

- `OS_base` = 5 GB (measured from the first build)
- `download_scratch` = `2 × largest_model` (Ollama partial file + final rename)
- `log_tmp` = 2 GB for journald / /tmp / systemd state
- `rotation_headroom` = 1× extra model at the current tier's max size

### 2.1 giantqueen-b

| Component | GB |
|---|---|
| OS base | 5.0 |
| Dense `qwen3:8b` | 5.2 |
| MoE `granite3.1-moe:3b` | 2.0 |
| Vision `qwen2.5vl:7b` | 4.2 |
| Sum models | 11.4 |
| Steady-state (OS + models + log_tmp) | 5 + 11.4 + 2 = 18.4 |
| Peak during largest pull (`qwen3:8b`, 5.2 GB) | 5 + (2.0 + 4.2) + 2×5.2 + 2 = 23.6 |
| Rotation headroom | 8.0 |
| **Required floor** | max(23.6, 18.4 + 8) = 26.4 |
| **Chosen disk size (floor × 2)** | **80 GB** |

### 2.2 dwarfqueen-b1, dwarfqueen-b2

| Component | GB |
|---|---|
| OS base | 5.0 |
| Dense `phi4-mini:3.8b` | 2.5 |
| MoE `granite3.1-moe:3b` | 2.0 |
| Vision `gemma3:4b` | 2.5 |
| Sum models | 7.0 |
| Steady-state | 5 + 7 + 2 = 14.0 |
| Peak during largest pull (2.5 GB) | 5 + 4.5 + 2×2.5 + 2 = 16.5 |
| Rotation headroom | 4.0 |
| **Required floor** | max(16.5, 14 + 4) = 18.0 |
| **Chosen disk size (floor × 2)** | **50 GB each** |

### 2.3 worker-b1, worker-b2, worker-b3, worker-b4

| Component | GB |
|---|---|
| OS base | 5.0 |
| Dense `qwen3:1.7b` | 1.1 |
| MoE `granite3.1-moe:1b` | 0.7 |
| Vision `qwen3.5:0.8b` | 0.6 |
| Sum models | 2.4 |
| Steady-state | 5 + 2.4 + 2 = 9.4 |
| Peak during largest pull (1.1 GB) | 5 + 1.3 + 2×1.1 + 2 = 10.5 |
| Rotation headroom | 5.0 |
| **Required floor** | max(10.5, 9.4 + 5) = 14.4 |
| **Chosen disk size** | **40 GB each** |

### 2.4 Disk totals

| VM | Disk (GB) |
|---|---|
| giantqueen-b | 80 |
| dwarfqueen-b1 | 50 |
| dwarfqueen-b2 | 50 |
| worker-b1 | 40 |
| worker-b2 | 40 |
| worker-b3 | 40 |
| worker-b4 | 40 |
| **Total virtual disk** | **340 GB** |
| **Big volume free** | ~1500 GB |
| **Utilization** | ~22% worst case |

qcow2 files are sparse; real on-disk allocation will grow toward the steady-state ~15–22 GB per VM as models are pulled. Real cumulative footprint at steady state with all 21 models pulled: ~100–130 GB.

---

## 3. Per-VM RAM sizing

Formula:

```
ram = OS_overhead + largest_single_model_in_memory + inference_overhead
```

### 3.1 Per-VM RAM

| VM | Largest model in memory | OS | Model | Inference | Sum | **Chosen RAM** |
|---|---|---|---|---|---|---|
| giantqueen-b | `qwen3:8b` (~5.5) or `qwen2.5vl:7b` (~4.5) → 5.5 | 1.0 | 5.5 | 1.5 | 8.0 | **8 GB** |
| dwarfqueen-b1 | `phi4-mini:3.8b` or `gemma3:4b` (~2.7) | 1.0 | 2.7 | 1.5 | 5.2 | **6 GB** |
| dwarfqueen-b2 | same as b1 | 1.0 | 2.7 | 1.5 | 5.2 | **6 GB** |
| worker-b1..b4 | `qwen3:1.7b` (~1.3) | 1.0 | 1.3 | 1.0 | 3.3 | **4 GB each** |

### 3.2 RAM totals and host-fit check

```
GiantQueen-B       :  8
DwarfQueen-B1      :  6
DwarfQueen-B2      :  6
Worker-B1          :  4
Worker-B2          :  4
Worker-B3          :  4
Worker-B4          :  4
                  ---
Total guest RAM    : 36 GB
```

**Host commit accounting (worst case):**

| Bucket | GiB |
|---|---|
| Physical usable RAM | 62.0 |
| Guest RAM allocation | 36.0 |
| QEMU process envelope tax (7 VMs × ~300 MB for qemu overhead, virtio queues, device models, memfd backing structures) | 2.1 |
| Cinnamon desktop + systemd + libvirtd + ICQ agent + host Ollama daemon idle + buff/cache floor | 2.0 |
| **Expected peak host commit** | **40.1** |
| **Remaining host headroom (floor)** | **~22** |

**Headroom target:** 5–8 GiB free minimum. **Achieved:** ~22 GiB floor. **PASS with ~3× margin.** Nir can work on the host during tests (Claude Code session, browser, text editor, ICQ terminal) without thinking about VM memory.

**Theoretical vs real peak:** the 40.1 GB number is the worst case — every VM running its largest model in memory at the same instant. In real KillerBee workloads the hierarchy delegates (RajaBee → GiantQueen → DwarfQueens → Workers), so not all 7 VMs inference simultaneously, and Ollama lazy-loads models on first call and unloads after idle timeout. Realistic peak commit during normal tests: **~25–30 GB**, leaving **30+ GiB day-to-day headroom**. The 22 GB number is the floor we are guaranteed even in the worst case, not the typical margin.

### 3.3 Context window assumption

All RAM allocations above assume the **Ollama default context window of approximately 8K tokens**. Inference overhead at 8K is ~1.5 GB per running model (~1 GB for Workers where models are smaller and KV cache is proportional to model dimension × context length).

**If Nir or a future session bumps context to 32K or higher** (long documents, multi-turn agents, image-heavy multimodal sessions, RAG experiments), KV cache grows roughly linearly. Per-VM RAM allocations must be recomputed BEFORE the longer context is enabled.

Rough scaling rule (q4_K_M models, llama.cpp-style KV cache):

| Context length | Extra RAM per VM (relative to 8K baseline) |
|---|---|
| 8K (default) | 0 |
| 16K | +1.0 GB |
| 32K | +3.0 GB |
| 64K | +6.0 GB |
| 128K | +12.0 GB |

**At 64K context, the GiantQueen-B 8 GB allocation is no longer enough** (baseline 8 + 6 KV = 14 GB). That VM would need to be rebuilt at 16 GB RAM, pushing total guest RAM from 36 → 44 GB and cutting host headroom from ~22 → ~14 GiB. Still within the 5–8 GiB target but tighter.

**Trip-up warning for future sessions:** more context costs more RAM, always check §3.1 before flipping the context knob.

---

## 4. Per-VM vCPU sizing

| VM | vCPU | Rationale |
|---|---|---|
| giantqueen-b | 6 | Largest dense + vision model; benefits most from more threads up to memory-bandwidth plateau |
| dwarfqueen-b1 | 4 | Mid-sized phi4-mini / gemma3 / granite; 4 threads near plateau for 3–4B models |
| dwarfqueen-b2 | 4 | Same |
| worker-b1..b4 | 2 each | Sub-2B models saturate at 2 threads on CPU |

Total: 6 + 4 + 4 + 2×4 = **22 vCPU on 32 logical** (69% allocation, no overcommit). 10 logical CPUs remain for host + libvirt overhead + any host workload.

---

## 5. Summary table (the one-page version)

All disk sizes below are **2× the §2 floors** per Nir's doubling rule.

| VM | Tier | Disk (GB) | RAM (GB) | vCPU | Dense | MoE | Vision |
|---|---|---|---|---|---|---|---|
| giantqueen-b | old-DQ | 80 | 8 | 6 | `qwen3:8b` ✓ | `granite3.1-moe:3b` ✓ | `qwen2.5vl:7b` ✓ |
| dwarfqueen-b1 | old-Worker | 50 | 6 | 4 | `phi4-mini:3.8b` ✓ | `granite3.1-moe:3b` ✓ | `gemma3:4b` ✓ |
| dwarfqueen-b2 | old-Worker | 50 | 6 | 4 | `phi4-mini:3.8b` ✓ | `granite3.1-moe:3b` ✓ | `gemma3:4b` ✓ |
| worker-b1 | TINY | 40 | 4 | 2 | `qwen3:1.7b` ✓ | `granite3.1-moe:1b` ✓ | `qwen3.5:0.8b` ✓ |
| worker-b2 | TINY | 40 | 4 | 2 | `qwen3:1.7b` ✓ | `granite3.1-moe:1b` ✓ | `qwen3.5:0.8b` ✓ |
| worker-b3 | TINY | 40 | 4 | 2 | `qwen3:1.7b` ✓ | `granite3.1-moe:1b` ✓ | `qwen3.5:0.8b` ✓ |
| worker-b4 | TINY | 40 | 4 | 2 | `qwen3:1.7b` ✓ | `granite3.1-moe:1b` ✓ | `qwen3.5:0.8b` ✓ |
| **Totals** |   | **340 GB** | **36 GB** | **22** |   |   |   |

✓ = tag verified against the live Ollama library. See §11 for the verification trace.

### Fit check

| Resource | Allocated | Host has | Remaining | Verdict |
|---|---|---|---|---|
| Disk (virtual, `/home`) | 340 GB | 1500 GB free | 1160 GB | Plenty. qcow2 sparse, real steady-state ~100–130 GB. |
| RAM (worst case) | 40.1 GB | 62 GiB | ~22 GB | PASS — ~3× the 5–8 GB floor target |
| RAM (realistic peak) | ~28 GB | 62 GiB | ~34 GB | Day-to-day headroom is much larger than worst case |
| vCPU | 22 | 32 | 10 | Plenty, no overcommit |

---

## 6. Explicit acknowledgements

- **MoE round status:** ALIVE. `granite3.1-moe:1b` (Workers) and `granite3.1-moe:3b` (DwarfQueens + GiantQueen-B) both exist on Ollama and are tag-verified. Full seven-VM coverage.
- **Vision round status:** ALIVE WITH KNOWN RISK at the Worker tier. Models exist for all three tiers and all are tag-verified: `qwen2.5vl:7b` on GiantQueen-B, `gemma3:4b` on DwarfQueens, `qwen3.5:0.8b` on Workers. However, sub-1B vision models are an ongoing research frontier, not a proven production capability. There is a real chance that `qwen3.5:0.8b` produces gibberish, refuses inputs, or returns nonsense on real test images despite loading cleanly. **The plan tolerates this explicitly:** if the Worker-tier vision round fails on first real inference, it is dropped and DwarfQueens become the only vision tier for Phase 3. GiantQueen-B and DwarfQueen vision are proven tech and stay fully alive regardless.
- **Model size vs capability trade:** this tier assignment is SLOWER and DUMBER than a theoretical best — V1 had `qwen3:14b` on GiantQueen and `qwen3:8b` on DwarfQueens, this plan downshifts to `qwen3:8b` and `phi4-mini:3.8b`. Token generation is faster (fewer weights per token) but reasoning quality per token is meaningfully lower. Nir explicitly accepted this trade in the downgrade brief: *"we need to be realistic, to downgrade everything."* The goal of Phase 3 is to watch the hive-consensus architecture WORK, not to win a benchmark — dumber models still exhibit the aggregation / escalation / consensus behavior the test is about.
- **RAM budget leaves ~22 GB host headroom (floor)**, not 0–2 GB. Honest accounting for QEMU envelope tax + Cinnamon + libvirtd + ICQ.
- **MINI tier was considered and rejected** for the "one-notch" interpretation. The downgrade brief's mapping is strict two-step (GQ→DQ, DQ→Worker, Worker→TINY), not three-step. If Nir later decides MINI should exist as an intermediate rung, that is a different plan and a different commit.

---

## 7. Execution plan (when Nir green-lights this file)

**Prerequisite:** `scripts/autoinstall_one.sh` and `scripts/full_cycle_one.sh` currently hard-code `size=15` inside the `--disk` flag. Before execution they must be updated to accept a `<disk-GB>` argument and interpolate it. Same for RAM and vCPU if not already parameterized. The driver becomes a loop over `(name, ram-MB, disk-GB, vcpu)` quadruples.

**Sequential one-by-one discipline:** provision VM 1 completely — apt → pip → builds → model pulls → integration test — before touching VM 2. Fix any bug on VM 1 immediately by updating `scripts/full_cycle_one.sh` or `PHASE3_PROVISION_VM.sh` (the STT+tooling provisioning script from `PHASE3_STT_PLAN.md`) in place so every subsequent VM picks up the fix. **Do NOT parallelize the build even though the 24-core CPU could handle it** — the constraint is human debuggability under time pressure, not machine capacity.

**Swap verification check.** After each VM's `full_cycle_one.sh` returns and before any `ollama pull`:

```bash
ssh -i ~/.ssh/phase3_ed25519 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
    -o BatchMode=yes nir@<vm-ip> 'sudo swapon --show && free -h'
```

Expected output: `swapon --show` lists at least one swap entry (typically `/swap.img` on Ubuntu 24.04 Server) with non-zero size; `free -h` shows non-zero `Swap:` total (expected ~2 GB Workers, ~4 GB DwarfQueens and GiantQueen-B).

**If a VM comes up with no swap:** halt that VM's post-install flow, debug the autoinstall seed's `storage:` section, and as an emergency manual fix run on the guest:

```bash
sudo fallocate -l 2G /swap.img && sudo chmod 600 /swap.img && \
  sudo mkswap /swap.img && sudo swapon /swap.img && \
  echo "/swap.img none swap sw 0 0" | sudo tee -a /etc/fstab
```

Rationale: a guest with no swap hard-OOMs on the first inference spike (qwen3:8b + image loaded simultaneously, or unexpected KV cache growth). With even 2 GB swap, an OOM becomes a brief slowdown instead of a killed process. 30-second check per VM catches a failure mode the earlier builds were silent about.

### Full build sequence (sequential, never parallelized)

1. `full_cycle_one.sh giantqueen-b 8192 80 6`
2. Swap verify: `ssh nir@<gqb-ip> 'sudo swapon --show && free -h'`
3. `ollama pull qwen3:8b && ollama pull granite3.1-moe:3b && ollama pull qwen2.5vl:7b` on giantqueen-b
4. Verify with `ollama list` and from host with `curl http://<ip>:11434/api/tags`
5. Run STT+tooling provisioning for the `giantqueen` tier (see `PHASE3_STT_PLAN.md` — installs ffmpeg, whisper.cpp, transformers+torch CPU, Cohere Transcribe weights)
6. Smoke test: one real audio file through the STT pass, one real image through the vision pass, one integration pass through the text reasoner
7. `full_cycle_one.sh dwarfqueen-b1 6144 50 4`
8. Swap verify on dwarfqueen-b1
9. Pull `phi4-mini:3.8b`, `granite3.1-moe:3b`, `gemma3:4b` on dwarfqueen-b1; verify
10. Run STT+tooling provisioning for the `dwarfqueen` tier
11. Smoke test on dwarfqueen-b1
12. `full_cycle_one.sh dwarfqueen-b2 6144 50 4`, same sequence
13. `full_cycle_one.sh worker-b1 4096 40 2`, swap verify, pull `qwen3:1.7b` + `granite3.1-moe:1b` + `qwen3.5:0.8b`, STT+tooling for the `worker` tier, smoke test
14. `full_cycle_one.sh worker-b2 4096 40 2`, same sequence
15. `full_cycle_one.sh worker-b3 4096 40 2`, same
16. `full_cycle_one.sh worker-b4 4096 40 2`, same
17. Full cluster verification: SSH each VM, `hostname && cat /etc/machine-id && ollama list`; from host `curl /api/tags` on each; one end-to-end hierarchy test (RajaBee → GiantQueen → DwarfQueens → Workers on a real audio file and a real image)
18. Telegraph ICQ to Laptop: `"Rebuild complete, 7 VMs up, 21 models pulled, host headroom X GB. Smoke tests green. Awaiting Nir review."`

**Estimated total wall clock:** ~2–3 hours
- 7 × ~4 min autoinstall = 28 min
- 7 × ~1 min post-install = 7 min
- 21 model pulls, total ~45 GB at ~80 MB/s avg = ~10 min transfer plus Ollama processing ≈ 45 min
- 7 × STT provisioning (ffmpeg + pip + whisper.cpp build + model downloads) = ~60 min
- Sanity checks + smoke tests + logging = 20 min

---

## 8. Foreseeable failure modes

1. **`granite3.1-moe:1b` does not exist or was renamed.** IBM's granite naming has shifted multiple times and Ollama occasionally re-tags. Mitigation: before pulling, `ollama show granite3.1-moe:1b` — if the tag is not found, fall back to `granite3.1-moe:3b` on Workers (upper TINY edge, still fits 4 GB RAM). Flag the incident in `EXPERIMENT_LOG.md`.
2. **`qwen3.5:0.8b` vision inference OOMs at 4 GB.** The multi-modal variant carries a vision encoder that can spike memory during image token preprocessing. If a Worker OOMs on first image inference, bump that Worker's RAM to 5 GB via `virsh setmem --config` (requires VM offline). The RAM budget in §3.2 has enough headroom to absorb 4 × 1 GB bump = 4 GB extra, which still leaves ~18 GB host headroom.
3. **GiantQueen-B vision model loaded memory larger than estimate.** `qwen2.5vl:7b` should load to ~4.5 GB, giving the 8 GB GiantQueen-B allocation ~1.5 GB internal headroom. If it OOMs on multi-image inference (e.g., 8+ high-resolution images at once), bump that VM's RAM via `virsh setmem --config` while offline. At +4 GB to GiantQueen-B the host still has ~18 GB headroom, well above the 5–8 GB floor.
4. **Worker TINY multi-modal round is useless because the models are too small to distinguish cat from dog.** Sub-1B vision models are a research frontier, not proven production capability. If the Worker vision round produces gibberish, drop it entirely and let DwarfQueens handle all vision. Document the failure in `EXPERIMENT_LOG.md` and continue.
5. **Total disk allocation jumps past 340 GB** because ±20% on 15 GB of models gives +3 GB, and repeated rotation tests fill `/tmp` and systemd-journald. Low risk — `/home` has 1.5 TB. If tight, shrink `rotation_headroom` from 8 → 4 GB on GiantQueen, 4 → 2 GB on DwarfQueens, 5 → 2 GB on Workers.
6. **STT+tooling provisioning failure on VM 1.** See `PHASE3_STT_PLAN.md` section "Provisioning strategy" for the sequential-one-by-one rule: fix the bug in place in the provisioning script before moving to VM 2. Do not paper over.

---

## 9. Status

Plan is committed. No VMs are being rebuilt. The earlier build's 7 VMs are destroyed. Autoinstall seed, `killerbee` pool, `br0` bridge, build scripts, and template are all ready for execution. **Desktop Claude is waiting for Nir to approve this plan (together with `PHASE3_STT_PLAN.md`) and authorize the sequential rebuild.**

Once Nir approves both plans, the execution order is: this plan first (VM hierarchy + text/vision models via Ollama), then the STT+tooling plan layered on top of each VM in the same sequential pass. Both layers run as one unified sequential build per VM — VM 1 gets fully provisioned (hierarchy + STT + tooling) before VM 2 starts.

---

## 10. Tag verification (live Ollama library)

All 8 primary model tags were verified against `https://ollama.com/library/<model>/tags` by direct HTTP fetch. Every primary pick below has been confirmed as a real, published Ollama library tag — no guesses, no "should exist", no "probably there".

| Tag | Verified | Notes |
|---|---|---|
| `qwen3:8b` | ✓ | Plus `qwen3:8b-q4`, `qwen3:8b-q8` variants |
| `qwen3:1.7b` | ✓ | Plus `qwen3:1.7b-q4`, `q8`, `fp16` variants |
| `qwen3.5:0.8b` | ✓ | Plus `qwen3.5:0.8b-q8`, `bf16`, `mxfp8`, `nvfp4` variants |
| `phi4-mini:3.8b` | ✓ | Plus `phi4-mini:3.8b-q4`, `q8`, `fp16` variants; `phi4-mini:latest` also present |
| `granite3.1-moe:1b` | ✓ | Plus `granite3.1-moe:1b-instruct-q4`, `q5`, `q6`, `q8` variants |
| `granite3.1-moe:3b` | ✓ | Plus `granite3.1-moe:3b-instruct-q4`, `q5`, `q6`, `q8` variants |
| `gemma3:4b` | ✓ | Plus `gemma3:4b-it-q4`, `q8`, `fp16`, `qat` variants |
| `qwen2.5vl:7b` | ✓ | Plus `qwen2.5vl:7b-q4`, `q8`, `fp16` variants |

### Rejected tags (do not use, verified non-existent)

| Tag | Reason |
|---|---|
| `qwen3-vl:8b` | `qwen3-vl` line jumps 2b → 30b on Ollama; no 4b, 7b, or 8b exists. Fallback path: use `qwen2.5vl:7b` (primary for GiantQueen-B). |
| `moondream2:1.7b` | Correct tag is `moondream` (no trailing 2, no explicit size suffix). |
| `ministral3:3b` | Does not exist on Ollama. |
| `smollm3:3b` | No v3 on Ollama; closest is `smollm2:1.7b`. |
| `granite3:*` (without `.1`) | Correct namespaces are `granite3.1-moe`, `granite3.1-dense`, `granite3.2`, `granite3.3`, or `granite4`. |

**Lesson for future sessions:** always verify against `https://ollama.com/library/<model>/tags` before committing a tag to a plan file. Do not trust blog posts or research paper names — they often do not match the Ollama registry exactly.

### Bonus — `granite4` family (not used in current plan, noted for future)

- `granite4:350m`, `granite4:1b`, `granite4:3b`, `granite4:3b-h` (hybrid) — fresh TINY/MINI IBM options
- `granite4:7b-a1b-h` — 7B total, 1B active hybrid MoE
- `granite4:32b-a9b-h` — 32B total, 9B active, for a future larger-tier revision

If Nir later wants to upgrade the MoE row from `granite3.1-moe` to `granite4`, these are the candidate tags.

---

*Canonical rebuild plan. Edit in place. Git is the time machine.*
