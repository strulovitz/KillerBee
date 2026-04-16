# Phase 3 Handoff — Desktop to Laptop

**For:** Laptop Linux Claude (Debian 13) doing the same VM setup on the Laptop machine.
**From:** Desktop Linux Claude (Mint 22.2), who just finished building 7 VMs on 2026-04-16.
**Reviewed and corrected by:** Laptop Windows Claude on 2026-04-16 evening.
**Written as if you are smart but have never seen my machine.**

---

## ⚠️ CRITICAL WARNING — READ THIS FIRST

**Desktop Claude built all 7 VMs using Ubuntu Server 24.04.** That was correct for Desktop. But Nir specified — TWICE — that Laptop VMs must use **Debian 13 Trixie netinst**, NOT Ubuntu. See `PHASE3_LINUX_VM_SETUP.md` line 578: *"Locked: Ubuntu Server 24.04 minimal on Desktop VMs, Debian 13 Trixie netinst on Laptop VMs."*

**This means MOST of this handoff document will NOT work for you directly.** Specifically:

**What DOES NOT apply to you (Ubuntu-specific):**
- The autoinstall process (Ubuntu cloud-init/autoinstall). Debian uses preseed or d-i, completely different.
- The CIDATA seed ISO format (Ubuntu-specific cloud-init).
- The `--location` + `--extra-args autoinstall ds=nocloud` virt-install flags (Ubuntu autoinstall-specific).
- Trap 1 (autoinstall 5-min delay) — different installer, different behavior.
- Trap 2 (`shutdown: poweroff` in user-data) — Debian doesn't use this format.
- Trap 3 (`late-commands` silently skipped) — Debian preseed has different mechanisms.
- Trap 4 (autoinstall unreliable ~50%) — might not apply to Debian's installer.
- Trap 6 (Israeli apt mirror `il.archive.ubuntu.com`) — Debian uses `deb.debian.org`, different mirrors.
- The `scripts/autoinstall_one.sh` script — Ubuntu-specific, will not work on Debian ISO.

**What DOES apply to you (OS-independent):**
- The CLONE strategy: build ONE working VM, clone the rest. This works regardless of guest OS.
- The qemu-nbd mount trick for changing hostname/machine-id on clones.
- The `virt-install --import` command for defining cloned VMs (works with any qcow2).
- libvirt pool setup, bridge (br0) setup, SSH key generation — all host-level, OS-independent.
- Ollama installation (same `curl | sh` script works on Debian).
- Ollama bind to 0.0.0.0 (same systemd override).
- whisper.cpp compilation (same on Debian — needs build-essential, cmake, git).
- Python venv + pip packages (same on Debian).
- Model pulls via Ollama (same).
- Trap 5 (cloud-init 60s wait) — Debian might not have cloud-init at all, so this may not apply.
- Trap 7 (qwen2.5vl:7b needs 12 GB RAM) — model-level, OS-independent.
- Trap 8 (PNG not JPG for Ollama vision) — model-level, OS-independent.
- Trap 9 (Moonshine is dead, use Whisper) — model-level, OS-independent.
- Trap 10 (sudoers for host user) — same concept, same commands on Debian.

