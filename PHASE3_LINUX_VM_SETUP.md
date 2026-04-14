# Phase 3: Linux VM Setup for the Full 15-VM KillerBee Cluster

**Audience:** Nir + the Claude Code session guiding him through this (Desktop Linux Claude on Mint, Laptop Linux Claude on Debian 13).
**Host OS — Desktop:** Linux Mint 22.2 "Zara" (Ubuntu 24.04 / `noble` base), kernel 6.14.0-37-generic, 64 GB RAM, RTX 4070 Ti, 10.0.0.5.
**Host OS — Laptop:** Debian 13 "Trixie", 64 GB RAM, RTX 5090, 10.0.0.1.
**Status:** Topology locked 2026-04-14. RAM budget per tier is **NOT YET LOCKED** — Nir is choosing between Options A/B/C in §4. Models are **NOT YET CHOSEN** — to be discovered via open-ended Google searches by category (§6), in three rounds: Dense → MoE → Vision. Build has not started.
**Precondition:** Phase 2 LAN test PASSED on 2026-04-11 (see `EXPERIMENT_LOG.md` Experiment 3).

> **WARNING TO ANY CLAUDE READING THIS DOC:** an earlier version of this file (committed 2026-04-14 08:47 UTC by Desktop Windows Claude) was wrong. It said Debian 12 netinst for the VMs and `llama3.2:3b` for the model. **That was never the plan.** The real plan is in this file. Do not revert to the earlier version. If you find yourself about to recommend Debian 12, llama3.2, or "same model on every VM," stop and re-read this file from the top.

---

## 1. Why this exists (Rule #1 recap)

`KillerBee/CLAUDE.md` Rule #1: if the architecture says a bee is a separate machine, it must BE a separate machine — its own OS, own IP, own processes — **or a real VM with the same properties.** No in-process fakes. No threads pretending to be distributed.

The full KillerBee hierarchy is **RajaBee → GiantQueens → DwarfQueens → Workers**. The smallest non-trivial topology that exercises every layer is **1 RajaBee + 2 GiantQueens + 4 DwarfQueens + 8 Workers = 15 separate machines**. We have two physical hosts. Math is short by 13. VMs are how the math closes.

We are building all 15 VMs **now**, in one go, so we never have to scramble for "one more box" mid-experiment.

## 2. The target topology (15 VMs, both hosts)

```
RajaBee (Laptop, 10.0.0.11)
|
+-- GiantQueen-A (Laptop, 10.0.0.12)
|     |
|     +-- DwarfQueen-A1 (Laptop, 10.0.0.13)
|     |     +-- Worker-A1a (Laptop, 10.0.0.15)
|     |     +-- Worker-A1b (Laptop, 10.0.0.16)
|     |
|     +-- DwarfQueen-A2 (Desktop, 10.0.0.21)
|           +-- Worker-A2a (Desktop, 10.0.0.22)
|           +-- Worker-A2b (Desktop, 10.0.0.23)
|
+-- GiantQueen-B (Desktop, 10.0.0.24)
      |
      +-- DwarfQueen-B1 (Laptop, 10.0.0.14)
      |     +-- Worker-B1a (Laptop, 10.0.0.17)
      |     +-- Worker-B1b (Laptop, 10.0.0.18)
      |
      +-- DwarfQueen-B2 (Desktop, 10.0.0.25)
            +-- Worker-B2a (Desktop, 10.0.0.26)
            +-- Worker-B2b (Desktop, 10.0.0.27)
```

**Why RajaBee on Laptop:** the KillerBee website (Flask, port 8877) and the WaggleDance server (Flask, port 8765) both run on the Laptop host. RajaBee talks to the website most. Keep it close.

**Why GiantQueens split across hosts:** Rule #1 — different physical machines really should be in the picture for a 3-level hierarchy test, not "all queens on one box."

## 3. Per-host VM count and OS

| Host | Host OS | Guest OS for ALL its VMs | VM count |
|---|---|---|---|
| **Laptop** (10.0.0.1, Debian 13, 64 GB) | Debian 13 Trixie | **Debian 13 Trixie netinst (minimal, no DE)** | **8** |
| **Desktop** (10.0.0.5, Linux Mint 22.2, 64 GB) | Linux Mint 22.2 (Ubuntu 24.04 base) | **Ubuntu Server 24.04 LTS (minimal, no DE)** | **7** |

