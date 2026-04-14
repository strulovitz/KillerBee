# Phase 3: Linux VM Setup for the 3-DwarfQueen Parallel Test

**Audience:** Nir + the Claude Code session that is guiding him through this (Desktop Linux Claude or Laptop Linux Claude).
**Host OS:** Linux Mint 22.2 (Desktop) or Debian 13 (Laptop). Same instructions work on both; filesystem paths and package names are identical.
**Status:** Not started as of 2026-04-14. This doc is the step-by-step plan.
**Precondition:** Phase 2 LAN test PASSED on 2026-04-11 (see `EXPERIMENT_LOG.md` Experiment 3).

---

## 1. Why this exists (Rule #1 recap)

`KillerBee/CLAUDE.md` Rule #1: if the architecture says a bee is a separate machine, it must BE a separate machine — its own OS, own IP, own processes — **or a real VM with the same properties.** No in-process fakes. No threads pretending to be distributed.

The next test on the roadmap is the **3-DwarfQueen parallel test**, which needs **at least three DwarfQueen machines running at the same time**. We only have two physical machines (Desktop + Laptop). Math is short by at least one. VMs are how the math closes.

Each physical machine running Linux can host multiple lightweight Linux VMs, each with its own IP on the LAN, each running its own Ollama + its own KillerBee bee process. Once both machines are on Linux and each has 2-3 VMs, the cluster has enough "machines" for 3-DwarfQueen (and eventually the full GiantQueen 3-level hierarchy test).

## 2. The target topology

Target for the end of Phase 3 setup (both machines, eventually):

```
Laptop (Debian 13 host, 10.0.0.1)
  |-- KillerBee website (Flask, port 8877)     [runs on host]
  |-- WaggleDance server (Flask, port 8765)    [runs on host]
  |-- RajaBee (Python, host Ollama)            [runs on host]
  |-- VM laptop-vm1 (bridged, e.g. 10.0.0.11)  [DwarfQueen + Workers]
  |-- VM laptop-vm2 (bridged, e.g. 10.0.0.12)  [DwarfQueen + Workers]

Desktop (Linux Mint 22.2 host, 10.0.0.5)
  |-- (host can run one DwarfQueen directly to save a VM)
  |-- VM desktop-vm1 (bridged, e.g. 10.0.0.21) [DwarfQueen + Workers]
  |-- VM desktop-vm2 (bridged, e.g. 10.0.0.22) [DwarfQueen + Workers]
```

Minimum for the **3-DwarfQueen parallel test** specifically: any three of those DwarfQueen rows above, each on a different OS instance with its own IP, all registering to the same KillerBee website on Laptop.

## 3. Why KVM/QEMU + virt-manager (not VirtualBox)

On Linux we recommend **KVM/QEMU with virt-manager** instead of VirtualBox, because:

1. **Native to the Linux kernel.** No third-party kernel modules. No "VirtualBox won't build on this kernel" surprises after an update.
2. **No licensing questions.** KVM is GPL.
3. **Bridged networking is straightforward** with `virt-manager` — one dropdown.
4. **Headless-friendly.** We do not need a GUI inside the guest; KVM handles that gracefully.
5. **Performance.** KVM uses hardware virtualization (VT-x/AMD-V) directly through the kernel. VirtualBox does too but with extra translation layers.

VirtualBox is a fallback if KVM has a problem on a given machine. Both are acceptable under Rule #1 because both give the VM its own kernel, IP, and processes.

## 4. Prerequisites — install on the Linux host (one-time)

**Step 4.1 — Confirm CPU virtualization is enabled in BIOS.**

Run:
```
grep -E --color 'vmx|svm' /proc/cpuinfo
```
If this returns several highlighted lines, virtualization is on. If it returns nothing, reboot into BIOS and enable Intel VT-x (Intel CPUs) or AMD-V / SVM (AMD CPUs), save, reboot back.

**Step 4.2 — Install KVM + virt-manager + bridge tools.**

On Linux Mint 22.2 / Debian 13:
```
sudo apt update
```
```
sudo apt install -y qemu-kvm libvirt-daemon-system libvirt-clients bridge-utils virtinst virt-manager
```

