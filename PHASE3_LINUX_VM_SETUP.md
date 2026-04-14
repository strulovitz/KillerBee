# Phase 3: Linux VM Setup for the Full 15-VM KillerBee Cluster

**Audience:** Nir + the Claude Code session guiding him through this (Desktop Linux Claude on Mint, Laptop Linux Claude on Debian 13).
**Host OS — Desktop:** Linux Mint 22.2 "Zara" (Ubuntu 24.04 / `noble` base), kernel 6.14.0-37-generic, 64 GB RAM, RTX 4070 Ti, 10.0.0.5.
**Host OS — Laptop:** Debian 13 "Trixie", 64 GB RAM, RTX 5090, 10.0.0.1.
**Status:** Plan locked 2026-04-14 by Nir + Desktop Linux Claude. Models PROVISIONAL — must be verified via Google before pulling. Build not started.
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

## 4. RAM budget (CPU-only Ollama, no GPU passthrough)

We are **not** doing PCIe GPU passthrough into the VMs. GPU passthrough on KVM is doable but fragile (IOMMU groups, vfio binding, host driver blacklisting), and it monopolizes the GPU — only one VM gets it. For a 15-VM cluster it doesn't scale. Inference inside each VM is **CPU-only** via Ollama. The host GPUs are still useful for non-VM workloads (host-side experiments, Honeymation, etc.) — we just don't expose them to the guests.

| Role | RAM per VM | Why |
|---|---|---|
| RajaBee | 8 GB | runs the largest reasoning model in the cluster |
| GiantQueen | 6 GB | planning model, mid-size |
| DwarfQueen | 6 GB | delegation model, mid-size |
| Worker | 4 GB | small executor, smallest models |

**Laptop usage:** RajaBee(8) + GiantQueen-A(6) + 2×DwarfQueen(6+6) + 4×Worker(4×4) = **42 GB**. Free for host: 22 GB. KillerBee website + WaggleDance server + host Ollama + headroom — comfortable.

**Desktop usage:** GiantQueen-B(6) + 2×DwarfQueen(6+6) + 4×Worker(4×4) = **34 GB**. Free for host: 30 GB. Very comfortable.

Neither host should swap.

## 5. IP plan (bridged networking on br0)

| Range | Used by |
|---|---|
| 10.0.0.1 | Laptop host |
| 10.0.0.5 | Desktop host |
| 10.0.0.11 – 10.0.0.18 | Laptop VMs (8 slots) |
| 10.0.0.21 – 10.0.0.27 | Desktop VMs (7 slots) |

All VMs on the real LAN via `br0`, **not** the libvirt default NAT (`192.168.122.x`). NAT would isolate VMs from the Laptop's KillerBee website at `10.0.0.1:8877` and break the test. See §7 for bridge setup.

## 6. Model assignment — PROVISIONAL, MUST BE GOOGLE-VERIFIED

> **STATUS: UNVERIFIED.** The model tags below are Desktop Claude's best guess at what's currently published on `ollama.com/library`. Claude does **not** have live web access in this session and the Ollama library changes constantly. Before pulling any of these, Nir will run a Google search per row (Claude will write the exact search string), paste the answer back, and we will replace the row with a real, currently-available tag. Rows still marked `?` after that pass do not get pulled.
>
> **Hard rule:** all 15 models must be from **Chinese labs** (Alibaba/Qwen, DeepSeek, Shanghai AI Lab/InternLM, Zhipu/GLM, 01.AI/Yi, Baichuan, etc.). If a row's verification turns up only non-Chinese alternatives, the row stays empty until we find a Chinese substitute. **No silent substitution with Llama, Gemma, Phi, Mistral, etc.**

| # | VM | Role | Host | RAM | Provisional model (UNVERIFIED) |
|---|---|---|---|---|---|
| 1 | RajaBee | orchestrator | Laptop | 8 GB | `deepseek-r1:7b` ? |
| 2 | GiantQueen-A | planner | Laptop | 6 GB | `qwen3:4b` ? |
| 3 | GiantQueen-B | planner | Desktop | 6 GB | `qwen2.5:7b` ? |
| 4 | DwarfQueen-A1 | delegator | Laptop | 6 GB | `qwen2.5:3b` ? |
| 5 | DwarfQueen-A2 | delegator | Desktop | 6 GB | `qwen2.5-coder:3b` ? |
| 6 | DwarfQueen-B1 | delegator | Laptop | 6 GB | `qwen3:1.7b` ? |
| 7 | DwarfQueen-B2 | delegator | Desktop | 6 GB | `deepseek-coder:6.7b` ? |
| 8 | Worker-A1a | executor | Laptop | 4 GB | `qwen2.5:1.5b` ? |
| 9 | Worker-A1b | executor | Laptop | 4 GB | `qwen2.5:0.5b` ? |
| 10 | Worker-A2a | executor | Desktop | 4 GB | `qwen2.5-coder:1.5b` ? |
| 11 | Worker-A2b | executor | Desktop | 4 GB | `qwen2.5-coder:0.5b` ? |
| 12 | Worker-B1a | executor | Laptop | 4 GB | `qwen3:0.6b` ? |
| 13 | Worker-B1b | executor | Laptop | 4 GB | `deepseek-r1:1.5b` ? |
| 14 | Worker-B2a | executor | Desktop | 4 GB | `deepseek-coder:1.3b` ? |
| 15 | Worker-B2b | executor | Desktop | 4 GB | `internlm2:1.8b` ? |

Each `?` means: not verified against `ollama.com/library` yet. Verification protocol is in §6.1.

### 6.1 Verification protocol (Google + Nir + Claude loop)

Claude does not have live internet here. To verify each row, Claude will hand Nir an exact Google search string. Nir pastes it into Google, pastes the AI Overview / first result back into the chat, Claude updates the row in this doc, repeat for the next row.

Example for row 1:

> **Claude tells Nir to paste into Google:** `ollama library deepseek-r1 7b tag site:ollama.com`
>
> **Nir pastes the result back.**
>
> **Claude updates row 1:** removes the `?`, locks the exact tag (e.g. `deepseek-r1:7b` confirmed, or replaces with whatever is actually there).

Run this loop 15 times before any `ollama pull` happens. The verified table replaces this provisional one.

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
- **2026-04-14 (afternoon, Linux session)** — Full rewrite by Desktop Linux Claude (Opus 4.6, on Mint 22.2 after reboot) under direct correction from Nir. Locked: Ubuntu Server 24.04 minimal on Desktop VMs, Debian 13 Trixie netinst on Laptop VMs, full 15-VM topology (1 RajaBee + 2 GiantQueens + 4 DwarfQueens + 8 Workers), CPU-only Ollama, different Chinese model per VM. Model table is PROVISIONAL pending §6.1 Google verification — Claude has no live web access and Nir does not memorise current Ollama tags, so all 15 rows must be checked against `ollama.com/library` via Google before any `ollama pull`.