**Why match guest to host family:** Same package manager, same kernel line, same muscle memory for the human guiding the install. We considered cross-mixing for "more heterogeneity," Nir chose match-host for simplicity. Decision is locked.

**Why "Server" / "netinst" and not Desktop flavors:** these are the headless minimal flavors. No GUI inside the VM. The VMs only run Ollama + a Python bee process and answer over the network — nobody will ever sit in front of one. Headless flavors save 2-3 GB disk and ~500 MB RAM per VM compared to their desktop siblings. With 15 VMs that compounds.

## 4. RAM budget — NOT YET LOCKED, three options on the table

We are **not** doing PCIe GPU passthrough into the VMs. GPU passthrough on KVM is doable but fragile (IOMMU groups, vfio binding, host driver blacklisting), and it monopolizes the GPU — only one VM gets it. For a 15-VM cluster it doesn't scale. Inference inside each VM is **CPU-only** via Ollama. The host GPUs are still useful for non-VM workloads — we just don't expose them to the guests.

**Design constraints from Nir (2026-04-14):**
1. Quality > speed. Long inference waits are acceptable.
2. Each layer of the hierarchy uses bigger models than the layer below. Workers small, DwarfQueens bigger, GiantQueens bigger still, RajaBee biggest.
3. Workers are **small, not tiny**. No 0.5B / 1B microcrumbs.
4. RajaBee and GiantQueens should be the **largest the hardware allows**.
5. 64 GB RAM per host. Two hosts. CPU-only inference.

**The squeeze:** at ~`params × 0.6 GB` per q4 model, "biggest at the top" + 15 simultaneous VMs + 64 GB hosts pulls in opposite directions. We have to pick a tradeoff. Three honest options:

### Option A — All 15 always on, accept smaller top
| Tier | RAM/VM | Fits roughly |
|---|---|---|
| Worker | 4 GB | 3B q4 model |
| DwarfQueen | 6 GB | 7B q4 model (tight) |
| GiantQueen | 10 GB | 13B q4 model (tight) |
| RajaBee | 14 GB | 14B q4 model (tight) |

Laptop usage: 14 + 10 + 6 + 6 + 4×4 = **52 GB / 64**. 12 GB free for host. Comfortable.
Desktop usage: 10 + 6 + 6 + 4×4 = **38 GB / 64**. 26 GB free. Very comfortable.
**Cost:** RajaBee maxes at ~14B. Not flagship.

### Option B — Big top tier, run cluster in waves
| Tier | RAM/VM | Fits roughly |
|---|---|---|
| Worker | 6 GB | 7B q4 model |
| DwarfQueen | 12 GB | 14B q4 model |
| GiantQueen | 20 GB | 22B q4 (or 27B q4 tight) |
| RajaBee | 28 GB | 32B q4 model |

Naive Laptop usage: 28 + 20 + 12 + 12 + 6×4 = **96 GB**. Over 64 by 32 GB.
**This is only viable if not all 15 are loaded simultaneously.** Concretely: RajaBee + both GiantQueens + the 2 DwarfQueens currently on the active path stay resident; idle Workers are `virsh suspend`ed and woken on demand. A suspended VM keeps its IP, libvirt domain, processes (frozen), and Ollama state — Rule #1 is still satisfied in spirit (it is a real separate machine, just paused). Active-set RAM on Laptop with 2 Workers awake: 28+20+12+12+6+6 = **84 GB** — still over 64. To fit we also need to swap one GiantQueen + DwarfQueens between hosts, or run only one branch of the tree at a time.
**Cost:** complex orchestration, plus paused-bee semantics may break some Rule #1 tests where "all bees online" is the explicit invariant.

### Option C — Mid path, all 15 on, modest top
| Tier | RAM/VM | Fits roughly |
|---|---|---|
| Worker | 4 GB | 3B q4 model |
| DwarfQueen | 8 GB | 8B q4 / 7B q5 model |
| GiantQueen | 12 GB | 13B q4 (or 14B q4 tight) |
| RajaBee | 18 GB | 22B q4 model |