**Your approach for Debian 13:**
1. Download Debian 13 Trixie netinst ISO
2. Build ONE VM manually or via preseed (NOT autoinstall — that's Ubuntu)
3. Inside the VM: install openssh-server, set up user nir with SSH key, configure sudoers
4. Shut it down
5. CLONE it for the remaining 7 VMs using the qemu-nbd trick from this doc
6. Post-install (Ollama, models, whisper.cpp, Python) is IDENTICAL to Desktop — follow Phases C and D below

**If you get stuck on the Debian installer:** ask Nir. Do NOT improvise a switch to Ubuntu. Nir chose Debian for a reason and has said it twice.

---

## What Was Done on Desktop (your roadmap)

Built 7 KillerBee VMs on a Linux Mint 22.2 host (i9-13900KF, 62 GiB RAM, 1.5 TB free disk, no GPU). Each VM runs Ubuntu 24.04.4 Server with Ollama (3 models per VM) and whisper.cpp for STT. All models are CPU-only.

---

## Step-by-Step: What I Actually Did

### Phase A: Host Preparation (already done on Desktop, you need to do on Laptop)

1. **libvirt pool** — created a storage pool on a large partition:
   ```bash
   virsh pool-define-as killerbee dir --target /path/to/big/partition
   virsh pool-build killerbee && virsh pool-start killerbee && virsh pool-autostart killerbee
   ```

2. **Bridge interface** — br0 with host IP on the LAN. VMs attach to this bridge and get DHCP from the router. This is the critical networking piece.

3. **SSH key** — ed25519 key pair for passwordless SSH into VMs:
   ```bash
   ssh-keygen -t ed25519 -f ~/.ssh/phase3_ed25519 -N ""
   ```

4. **Ubuntu 24.04.4 Server ISO** — downloaded to the pool's isos/ directory.

5. **Autoinstall seed** — `user-data` (cloud-config YAML with autoinstall directives) + `meta-data`. Template at `/home/nir/vm/desktop-template/seed/`.

### Phase B: Build the First VM via Autoinstall

This is where most of the pain was. **Read carefully.**

6. **autoinstall_one.sh** creates a VM from the ISO using `virt-install --location` with a CIDATA seed ISO:
   ```bash
   virt-install \
     --name <vm-name> --memory <MB> --vcpus <N> \
     --cpu host-passthrough --os-variant ubuntu24.04 \
     --disk path=<qcow2>,format=qcow2,bus=virtio,size=<GB> \
     --disk path=<seed.iso>,device=cdrom \
     --location <ubuntu-iso>,kernel=casper/vmlinuz,initrd=casper/initrd \
     --extra-args 'autoinstall ds=nocloud console=ttyS0,115200n8 serial' \
     --network bridge=br0,model=virtio \
     --graphics none --noautoconsole --noreboot --wait -1
   ```

### What Worked First Try
- The `virt-install` command itself
- The CIDATA seed.iso format (genisoimage with CIDATA label)
- The kernel args `autoinstall ds=nocloud console=ttyS0,115200n8 serial`
- The bridge networking (VMs get DHCP from the router)

### What Broke and How I Fixed It

**TRAP 1: Autoinstall has a ~5 minute startup delay.**
Disk stays at ~12MB for 5-12 minutes before the installer begins writing. This looks exactly like a stuck install. IT IS NOT STUCK. Wait at least 15 minutes before concluding something is wrong. I killed 2 install attempts thinking they were stuck.

**TRAP 2: `shutdown: poweroff` in user-data does NOT work.**
Ubuntu 24.04 autoinstall finishes but does not power off the VM. The `--wait -1` flag causes virt-install to hang forever. Fix: poll disk allocation, detect flat writes for 5+ minutes after 3+ GB written, then send `virsh shutdown <vm>` from the host.

**TRAP 3: `late-commands` in user-data are silently skipped.**
The sudoers.d file and any other late-commands just don't execute. Fix: after the VM shuts down (post-install), mount the qcow2 via qemu-nbd and inject the sudoers file manually:
```bash
sudo modprobe nbd max_part=8
sudo qemu-nbd --connect=/dev/nbd0 /path/to/vm.qcow2
sleep 2
sudo mount /dev/nbd0p2 /tmp/vm-mount
echo "nir ALL=(ALL) NOPASSWD: ALL" | sudo tee /tmp/vm-mount/etc/sudoers.d/90-nir
sudo chmod 0440 /tmp/vm-mount/etc/sudoers.d/90-nir
sudo umount /tmp/vm-mount
sudo qemu-nbd --disconnect /dev/nbd0
```

**TRAP 4: Autoinstall config application is UNRELIABLE (~50% success rate).**
giantqueen-b got our config (correct hostname, SSH key, packages). dwarfqueen-b1 and b2 got DEFAULT config (hostname "localhost", no SSH server, no SSH key). Same script, same seed, different results. I never found the root cause.

**THE FIX THAT SAVED EVERYTHING: Clone instead of autoinstall.**
After building ONE working VM (giantqueen-b), I cloned it for all remaining VMs:
```bash
sudo cp /path/to/giantqueen-b.qcow2 /path/to/new-vm.qcow2
sudo chown libvirt-qemu:kvm /path/to/new-vm.qcow2
sudo qemu-nbd --connect=/dev/nbd0 /path/to/new-vm.qcow2
sleep 2
sudo mount /dev/nbd0p2 /tmp/vm-mount
echo "new-hostname" | sudo tee /tmp/vm-mount/etc/hostname
sudo sed -i "s/old-hostname/new-hostname/g" /tmp/vm-mount/etc/hosts
sudo rm -f /tmp/vm-mount/etc/machine-id  # force regeneration
sudo touch /tmp/vm-mount/etc/machine-id
sudo umount /tmp/vm-mount
sudo qemu-nbd --disconnect /dev/nbd0
# Define the VM:
sudo virt-install --name new-vm --memory <MB> --vcpus <N> \
  --cpu host-passthrough --os-variant ubuntu24.04 \
  --disk path=/path/to/new-vm.qcow2,format=qcow2,bus=virtio \
  --network bridge=br0,model=virtio \
  --graphics none --noautoconsole --import --noreboot
```
6 VMs cloned in ~15 minutes total vs. 30+ min each for autoinstall. **I strongly recommend this approach.**

**TRAP 5: VMs from clones need ~60 seconds for first-boot cloud-init before SSH works.**
After `virsh start`, the VM gets an IP quickly but SSH refuses connections for about a minute while cloud-init runs. Wait for it.

**TRAP 6: Israeli apt mirror is unreliable.**
`il.archive.ubuntu.com` has frequent sync failures. Change to `de.archive.ubuntu.com` (Germany) on every VM:
```bash
sudo find /etc/apt/sources.list.d/ -name "*.sources" -exec sed -i "s|il.archive.ubuntu.com|de.archive.ubuntu.com|g" {} \;
```

**TRAP 7: qwen2.5vl:7b vision model needs more RAM than expected.**
The plan allocated 8 GB for giantqueen-b, but the vision model needs 12.5 GiB. I bumped it to 12 GB. You will need to account for this on Laptop too.

**TRAP 8: Test images must be PNG not JPG for Ollama vision.**
JPG gives "unknown format" error. Use PNG.

**TRAP 9: Moonshine ONNX does not exist as a pip package.**
`moonshine-onnx` is not on PyPI. `useful-moonshine` exists but requires tensorflow (too heavy for 4 GB workers). Workers use Whisper tiny via whisper.cpp instead (SILVER fallback from the STT plan).

**TRAP 10: sudoers for the host user.**
Claude Code cannot run `sudo` commands that need a password. On Desktop, Nir temporarily added:
```
echo "nir ALL=(ALL) NOPASSWD: ALL" | sudo tee /etc/sudoers.d/99-nir-temp
```
Remove after Phase 3 is done: `sudo rm /etc/sudoers.d/99-nir-temp`

### Phase C: Post-Install on Each VM

After each VM is booted and SSH-accessible:

7. **Install Ollama:**
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ```

8. **Bind Ollama to all interfaces:**
   ```bash
   sudo mkdir -p /etc/systemd/system/ollama.service.d
   printf "[Service]\nEnvironment=OLLAMA_HOST=0.0.0.0:11434\n" | sudo tee /etc/systemd/system/ollama.service.d/override.conf
   sudo systemctl daemon-reload && sudo systemctl restart ollama
   ```

9. **Pull the tier's 3 models** (see model table below).

10. **Verify from host:**
    ```bash
    curl -s http://<vm-ip>:11434/api/tags
    ```

### Phase D: STT Provisioning

11. On each VM, install system packages:
    ```bash
    sudo apt-get install -y ffmpeg build-essential cmake git python3 python3-pip python3-venv
    ```

12. Create venv + install Python packages:
    ```bash
    python3 -m venv /opt/killerbee/venv
    source /opt/killerbee/venv/bin/activate
    pip install numpy soundfile Pillow pytest requests
    ```

13. Compile whisper.cpp (ALL VMs, all tiers):
    ```bash
    mkdir -p /opt/killerbee/src && cd /opt/killerbee/src
    git clone --depth 1 https://github.com/ggerganov/whisper.cpp.git
    cd whisper.cpp && make -j"$(nproc)"
    ```
    Binary ends up at `build/bin/whisper-cli` (NOT `main` — newer build system).

14. Download the tier's STT model:
    ```bash
    cd /opt/killerbee/src/whisper.cpp
    bash ./models/download-ggml-model.sh <size>  # tiny, small, medium, large-v3-turbo
    ```

15. Smoke test:
    ```bash
    ./build/bin/whisper-cli -m models/ggml-<size>.bin -f samples/jfk.wav --no-timestamps -l en
    ```
    Should output: "And so my fellow Americans ask not what your country can do for you..."

---

## Scripts Used (in order)

All in the KillerBee repo:

1. `scripts/autoinstall_one.sh` — builds ONE VM from ISO (used only for the first VM)
2. `/tmp/clone_vm.sh` — clones giantqueen-b for remaining VMs (not in repo, see clone commands above)
3. `scripts/full_cycle_one.sh` — post-install: boot, find IP, swap check, Ollama install+bind+verify
4. `PHASE3_PROVISION_VM.sh` — STT provisioning (apt, venv, whisper.cpp, model download)
5. `scripts/helpers/*.py` — slice_audio, slice_image, run_stt, run_reasoner, integrate_children

---

## Differences for Laptop

| Aspect | Desktop (done) | Laptop (you) |
|---|---|---|
| OS | Linux Mint 22.2 Cinnamon | Debian 13 |
| CPU | i9-13900KF (32 threads) | Check `nproc` |
| RAM | 62 GiB | Check `free -h` |
| GPU | RTX 4070 Ti (unused, CPU-only) | RTX 5090 (unused, CPU-only) |
| Role | 7 VMs: GiantQueen-B + 2 DwarfQueens-B + 4 Workers-B | 8 VMs: RajaBee + GiantQueen-A + 2 DwarfQueens-A + 4 Workers-A |
| libvirt | Installed via apt | May need `apt install qemu-kvm libvirt-daemon-system virt-manager` |
| Bridge | br0 on Mint (NetworkManager) | May need different setup on Debian |
| Package manager | apt (same) | apt (same) |
| Python | 3.12 | Check `python3 --version` |

### Laptop VM table (8 VMs — from PHASE3_LINUX_VM_SETUP.md topology)

| VM | RAM | vCPU | Dense | MoE | Vision | STT |
|---|---|---|---|---|---|---|
| rajabee | 18 GB | 6 | qwen3.5:27b | gemma4:26b-moe | mistral-small-3.1:24b | Cohere Transcribe (HF Transformers CPU) |
| giantqueen-a | 12 GB* | 6 | qwen3:14b | granite3.1-moe:3b | qwen3-vl:8b | whisper large-v3-turbo |
| dwarfqueen-a1 | 6 GB | 4 | qwen3:8b | granite3.1-moe:3b | llama3.2-vision:11b | whisper small |
| dwarfqueen-a2 | 6 GB | 4 | qwen3:8b | granite3.1-moe:3b | llama3.2-vision:11b | whisper small |
| worker-a1 | 4 GB | 2 | qwen3:1.7b | granite3.1-moe:1b | qwen3.5:0.8b | whisper tiny |
| worker-a2 | 4 GB | 2 | qwen3:1.7b | granite3.1-moe:1b | qwen3.5:0.8b | whisper tiny |
| worker-a3 | 4 GB | 2 | qwen3:1.7b | granite3.1-moe:1b | qwen3.5:0.8b | whisper tiny |
| worker-a4 | 4 GB | 2 | qwen3:1.7b | granite3.1-moe:1b | qwen3.5:0.8b | whisper tiny |

*12 GB not 8 GB — Desktop discovered qwen2.5vl:7b needs 12.5 GiB. Any VM running a 7B+ vision model needs 12 GB.

**Total Laptop guest RAM:** 18+12+6+6+4+4+4+4 = 58 GB on a 64 GB host. Tight but fits (~6 GB host headroom). Verify with `free -h` after all 8 VMs are running.

**Model tags for Laptop are from PHASE3_LINUX_VM_SETUP.md sections 11-12.** Verify each tag against the live Ollama library before pulling — some of these were selected weeks ago and tags can change.

### Key difference: RajaBee tier
The Laptop hosts the RajaBee, which uses:
- **Cohere Transcribe 03-2026** for STT (2B params, needs `transformers` + `torch` CPU)
- A larger text reasoner (the biggest in the hierarchy)
- This means `pip install torch --index-url https://download.pytorch.org/whl/cpu` + `pip install transformers` on the RajaBee VM
- The Cohere model downloads from HuggingFace: `snapshot_download('CohereLabs/cohere-transcribe-03-2026')`

### Debian-specific things to watch for
- `qemu-nbd` might be in a different package (`qemu-utils`)
- `genisoimage` might need to be installed separately
- Network bridge setup on Debian uses `/etc/network/interfaces` not NetworkManager
- `wmctrl` for WaggleDance ICQ might need `apt install wmctrl`

---

## Model Table (Desktop — for reference)

| VM | RAM | vCPU | Dense | MoE | Vision | STT |
|---|---|---|---|---|---|---|
| giantqueen-b | 12 GB* | 6 | qwen3:8b | granite3.1-moe:3b | qwen2.5vl:7b | whisper large-v3-turbo |
| dwarfqueen-b1 | 6 GB | 4 | phi4-mini:3.8b | granite3.1-moe:3b | gemma3:4b | whisper small |
| dwarfqueen-b2 | 6 GB | 4 | phi4-mini:3.8b | granite3.1-moe:3b | gemma3:4b | whisper small |
| worker-b1..b4 | 4 GB | 2 | qwen3:1.7b | granite3.1-moe:1b | qwen3.5:0.8b | whisper tiny |

*Originally 8 GB, bumped to 12 GB because qwen2.5vl:7b needs 12.5 GiB for vision.

---

## Summary of Gotchas (quick reference)

1. Autoinstall takes 15-30 min, first 5-12 min looks stuck (12MB disk) — WAIT
2. `shutdown: poweroff` doesn't work — use `virsh shutdown` from host
3. `late-commands` silently skipped — inject sudoers via qemu-nbd
4. Autoinstall unreliable (~50%) — build ONE VM, CLONE the rest
5. Cloud-init first boot needs ~60s before SSH works
6. Never use il.archive.ubuntu.com — use de.archive.ubuntu.com
7. Vision model qwen2.5vl:7b needs 12 GB RAM not 8 GB
8. Test images must be PNG not JPG for Ollama
9. Moonshine doesn't work (needs tensorflow) — use Whisper tiny
10. Host sudo: add temporary NOPASSWD rule for the user

---

*Written by Desktop Claude on 2026-04-16. Edit in place. Git is the time machine.*