**Step 4.3 — Add your user to the libvirt and kvm groups.**
```
sudo usermod -aG libvirt $USER
```
```
sudo usermod -aG kvm $USER
```
Then **log out and log back in** so the group change takes effect. Confirm with `groups` — you should see `libvirt` and `kvm` in the list.

**Step 4.4 — Verify KVM is working.**
```
sudo systemctl status libvirtd
```
You should see `active (running)`. If not:
```
sudo systemctl enable --now libvirtd
```

**Step 4.5 — Install Ollama on the host too (for RajaBee and for testing).**
```
curl -fsSL https://ollama.com/install.sh | sh
```
```
ollama pull llama3.2:3b
```

Set `OLLAMA_HOST=0.0.0.0` so Ollama accepts LAN connections. Add this line to `~/.bashrc`:
```
echo 'export OLLAMA_HOST=0.0.0.0' >> ~/.bashrc
```
Then restart Ollama:
```
sudo systemctl restart ollama
```

**Step 4.6 — Install the rest of the dev stack.**
```
sudo apt install -y git python3 python3-pip python3-venv curl
```
```
pip install flask flask-login flask-wtf requests
```

**Step 4.7 — Clone all the repos (per `feedback_full_context`: full context everywhere).**
```
mkdir -p ~/Projects && cd ~/Projects
```
```
for r in HoneycombOfAI GiantHoneyBee KillerBee BeehiveOfAI WaggleDance BeeSting Honeymation MadHoney TheDistributedAIRevolution; do git clone https://github.com/strulovitz/$r.git; done
```

## 5. Create the bridged network (one-time)

By default, `libvirt` creates a NAT network called `default` on `192.168.122.x`. That network is **isolated from the LAN** — VMs on it cannot be reached from Laptop at `10.0.0.1`, which breaks the whole test. We need **bridged networking** so each VM gets an IP on the real `10.0.0.0/24` LAN.

**Step 5.1 — Identify the host's real network interface.**
```
ip -br link
```
Look for the interface that is `UP` and has the LAN MAC address. It will typically be `enp3s0`, `eno1`, `eth0`, or similar. **Write that name down** — you will use it in the next step. Call it `<IFACE>` below.

**Step 5.2 — Create the bridge with NetworkManager (Mint default) or systemd-networkd.**

Easiest on Mint / modern Debian is `nmcli`:
```
sudo nmcli connection add type bridge ifname br0 con-name br0
```
```
sudo nmcli connection add type bridge-slave ifname <IFACE> master br0
```
```
sudo nmcli connection modify br0 bridge.stp no
```
```
sudo nmcli connection up br0
```

**Warning:** this will briefly drop the host's network connection (seconds). If you are remoting in, do it from the local console.

Verify:
```
ip -br addr show br0
```
`br0` should have the host's LAN IP.

**Step 5.3 — Tell libvirt about the bridge.**