Laptop usage: 18 + 12 + 8 + 8 + 4×4 = **62 GB / 64**. Only 2 GB host headroom — *tight*. KillerBee website + WaggleDance + host Ollama may need to move to Desktop, or we accept that the Laptop host runs basically nothing besides the libvirt stack while a test is in progress.
Desktop usage: 12 + 8 + 8 + 4×4 = **44 GB / 64**. 20 GB free. Comfortable.
**Cost:** RajaBee = 22B (decent but not flagship). Workers stay small (3B).

### 4.1 Quantization (already baked in, but we can push it further)

Ollama serves quantized models by default — `ollama pull qwen2.5:32b` returns `q4_K_M` (4-bit), not full-precision fp16. The `params × 0.6 GB` math used in Options A/B/C above **already assumes q4_K_M.** Quantization is not a new lever; it is the one we have been pulling all along.

What we *can* do is push the dial harder for the top of the tree, where larger models tolerate aggressive quantization better than small ones. Rough RAM-per-billion-params at common quant levels:

| Quant | GB per 1B params | Quality vs fp16 | Notes |
|---|---|---|---|
| fp16 | 2.0 | 100% | not viable on this hardware |
| q8_0 | 1.0 | ~99% | overkill |
| q6_K | 0.75 | ~98% | nice for top tier |
| q5_K_M | 0.7 | ~97% | safe for small models |
| **q4_K_M** | **0.6** | **~95%** | **Ollama default** |
| q3_K_M | 0.45 | ~90% | aggressive; works on big models |
| q2_K | 0.3 | ~80% | only on very large models; breaks small ones |

**Rule of thumb for this cluster:** quantize the *top* of the tree harder, not the bottom. A 70B at q2 is still useful; a 3B at q2 is broken. Workers stay at q4 or q5; RajaBee may go to q3 to fit a much larger base model in the same VM.

### 4.2 Option C-quant (preferred starting point — to confirm with Nir)

Apply Options C's RAM caps but assign quantization per tier:

| Tier | RAM/VM | Quant | Fits roughly |
|---|---|---|---|
| Worker | 4 GB | q5_K_M | 3B q5 model |
| DwarfQueen | 8 GB | q4 or q3 | 8B q4 or 13B q3 |
| GiantQueen | 12 GB | q3_K_M | 22B q3 (or 14B q5) |
| RajaBee | 18 GB | q3_K_M | **32B q3** (or 27B q4 as fallback) |

Same per-host totals as plain Option C (Laptop 62/64, Desktop 44/64), but RajaBee jumps from a 22B model to a **32B model** at the same VM size. Real quality upgrade, no extra RAM.

### Decision: C-quant LOCKED 2026-04-14 by Nir
Worker 4 GB / DwarfQueen 8 GB / GiantQueen 12 GB / RajaBee 18 GB, with quantization pushed harder at the top (q3_K_M for GiantQueen + RajaBee, q4 for DwarfQueen, q5 for Worker). Search Google for models by parameter range only — do NOT mention quantization or CPU/RAM in the queries; assume models hold up under quantization, then Claude picks the exact quantized tag from ollama.com/library after Nir pastes the list.

### 4.3 Google search rules (locked by Nir 2026-04-14)
1. **Short keyword queries.** Google is not ChatGPT — do not paste paragraphs. 5-8 words max per query.
2. **Always include the word `ollama`** in the query so results point at the Ollama library, not random Hugging Face mirrors or research papers.
3. **Always end the query with `2026`** so Google biases toward current releases.
4. **Do NOT mention "quantized", "q3", "q4", "CPU", "RAM", "VM"** in the query. We assume all candidates hold up under quantization; Claude picks the exact `q*` tag from `ollama.com/library` later.
5. **Many short searches, not one mega-query.** Each tier × each round gets its own short query.
6. **Nir runs the searches manually**, pastes the list back. Claude does not have live web access in this session.

## 5. IP plan (bridged networking on br0)

| Range | Used by |
|---|---|
| 10.0.0.1 | Laptop host |
| 10.0.0.5 | Desktop host |
| 10.0.0.11 – 10.0.0.18 | Laptop VMs (8 slots) |
| 10.0.0.21 – 10.0.0.27 | Desktop VMs (7 slots) |

All VMs on the real LAN via `br0`, **not** the libvirt default NAT (`192.168.122.x`). NAT would isolate VMs from the Laptop's KillerBee website at `10.0.0.1:8877` and break the test. See §7 for bridge setup.

## 6. Model selection — three test rounds, open category discovery

### 6.1 Three rounds, three independent model assignments

The same 15 VMs will be tested in three independent passes. Each pass loads a different *family* of models, runs the same KillerBee benchmark, and gets logged to `EXPERIMENT_LOG.md` as its own experiment.

| Round | Model family | Why |
|---|---|---|
| **1. Dense** | Standard dense transformers (Qwen, Llama, Gemma, etc.) | The baseline. What every distributed-AI paper assumes. |
| **2. MoE** | Mixture-of-Experts (DeepSeek-V3, Qwen-MoE, Mixtral, Phi-MoE, etc.) | MoE punches above its weight on CPU because only a fraction of experts activate per token. Could let us run "bigger" effective models in the same RAM budget. |
| **3. Vision** | Vision-language models (Qwen-VL, LLaVA, MiniCPM-V, etc.) | Lets the swarm process images. Opens up image-batch tasks for the cluster. |

Between rounds: stop all bees, `ollama rm` the previous round's models, `ollama pull` the next round's models, restart bees. Same VMs, same hostnames, same IPs.

### 6.2 Hard filters for every model in every round