Create a file `/tmp/br0.xml` with this content (save via text editor):
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
```
```
sudo virsh net-start br0
```
```
sudo virsh net-autostart br0
```
Verify:
```
sudo virsh net-list --all
```
You should see `br0` as `active` and `autostart yes`.

## 6. Create the first VM (template)

Use a **minimal** guest — no GUI. Two good choices:

- **Debian 12 netinst** (~400 MB ISO) — familiar apt, easy Ollama install.
- **Alpine Linux standard** (~200 MB ISO) — tiniest, but musl libc means Ollama sometimes fights back. Prefer Debian unless disk is tight.

**Step 6.1 — Download the ISO.**
```
mkdir -p ~/isos && cd ~/isos
```
```
curl -L -o debian-12-netinst.iso https://cdimage.debian.org/debian-cd/current/amd64/iso-cd/debian-12.7.0-amd64-netinst.iso
```
(URL may advance — check https://www.debian.org/download for the current filename if this 404s.)

**Step 6.2 — Launch `virt-manager`.**
```
virt-manager
```
A GUI window opens. **File → New Virtual Machine.**
- **Step 1:** Local install media → Forward.
- **Step 2:** Browse → Browse Local → pick `~/isos/debian-12-netinst.iso`. Let it auto-detect OS.
- **Step 3:** Memory **2048 MiB**, CPUs **2**. (Adjust up if you have lots of RAM — more helps Ollama inference.)
- **Step 4:** Create a disk image, **15 GiB**.
- **Step 5:** Name the VM `desktop-vm1` (or `laptop-vm1` etc — use the pattern in §2). **Important:** click "Customize configuration before install" and then Forward.
- **Customization screen:** select the **NIC** entry on the left. In the dropdown, change "Network source" to **Bridge device: br0** (or select `br0` from the virtual network list). Apply. Begin Installation.

**Step 6.3 — Run the Debian installer inside the VM.**
- Language, locale, keyboard — defaults are fine.
- Hostname: same as the VM name (`desktop-vm1`).
- Create user `nir` with a memorable password.
- Disk: guided, use entire disk, single partition.
- **Software selection:** UNCHECK desktop environment. CHECK "SSH server" and "standard system utilities". That is all. No GUI.
- Install GRUB to `/dev/vda`. Reboot.

**Step 6.4 — First-boot inside the VM.**

Log in as `nir`. Confirm LAN IP:
```
ip -br addr show
```
You should see an address like `10.0.0.11/24` on the main interface (not `192.168.122.x`). If you see the 192 range, the bridge did not take — go back to §5.

From the **host**, confirm you can ping the VM:
```
ping -c 3 10.0.0.11
```

**Step 6.5 — Install Ollama + a small model in the VM.**

SSH into the VM from the host:
```
ssh nir@10.0.0.11
```
Inside the VM:
```
sudo apt update && sudo apt install -y curl python3 python3-pip git
```
```
curl -fsSL https://ollama.com/install.sh | sh
```
```
echo 'export OLLAMA_HOST=0.0.0.0' >> ~/.bashrc && source ~/.bashrc
```
```
sudo systemctl edit ollama
```
In the editor that opens, add:
```
[Service]
Environment="OLLAMA_HOST=0.0.0.0"
```
Save and exit (`Ctrl+O`, Enter, `Ctrl+X` in nano, or `:wq` in vim), then:
```
sudo systemctl restart ollama
```
Pull a tiny model (per `KillerBee/PROJECT_REPORT.md` Design Principle #5 — small models for testing):
```
ollama pull llama3.2:3b
```

**Step 6.6 — Open Ollama to the LAN from the VM.**
```
sudo ufw allow 11434/tcp 2>/dev/null || true
```
(Debian minimal often has no ufw installed — the `|| true` makes it a no-op if so. iptables is open by default on a bare Debian install.)

**Step 6.7 — Verify from the host.**

Back on the host:
```
curl http://10.0.0.11:11434/api/tags
```
You should get JSON listing `llama3.2:3b`. That means the VM is reachable from the LAN and its Ollama is answering — the VM is now a real distributed AI node for Rule #1 purposes.

## 7. Clone the template VM for the other nodes

Instead of redoing §6 for each VM, clone the first one.

From the host, with `desktop-vm1` powered off (`sudo virsh shutdown desktop-vm1`):
```
sudo virt-clone --original desktop-vm1 --name desktop-vm2 --auto-clone
```

Start the clone:
```
sudo virsh start desktop-vm2
```

Then SSH into it once to change its hostname and let DHCP give it a fresh IP:
```
ssh nir@<new-ip>
```
```
sudo hostnamectl set-hostname desktop-vm2
```
```
sudo reboot
```

Repeat for `desktop-vm3` if you want three VMs on one host. For the 3-DwarfQueen parallel test we need a total of **three DwarfQueen-capable machines across the cluster**, so one possible layout is: 1 on Laptop host + 1 on Desktop host + 1 in a single VM — minimum three. Having more VMs on each host lets us graduate to the 5- or 6-DwarfQueen test and eventually the 3-level GiantQueen hierarchy without redoing this infrastructure.

## 8. Rule #1 compliance checklist (do before declaring the test ready)

Before running any KillerBee test on this infra, confirm every item:

- [ ] Each VM has its **own IP** on `10.0.0.0/24` (verify with `ip -br addr show` inside each VM).
- [ ] Each VM runs its **own kernel** (verify with `uname -r` — should match the guest OS, not the host).
- [ ] Each VM has its **own Ollama process** (verify with `ps aux | grep ollama` inside the VM, and `curl http://<vm-ip>:11434/api/tags` from a different machine).
- [ ] Each VM can be reached from Laptop's KillerBee website host (ping + curl).
- [ ] The KillerBee website firewall on Laptop accepts connections from each VM's IP on port 8877.
- [ ] No bee process on a VM is running as a subprocess spawned from the host — each bee is a separately-launched process inside the VM's OS, logged into the KillerBee website as a distinct user.
- [ ] If any item above fails, **stop** and fix before running the test. Do not paper over it.