- **Available on `ollama.com/library`** as a real published tag. No "you can convert it from Hugging Face." Already tested non-Ollama paths in the LM Studio era; not going there again.
- **Released recently** — we want current state-of-the-art, not 2024 leftovers. Each Google search is time-bounded to the most recent releases.
- **English-language tasks.** No Chinese/Hebrew language requirement. (We expect the answers to be mostly Chinese-lab models because China leads in small-and-efficient open models, but origin is not a filter — Google/Meta/Mistral/etc. results are equally welcome if they're the best in their category.)
- **Quality > speed.** A model that takes 5 minutes per token is fine if it's smarter than one that takes 5 seconds.
- **Fits the tier RAM budget** picked in §4 (Option A/B/C TBD).

### 6.3 Discovery protocol — open-ended Google searches by category

Claude has no live web in this session. Each category gets **one open-ended Google query** that Claude writes for Nir. Nir pastes it into Google, lets Google's AI / Gemini / search results answer, pastes the response back. Claude writes the candidates into the table for that category. Repeat per category. Then assignment.

**Open-ended means:** the question is "what are the best X" not "is X available." We want Google to volunteer names we haven't thought of, including non-Chinese ones if they're genuinely competitive.

Categories per round are chosen so that each tier (Worker / DwarfQueen / GiantQueen / RajaBee) has at least one search aimed at the parameter range it can host.

#### Round 1 — Dense models, categories:
- **D1.** Best small dense LLMs (≈3B-class) on Ollama for Worker tier.
- **D2.** Best mid-size dense LLMs (≈7B-8B-class) on Ollama for DwarfQueen tier.
- **D3.** Best larger dense LLMs (≈13B-14B-class) on Ollama for GiantQueen tier.
- **D4.** Best top-tier dense LLMs (≈22B-32B-class) on Ollama for RajaBee.
- (Add D5 if Option B in §4 is picked: Best ≈70B-class dense on Ollama, for the wave-loaded RajaBee.)

#### Round 2 — MoE models, categories:
- **M1.** Best MoE LLMs on Ollama with small total footprint (single-digit GB) — Worker tier.
- **M2.** Best MoE LLMs on Ollama in the ~10-20 GB RAM footprint — Queen tiers.
- **M3.** Best top-tier MoE LLMs on Ollama (DeepSeek-V3 family, Qwen-MoE family, etc.) — RajaBee.

#### Round 3 — Vision models, categories:
- **V1.** Best small vision-language LLMs on Ollama — Worker tier.
- **V2.** Best mid-size vision-language LLMs on Ollama — DwarfQueen / GiantQueen tier.
- **V3.** Best top-tier vision-language LLMs on Ollama — RajaBee.

### 6.4 Candidate tables (filled in as Google answers come back)

#### Round 1 — Dense

| Cat | Tier | RAM target | Candidates from Google (filled per search) | Chosen |
|---|---|---|---|---|
| D1 | Worker | tier-W | _pending search D1_ | _pending_ |
| D2 | DwarfQueen | tier-DQ | _pending search D2_ | _pending_ |
| D3 | GiantQueen | tier-GQ | _pending search D3_ | _pending_ |
| D4 | RajaBee | tier-RB | _pending search D4_ | _pending_ |

#### Round 2 — MoE

| Cat | Tier | RAM target | Candidates from Google | Chosen |
|---|---|---|---|---|
| M1 | Worker | tier-W | _pending search M1_ | _pending_ |
| M2 | Queens | tier-DQ/GQ | _pending search M2_ | _pending_ |
| M3 | RajaBee | tier-RB | _pending search M3_ | _pending_ |

#### Round 3 — Vision

| Cat | Tier | RAM target | Candidates from Google | Chosen |
|---|---|---|---|---|
| V1 | Worker | tier-W | _pending search V1_ | _pending_ |
| V2 | DQ/GQ | tier-DQ/GQ | _pending search V2_ | _pending_ |
| V3 | RajaBee | tier-RB | _pending search V3_ | _pending_ |

### 6.5 Final per-VM assignments (filled at the end of each round)

Same shape three times — one table per round — once Nir has chosen from the candidates above. Until §4 (RAM tier) and §6.4 (candidates) are filled, no `ollama pull` and no `virt-install` happens.

## 7. Build order

1. **Confirm CPU virt enabled on Desktop:** `grep -E 'vmx|svm' /proc/cpuinfo` — done in this Mint session before installing KVM.
2. **Install KVM stack on Desktop:** `qemu-kvm libvirt-daemon-system libvirt-clients bridge-utils virtinst virt-manager`. Add user to `libvirt` and `kvm` groups, log out/in.
3. **Build `br0` bridge on Desktop** (§5 — bridged, not NAT).
4. **Download Ubuntu Server 24.04 LTS minimal ISO** to `~/isos/ubuntu-24.04-server-amd64.iso`.
5. **Build template VM `desktop-template`:**
   - 2 vCPU, 4 GB RAM, 15 GB disk (template specs; clones get resized later).
   - Install Ubuntu Server 24.04 minimal, no extra packages, OpenSSH only.
   - Hostname: `desktop-template`. User: `nir`.
   - Inside the VM: install `curl python3 python3-pip git`, install Ollama, set `OLLAMA_HOST=0.0.0.0` via `systemctl edit ollama` (not `.bashrc` — service does not inherit user env), `systemctl restart ollama`.
   - Verify from Desktop host: `curl http://<vm-ip>:11434/api/tags` returns JSON.
6. **Shut down `desktop-template`** and clone with `virt-clone --original desktop-template --name desktop-vm-N --auto-clone` for N = 1..7. Each clone:
   - Boot, SSH in, `hostnamectl set-hostname <role-name>` (e.g. `giantqueen-b`), reboot, verify new IP via DHCP, `ollama pull <verified model from §6>`.
7. **Run §6.1 verification loop FIRST** before any `ollama pull` happens on any VM. Pulling 15 hallucinated tags would fail loudly but waste hours.
8. **Hand off to Laptop Linux Claude** over WaggleDance ICQ to do the same with **Debian 13 Trixie netinst** as the guest OS on the Laptop host. Same template+clone pattern, same verification loop, same RAM budget.
9. **Run the Rule #1 compliance checklist (§9 below) across all 15 VMs.**
10. **Run the 3-DwarfQueen test first** (§10) as the warm-up — only 3 of the 4 DwarfQueens active, RajaBee plus one GiantQueen. Then scale to the full 1+2+4+8 GiantQueen 3-level test.

## 8. KVM/QEMU + virt-manager prerequisites — Desktop side

(This section was correct in the previous version and is unchanged in spirit; preserved here so the doc is self-contained.)

**8.1 — Confirm CPU virt:**
```
grep -E --color 'vmx|svm' /proc/cpuinfo
```
Several highlighted lines = on. Empty = reboot into BIOS, enable Intel VT-x or AMD-V, save.

**8.2 — Install KVM + tools** (Mint 22.2, apt-based, identical command on Debian 13):
```
sudo apt update
sudo apt install -y qemu-kvm libvirt-daemon-system libvirt-clients bridge-utils virtinst virt-manager
```

**8.3 — Group membership:**
```
sudo usermod -aG libvirt $USER
sudo usermod -aG kvm $USER
```
Log out and back in. Confirm with `groups`.

**8.4 — libvirtd running:**
```
sudo systemctl status libvirtd
sudo systemctl enable --now libvirtd
```

**8.5 — Host-side dev stack** (host-side Ollama is for non-VM experiments; the VMs each run their own):
```
sudo apt install -y git python3 python3-pip python3-venv curl
curl -fsSL https://ollama.com/install.sh | sh
echo 'export OLLAMA_HOST=0.0.0.0' >> ~/.bashrc
sudo systemctl restart ollama
```

## 9. The bridge (br0) — both hosts, identical procedure

NAT default is wrong for us. We need bridged so VMs get real `10.0.0.x` IPs reachable from the other host.

**9.1 — Identify the host's LAN interface:**
```
ip -br link
```
Pick the UP interface with the LAN MAC (`enp3s0`, `eno1`, `eth0`, etc.). Call it `<IFACE>`.

**9.2 — Create the bridge** (NetworkManager / nmcli, the Mint default):
```
sudo nmcli connection add type bridge ifname br0 con-name br0
sudo nmcli connection add type bridge-slave ifname <IFACE> master br0
sudo nmcli connection modify br0 bridge.stp no
sudo nmcli connection up br0
```
**Warning:** the host briefly drops LAN. Do this from the local console, not SSH.

**9.3 — Verify:**
```
ip -br addr show br0
```
`br0` should have the host's LAN IP.

**9.4 — Tell libvirt about it.** Save `/tmp/br0.xml`:
```
<network>
  <name>br0</name>
  <forward mode='bridge'/>
  <bridge name='br0'/>
</network>
```
Then:
```
sudo virsh net-define /tmp/br0.xml
sudo virsh net-start br0
sudo virsh net-autostart br0
sudo virsh net-list --all
```
Should show `br0 active autostart`.

## 10. Rule #1 compliance checklist (run before declaring the cluster ready)

Per VM:
- [ ] Own IP on `10.0.0.0/24` (verify with `ip -br addr show` inside).
- [ ] Own kernel (`uname -r` matches the guest OS, not the host).
- [ ] Own Ollama process (`ps aux | grep ollama` inside; `curl http://<vm-ip>:11434/api/tags` from a different machine).
- [ ] Reachable from the Laptop's KillerBee website host (ping + curl on 8877).
- [ ] The model assigned in §6 is the one actually loaded (`ollama list` matches the verified table).
- [ ] No bee process on the VM was spawned as a host subprocess. Each bee is a separately launched process inside the VM, registered to the KillerBee website as a distinct user.

If ANY box is unchecked: **stop**. Fix before running tests. No papering over.

## 11. Running the tests

**Warm-up (3-DwarfQueen parallel test):**
1. Laptop host: KillerBee website running on `:8877`.
2. Laptop host: WaggleDance running on `:8765`.
3. Three DwarfQueen VMs (any 3 of the 4): start `dwarf_queen_client.py --server http://10.0.0.1:8877 --swarm-id 1 --username queen_<X> --password password --model <verified model from §6>`.
4. Two Workers per DwarfQueen: start `worker_client.py` similarly.
5. RajaBee VM (10.0.0.11): start `raja_bee.py --server http://10.0.0.1:8877 --swarm-id 1 --username raja_nir --password password --model <verified model>`.
6. Laptop host: submit a job via the website UI.
7. Log to `EXPERIMENT_LOG.md` as Experiment 4.

**Expected hiccup:** `seed_data.py` currently seeds `queen_alpha` and `queen_bravo` only. Add `queen_charlie` (and a third Worker pair, plus a `raja_nir` user if not present) to the seed before running. Commit the seed change.

**Full GiantQueen 3-level test (after warm-up passes):** all 15 VMs, full hierarchy from §2. Same script pattern, scaled. Expect this to be the first time the cluster has ever run with two GiantQueens above four DwarfQueens above eight Workers all on heterogeneous Chinese models.

## 12. Troubleshooting

- **VM gets `192.168.122.x` not `10.0.0.x`** → bridge not wired. `sudo virsh edit <vm>`, set `<source bridge='br0'/>` on the NIC.
- **Host loses network when bringing up `br0`** → distro wasn't using NetworkManager. Fall back to `/etc/network/interfaces` or `systemd-networkd`. Stop and ask Nir to describe the network state before guessing.
- **`virt-manager` cannot see your VMs** → user not in `libvirt` group, or you ran `sudo virt-manager` (which sees a different libvirt connection). Fix groups, log out/in, run as normal user.
- **Ollama in VM refuses LAN connections** → `OLLAMA_HOST=0.0.0.0` not picked up by the systemd unit. `systemctl edit ollama` (not `.bashrc`), add `Environment="OLLAMA_HOST=0.0.0.0"`, `systemctl restart ollama`.
- **Host swaps under load** → too many VMs running with too-large models. Pause some VMs (`virsh suspend <vm>`) until you find the working set that fits 64 GB. Update §4 budget.
- **Ollama tag from §6 doesn't pull** → it was hallucinated. Re-run §6.1 Google verification for that row before retrying.

## 13. Session handshake for any future Claude on this mission

When Desktop Linux Claude or Laptop Linux Claude wakes up and is told "your mission is Phase 3 VM setup," the handshake REPLY on ICQ should say, in one message:

> *"Role: <desktop-linux-claude | laptop-linux-claude>. Track: testing / Phase 3 VM setup. Repos synced. Read: FRESH_CLAUDE_START_HERE, PARALLEL_VIBING, WHEN_TO_USE_WAGGLEDANCE, LESSONS, KillerBee/PROJECT_REPORT, KillerBee/CLAUDE, KillerBee/PHASE3_LINUX_VM_SETUP. I understand: 15 VMs total, Ubuntu Server 24.04 minimal on Desktop host, Debian 13 Trixie netinst on Laptop host, CPU-only Ollama, different Chinese model per VM, model list in §6 is PROVISIONAL and must be Google-verified before any pull. Ready to guide Nir through §8 prerequisites. Over."*

Then stop. Wait for Nir to say go.

---

## Changelog

- **2026-04-14 08:47 UTC** — Initial version by Desktop Windows Claude (Opus 4.6) before reboot to Linux. **Wrong on key points** (Debian 12 netinst guests, llama3.2:3b, same model on every VM). Superseded.
- **2026-04-14 (afternoon, Linux session)** — Full rewrite by Desktop Linux Claude (Opus 4.6, on Mint 22.2 after reboot) under direct correction from Nir. Locked: Ubuntu Server 24.04 minimal on Desktop VMs, Debian 13 Trixie netinst on Laptop VMs, full 15-VM topology (1 RajaBee + 2 GiantQueens + 4 DwarfQueens + 8 Workers), CPU-only Ollama. Model selection then: provisional Chinese-only table, row-by-row verification.
- **2026-04-14 (later that afternoon)** — §4 (RAM budget) and §6 (model selection) corrected by Nir. Origin filter "Chinese only" **removed** — origin is not a filter, quality is; in practice most answers are expected to be Chinese-lab models because China leads in small-and-efficient open models, but Google/Meta/Mistral/etc. results are accepted on merit. "Tiny" tier removed — Workers are small, not tiny, and each layer above grows. RajaBee + GiantQueens should be the largest the hardware allows. Three test rounds added (Dense → MoE → Vision), each its own model assignment over the same 15 VMs. RAM budget left as three options (A small-top-all-on, B big-top-waves, C mid-all-on) pending Nir's pick. Model discovery is now open-ended Google searches by category, not row-by-row tag verification.