## 9. Running the 3-DwarfQueen parallel test

Once §8 is green, the test itself is a straight extension of Phase 2 (`PHASE2_LAN_INSTRUCTIONS.md`):

1. Laptop host: start KillerBee website (`python app.py` in `KillerBee/`).
2. Laptop host: start WaggleDance server if not already running.
3. On each DwarfQueen VM (three of them): `python dwarf_queen_client.py --server http://10.0.0.1:8877 --swarm-id 1 --username queen_<X> --password password --model llama3.2:3b` — where `<X>` is `alpha`, `bravo`, `charlie`.
4. On each Worker VM (two per DwarfQueen is the minimum for the calibration pass): `python worker_client.py --server http://10.0.0.1:8877 --swarm-id 1 --username worker_<Y> --password password --model llama3.2:3b`.
5. Laptop host: start RajaBee: `python raja_bee.py --server http://10.0.0.1:8877 --swarm-id 1 --username raja_nir --password password --model llama3.2:3b`.
6. Laptop host: submit a job via the KillerBee website UI.
7. Watch. Log. Commit results to `EXPERIMENT_LOG.md` as "Experiment 4: 3-DwarfQueen parallel test".

Expected hiccups: the KillerBee `seed_data.py` currently seeds `queen_alpha` and `queen_bravo` but not `queen_charlie`. Add a third DwarfQueen user (and additional Workers) to the seed before running this test. Commit the seed change.

## 10. Troubleshooting

- **VM gets `192.168.122.x` not `10.0.0.x`** → bridge is not wired. Check that the NIC in the VM's XML is set to `source network='br0'` or `source bridge='br0'`. Edit with `sudo virsh edit <vm-name>`.
- **Host loses network when bringing up `br0`** → `nmcli` was not the right tool for this distro's network stack. Fall back to editing `/etc/network/interfaces` or using `systemd-networkd`. Ask Nir to pause and describe the distro state before guessing.
- **`virt-manager` cannot see the user's VMs** → user is not in `libvirt` group, or used `sudo virt-manager` (which runs as root and sees a different connection). Log out/in after `usermod`, then run `virt-manager` as the normal user.
- **Ollama in the VM refuses LAN connections** → `OLLAMA_HOST=0.0.0.0` was not picked up. Check with `systemctl show ollama | grep Environment`. Use `systemctl edit ollama` (not just `.bashrc` — the service does not inherit user env).
- **Test runs but some DwarfQueen reports 0 Workers** → that VM's bee process is connecting to KillerBee but its Workers are not. Check that the Worker processes are actually alive inside that specific VM (not accidentally launched on the host).

## 11. What goes in the session handshake for this mission

When Desktop Linux Claude or Laptop Linux Claude wakes up and is told "your mission is Phase 3 VM setup," the handshake REPLY on ICQ should say, in one message:

> *"Role: <desktop-linux-claude | laptop-linux-claude>. Track: testing / Phase 3 VM setup. Repos synced. Read: FRESH_CLAUDE_START_HERE, PARALLEL_VIBING, WHEN_TO_USE_WAGGLEDANCE, LESSONS, KillerBee/PROJECT_REPORT, KillerBee/CLAUDE, KillerBee/PHASE3_LINUX_VM_SETUP. Ready to guide Nir through §4 prerequisites. Over."*

Then stop. Wait for Nir to say go.

---

## Changelog

- **2026-04-14** — Initial version written by Desktop Windows Claude (Opus 4.6) during the first parallel-vibing day, as a handoff document for the Linux Claude session that will take over the testing track after Nir reboots Desktop into Linux Mint.
