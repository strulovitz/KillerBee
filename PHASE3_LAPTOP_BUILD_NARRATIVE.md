# How We Built The Laptop Half Of Phase 3

**Date:** 2026-04-17 (single day) into the small hours of 2026-04-18.
**Told by:** Opus 4.7 xhigh, Laptop Linux session, to Nir, with Desktop Windows Claude on the other end of the WaggleDance ICQ bridge.
**Canonical source files:** `PHASE3_LAPTOP_BUILD_LOG.md`, `PHASE3_RAM_MEASUREMENT_LOG.md`, `PHASE3_LAPTOP_ROSTER_LOCKED.md`, `PHASE3_VISION_SWAP_GIANTQUEEN.md`, `PHASE3_DEBIAN13_PRESEED.cfg`.

---

## 0. What this chapter is

This is the story of a single day in which eight virtual machines went from not-existing to fully-provisioned members of a 15-VM distributed AI hierarchy, written honestly. It includes the mistakes.

Read it as both a how-to and a cautionary tale. The raw operational log is in `PHASE3_LAPTOP_BUILD_LOG.md`. This file is the narrative layer on top of that, because a book chapter needs arc and reflection, not just commands.

---

## 1. The mission

Nir wanted eight virtual machines on his Laptop host, each one a standalone Debian 13 box with a specific LLM loadout and a specific role in the KillerBee hierarchy: one RajaBee at the top, one GiantQueen below it, two DwarfQueens below that, and four Workers at the bottom. Together with seven existing VMs on his Desktop machine, this would form a 15-VM cluster — the smallest non-trivial topology that exercises every layer of his hierarchy design.

Each VM would run:
- A dense text model (for reasoning).
- A Mixture-of-Experts model (for cheaper reasoning-at-scale).
- A vision-language model (for images).
- Whisper.cpp for speech-to-text.

Bigger VMs at the top would run bigger models. Smaller VMs at the bottom would run smaller ones. The exact picks were locked in `PHASE3_LAPTOP_ROSTER_LOCKED.md`.

One constraint mattered more than any other: **all inference is CPU-only**. No GPU passthrough. The RTX 5090 inside the Laptop host stays on the host for other work. The VMs see no GPU, ever. Nir's reason, stated back in April: passthrough monopolizes the GPU for one VM and scales to nothing; we want fifteen real separate machines talking over a real network.

---

## 2. The morning: four measurement sessions

Before any VM could be built, we had to know which vision model to put on the top tier. Yesterday (April 16) Desktop Claude built seven VMs on the Desktop machine and picked vision models using a formula: "RAM loaded equals roughly params times 0.6 GB". That formula is accurate for dense text models. It is catastrophically wrong for vision-language models, which carry a separate image encoder and a large KV cache for image tokens.

The proof: one of Desktop's VMs, `giantqueen-b`, was built with 12 GB of VM RAM to hold `qwen2.5vl:7b`. The formula said the model would need about 4.5 GB loaded. Reality: 12.5 GiB loaded. That VM had been running with its vision model spilling 0.5 GB into its own swap file every time vision inference ran. It worked, but it was fragile.

So we measured. The rule: pull the model on the Laptop host, force CPU-only inference with `num_gpu: 0`, record `free -h` delta and `ollama ps` claimed size, then delete the model. Each measurement ended with a commit to GitHub confirming the test model was gone from `ollama list`. This commitment was not optional. I promised Nir at the start of each session to delete the models after measurement, and a public record on GitHub kept that promise honest.

Four sessions happened, in order:

**Session 1** measured three vision candidates simultaneously for the 12 GB GiantQueen tier: `minicpm-v:8b` (real loaded ~5.6 GB), `qwen3-vl:8b` (6.1 GB), and `gemma3:12b` (10.1 GB). Conclusions: `qwen3-vl:8b` fit the 12 GB apartment most comfortably AND gave the best output on a test image, counting every element correctly. `gemma3:12b` overflowed. `minicpm-v:8b` fit but used less of the apartment.

**Session 2** measured `qwen3:14b` (the dense text model for RajaBee): loaded to ~9 GB. Cleanly fits a 16 GB VM with 4.5 GB headroom. The old `params × 0.6 GB` formula predicted 8.4 GB, which was close — the formula is reliable for dense text. The lesson: measure vision, trust the formula for text.

**Session 3** tested `gemma4:e4b`, Google's April-2026 "effective 4B" unified multimodal model. Benchmark claim: 52.6% MMMU Pro. We had to upgrade Ollama on the host from 0.12.10 to 0.21.0 just to pull it. Result: 10.2 GB loaded with a 32K default context window. Fits 16 GB VM but overflows 12 GB GiantQueen. Also inferenced 3× slower on CPU than `qwen3-vl:8b` and hallucinated an extra text block on the test image. Rejected.

**Session 4** tested `qwen3.5:9b`, Alibaba's brand-new unified vision-language model (no `-vl` suffix — vision is baked in via early-fusion training, not bolted on). Benchmark claim: 69.2% MMMU Pro, against `qwen3-vl:8b`'s 56.6%. That is a 12.6-point jump, which is huge for two models in the same size class. Result: 8.1 GB loaded in real RAM, 9.6 GB claimed by ollama ps (the 32K context buffer inflates the claimed number). Fits 16 GB RajaBee VM comfortably (5.4 GB headroom). Does NOT safely fit 12 GB GiantQueen VM (would run ~1.4 GB headroom at best, possibly overflow by 0.1 GB by the conservative metric — and we had literally spent that morning removing that exact failure mode from Desktop).

Decision: RajaBee gets `qwen3.5:9b`, GiantQueens (both Desktop and Laptop) keep `qwen3-vl:8b`.

Total tests this morning: 8 models pulled, measured, deleted. 8 GitHub commits keeping the promise. Zero models left behind.

---

## 3. The Desktop fix

Before starting any new work on Laptop, we had to fix Desktop's `giantqueen-b` — the swap-spilling vision model. That VM was on the Desktop machine, which was still on Linux Mint at the start of the day but about to reboot into Windows for video work. So: write instructions, commit them, send Desktop Linux Claude over the ICQ bridge to execute, sign off before the Windows reboot.

The fix was one VM, one model. Remove `qwen2.5vl:7b` from `giantqueen-b`. Pull `qwen3-vl:8b` in its place (we already knew from Session 1 that it fit). Test with a PNG. Update the status file.

Desktop Linux Claude did the swap. Reported back: 6.3 GiB loaded (matching our Laptop measurement to within 3%), zero swap spill during load (down from 0.5 GB), and a detailed vision description that correctly identified black outlines, colors, and text placement. Commit `045b4cf`.

One of the two GiantQueens was now healthy. The other (Laptop's `giantqueen-a`) didn't exist yet.

---

## 4. The RajaBee roster: three answers in one day

Before this day, the Laptop roster file had RajaBee's vision as `qwen3-vl:8b` (to match both GiantQueens). Then, because Nir pointed out RajaBee has a bigger apartment (16 GB VM vs 12 GB), we upgraded to `gemma3:12b` to actually use that capacity. Then, because Nir asked "do we actually know which one is better quality?", we pulled benchmark numbers and learned that `qwen3-vl:8b` beats `gemma3:12b` on MMMU Pro by 6 points despite being smaller. So we almost went back.

Then Nir asked "is there a bigger model from the same family that fits AND is better?" We searched. The Qwen vision family has an inconvenient gap between 8b and 30b — no 14b or 20b. BUT: a brand-new unified family called `qwen3.5` (no `-vl` suffix) did have a 9b variant with vision baked in and a much higher MMMU Pro benchmark. We verified the model page directly on Ollama (not just the tags page — Google had already hallucinated model names twice that day), confirmed it was multimodal via the "Text, Image" marker, ran Session 4 to measure it, and locked RajaBee on `qwen3.5:9b`.

Three answers, one day, all recorded in the roster-locked file. The Git history preserves the full arc. A reviewer can see exactly why the final pick is what it is.

---

## 5. The Laptop build — prerequisites

With the roster locked, the Laptop build could begin. Before any VM could run, the host needed:

1. **KVM stack installed.** `qemu-kvm`, `libvirt-daemon-system`, `libvirt-clients`, `bridge-utils`, `virtinst`, `virt-manager`, `qemu-utils`, `genisoimage`. On Debian 13 in April 2026, this ran into a stale apt package-index problem: the index referenced `libcapstone5 5.0.6-1` but the real pool only had `5.0.7-1`. Fix: `sudo apt-get clean && sudo rm -rf /var/lib/apt/lists/* && apt-get update`, then `apt --fix-broken install` to finish the install cleanly.

2. **User `nir` added to `libvirt` and `kvm` groups.**

3. **libvirtd enabled and running.**

4. **Directories:** `/home/killerbee-images/isos/` as the libvirt storage pool target, `~/vm/laptop-template/seed/` to hold the preseed file.

5. **SSH key pair:** `~/.ssh/phase3_ed25519` (ed25519, passphrase-less, purpose-tagged in the comment).

6. **Debian 13 netinst ISO:** `debian-13.4.0-amd64-netinst.iso`, 790 MB. Took two tries: the first curl asked for `debian-13.0.0-amd64-netinst.iso` which returned a 200 but zero bytes (silent redirect / nonexistent filename). The real current version on `cdimage.debian.org/debian-cd/current/` was `debian-13.4.0`.

7. **libvirt pool `killerbee`** defined on `/home/killerbee-images/`, started, autostart enabled.

8. **The `br0` bridge.** This one gets its own section (next).

9. **NOPASSWD sudo.** Earlier in the day, to do autonomous build work without asking Nir for his password for every `sudo` call, I asked him to paste one command in a regular terminal: `echo "nir ALL=(ALL) NOPASSWD: ALL" | sudo tee /etc/sudoers.d/99-nir-temp && sudo chmod 0440 /etc/sudoers.d/99-nir-temp`. That rule stays in `/etc/sudoers.d/` until he removes it. He can revoke with `sudo rm /etc/sudoers.d/99-nir-temp`.

10. **The Debian 13 preseed file.** Ubuntu's autoinstall format doesn't apply to Debian; d-i uses preseed. Wrote a fresh preseed at `~/vm/laptop-template/seed/preseed.cfg`, canonical copy at `PHASE3_DEBIAN13_PRESEED.cfg` in the repo. Key sections:
    - Locale en_US.UTF-8, keyboard US, time zone Asia/Jerusalem.
    - Auto-choose first NIC, DHCP.
    - User `nir` with a placeholder password that gets neutered later because SSH login is key-only.
    - Root login disabled.
    - Atomic partitioning on `/dev/vda`.
    - Install `openssh-server curl python3 python3-pip python3-venv git ca-certificates sudo wget`.
    - `late_command` injects the phase3 SSH pubkey into `/home/nir/.ssh/authorized_keys`, writes `/etc/sudoers.d/90-nir` with `NOPASSWD: ALL`, disables password SSH, enables ssh.service, enables pubkey auth.

---

## 6. The `br0` bridge — careful, atomic, and with fallback

A bridged network was mandatory per the plan: VMs must get real `10.0.0.x` IPs on the same LAN as the host, so they can reach the KillerBee website and WaggleDance ICQ, and so VMs on the Desktop machine can reach VMs on the Laptop machine and vice versa. The default libvirt NAT network (`192.168.122.x`) would isolate the VMs and break the test.

The Laptop host's primary network interface (`enp129s0`) was being managed by classic Debian ifupdown, not NetworkManager (NetworkManager saw it as "unmanaged"). So `nmcli` wasn't the right tool. The right tool was `/etc/network/interfaces` with `bridge_ports`.

Before editing, I saved a backup: `sudo cp /etc/network/interfaces /etc/network/interfaces.pre-br0.backup`. That backup is still there. It is the rollback path if anything in this section ever breaks.

The new config:
- `enp129s0` in `inet manual` mode (no IP).
- `br0` in `inet dhcp` with `bridge_ports enp129s0`, `bridge_stp off`, `bridge_fd 0`, and `hwaddress ether c8:53:09:be:bf:3a` (the MAC of `enp129s0`, cloned onto the bridge so the LAN router hands back the same DHCP lease, `10.0.0.8`).

`sudo systemctl restart networking` was the switch. Networking blipped for about five seconds, then `br0` came up with `10.0.0.8/24` as expected. `libvirt` got a matching bridge-forwarding network definition (`virsh net-define` / `net-start` / `net-autostart` with `forward mode=bridge`).

One small mess needed cleanup: after the bridge restart, `enp129s0` still had its old IP as a stale entry. `sudo ip addr flush dev enp129s0` cleared it. No damage.

The bridge fix gets its own story later, because it wasn't actually done yet — there was a dhcpcd daemon still running on `enp129s0` that would keep re-adding stale routes after every reboot. We didn't discover that until we tried to SSH the first clone.

---

## 7. The template VM — five separate mistakes, one working Debian

With prerequisites in place, I ran `virt-install` with the preseed injected into the initrd. The command used `--location` pointing at the Debian ISO's `install.amd/vmlinuz` and `install.amd/initrd.gz`, `--initrd-inject` with the preseed, and `--extra-args "auto=true priority=critical preseed/file=/preseed.cfg interface=auto locale=en_US console=ttyS0,115200n8 serial"`.

The install completed in about five minutes. Short by Ubuntu autoinstall standards. virt-install returned 0 and the VM shut itself off, as `--noreboot` tells it to.

Then the template refused to come online.

Five distinct things went wrong, in this order:

**Mistake 1: the installed network config didn't match the kernel's actual interface name.** Debian's installer wrote `allow-hotplug enp1s0` to `/etc/network/interfaces`. `allow-hotplug` means "come up when a hotplug event fires" — which does not fire reliably on virtio NICs at boot. So networking.service started and exited without bringing any interface up.

**Mistake 2: the kernel wasn't sending output to the serial console.** Without `console=ttyS0,115200n8` in `GRUB_CMDLINE_LINUX`, the kernel output went to a graphical console that didn't exist (graphics=none). I couldn't see what the system was doing after GRUB handed off.

**Mistake 3: the serial console via `virsh console` needed a controlling TTY I didn't have.** Claude Code runs without a TTY. So even when the output WAS on serial, I couldn't attach.

**Mistake 4: the VM's IPv4 DHCP wasn't firing but IPv6 SLAAC was.** Once I redirected serial to a file by editing the VM XML, I could see the kernel boot to a login prompt. I also saw DHCPv6 requests on `vnet*` (the VM's tap interface on the host side) but no DHCPv4. SLAAC derived a public IPv6 from the VM's MAC automatically — the kernel does this without any userspace config.

**Mistake 5: the systemd predictable-naming interface name isn't always `enp1s0`.** Even after fixing `/etc/network/interfaces`, the interface name might differ.

The five fixes, combined:

- Mount the template qcow2 via `qemu-nbd` with the VM shut off.
- In `/etc/default/grub` and the existing `/boot/grub/grub.cfg`, add `net.ifnames=0 biosdevname=0 console=ttyS0,115200n8 console=tty0` to the kernel command line. This forces the old-school `eth0` naming AND sends kernel output to serial.
- Rewrite `/etc/network/interfaces` with a single `auto eth0 / iface eth0 inet dhcp` entry.
- Edit the VM's libvirt XML to redirect the serial char device to a file at `/tmp/laptop-template-console.log` so I can `tail` it from the host.
- Boot. SSH in via the IPv6 link-local address (derived from the VM's MAC via EUI-64) since IPv4 wasn't working yet. Verify that with `net.ifnames=0`, the interface is now `eth0` and DHCP is actually running.

At that point, the VM had IPv4 via DHCP (`10.0.0.12`), SSH worked with the phase3 key, sudo NOPASSWD worked, and all the preinstalled packages (curl, python3, git, pip3) were there. Clean shutdown. The template was done.

Total time for "Debian installs, then takes an hour of debugging": about 75 minutes.

---

## 8. The IPv6-link-local discovery trick

Because we're using bridged networking (not libvirt's NAT), libvirt has no visibility into which IP the LAN router assigned to a VM. `virsh net-dhcp-leases br0` is empty. The router is the source of truth and it doesn't publish a listing over the bridge.

The trick: IPv6 link-local (`fe80::/10`) is auto-configured on every up interface using EUI-64 from the MAC. You can compute the link-local address of any VM purely from its virtio MAC:

1. `sudo virsh domiflist <vm> | awk '/bridge/ {print $NF}'` gives you the MAC.
2. Flip the second bit of the first byte (`52:` XOR `0x02` = `50:`).
3. Insert `ff:fe` in the middle.
4. Prepend `fe80::`.

So MAC `52:54:00:e1:a5:1b` becomes `fe80::5054:ff:fee1:a51b`.

SSH with `ssh -6 nir@fe80::5054:ff:fee1:a51b%br0` (the `%br0` tells the kernel which interface scope the link-local belongs to). Once logged in, `ip -br addr show eth0` reveals the IPv4 lease the router gave.

This trick became the discovery method for all eight clones.

---

## 9. The clone — eight VMs in about five minutes

With the template working, cloning was mostly mechanical. For each of the eight target VMs (rajabee, giantqueen-a, two dwarfqueens, four workers):

1. `sudo cp --reflink=auto /home/killerbee-images/laptop-template.qcow2 /home/killerbee-images/<vm>.qcow2`.
2. `sudo chown libvirt-qemu:kvm <vm>.qcow2`.
3. Mount via `qemu-nbd --connect=/dev/nbd0 <vm>.qcow2`.
4. Write the new hostname to `/etc/hostname`, rewrite `/etc/hosts`, truncate `/etc/machine-id` (so systemd regenerates a unique one on first boot) and the dbus equivalent.
5. Unmount, disconnect NBD.
6. `virt-install --import --name <vm> --memory <tier-RAM> --vcpus <tier-vcpus> --disk path=<vm>.qcow2,format=qcow2,bus=virtio --network bridge=br0,model=virtio --graphics none --noautoconsole --noreboot`.
7. `virsh start <vm>`.

The first attempt went wrong mid-script on `rajabee` — my script had a set-minus-e behavior hitting a non-zero SSH check that aborted the loop without printing "clone complete". The template was fine, rajabee was fine, just the script bailed. Fix: I copy-pasted the loop into a bash one-liner that didn't have the bail-out behavior and re-ran it for the remaining seven VMs. All eight defined cleanly.

For discovery I used the IPv6 link-local trick on each MAC. Every VM came up with a unique IPv4 lease, each with a unique machine-id, each SSH-able with the phase3 key. Took about eight minutes from `cp` of the first clone to SSH-verified last clone.

---

## 10. The dhcpcd skirmish — an invisible fight over 10.0.0.8

After clones came up, I expected SSH via IPv4 to work directly. It did not. `ssh nir@10.0.0.14` returned "No route to host", even though `ssh -6 nir@fe80::...%br0` to the same VM worked fine.

The route-get trace told the story:

```
$ ip route get 10.0.0.14
10.0.0.14 dev enp129s0 src 10.0.0.8
```

The kernel was routing to `10.0.0.14` out of `enp129s0` (the physical interface, now a bridge slave) instead of `br0` (the bridge). That makes no sense for a bridge slave — frames put on `enp129s0` go to the physical port, not into the bridge logic. So the ARP requests for the VM's IP went out the wire to the LAN, the LAN router looked puzzled, and no VM answered.

Why was the kernel choosing `enp129s0`? Because there were stale routes:

```
10.0.0.0/24 dev enp129s0 proto dhcp scope link src 10.0.0.8 metric 1002
10.0.0.0/24 dev br0      proto dhcp scope link src 10.0.0.8 metric 1004
```

Both interfaces had `10.0.0.0/24` routes, and the one on `enp129s0` had a lower metric (1002 vs 1004). Lower metric wins. `ip route flush dev enp129s0` cleared them.

Two minutes later, they came back.

A process was actively re-adding them. `ps auxf | grep dhcpcd` revealed the culprit: **`dhcpcd` was running on BOTH `enp129s0` AND `br0`**, each claiming `10.0.0.8`. `dhcpcd` had been started at system boot before the bridge existed, picked up `enp129s0`, and was renewing its lease every few minutes — adding routes back each time.

Fix: add `denyinterfaces enp129s0` to `/etc/dhcpcd.conf` (persists across reboot), kill the running `dhcpcd` that was still bound to `enp129s0`, flush the IP + routes one more time. Routes stayed clean. IPv4 SSH started working.

Lesson for any future bridge build on a Debian host that already had dhcpcd running: kill and forbid dhcpcd on the physical interface BEFORE starting the bridge, or at least during the bridge migration. Otherwise you fight a ghost.

---

## 11. The disk-resize crisis — the 30 GB template was too small for the top tier

With all eight VMs alive and reachable, provisioning began. Sequential, per Nir's instruction: "definitely one by one, take your time, no rush, do not go around problems, solve them from the root very patiently please." The script `scripts/provision_laptop_vm.sh` handles per-VM Ollama install, the three model pulls, whisper.cpp compile, whisper STT model download, and Python venv creation.

Rajabee went first. About 45 minutes later, exit code 0. I verified:

- qwen3:14b (9.3 GB loaded) — present.
- granite3.1-moe:3b (2.0 GB) — present.
- qwen3.5:9b (6.6 GB) — present.
- whisper large-v3-turbo (1.6 GB) — present.
- Python venv — present.
- `df -h /` — **28G used of 28G, 625M free, 98% full.**

The template had been created with a 30 GB qcow2 disk. Fine for a bare Debian 13. NOT fine for RajaBee, whose model pile totals about 19 GB plus 7 GB of OS, whisper, apt cache, and margin.

The temptation was to move on. Nir's instruction was the opposite. Solve from the root.

Root fix: resize. Install `libguestfs-tools` (contains `virt-resize`). Shut rajabee down cleanly. Create a new 60 GB qcow2 file. Run:

```
sudo virt-resize --expand /dev/sda1 old.qcow2 new.qcow2
```

`virt-resize` handles the partition layout properly, including moving the Debian swap partition that sits after root. Swap the old and new files, `chown libvirt-qemu:kvm`, start rajabee, verify `df -h /` now shows `58G used 26G free 48% used`. Delete the 30 GB backup. Done.

While rajabee was up with an oversized disk, I proactively resized giantqueen-a (30 GB → 50 GB), both dwarfqueens (30 GB → 40 GB), and kept workers at 30 GB. The disk math per tier was done BEFORE provisioning those VMs, preventing a repeat of the rajabee surprise on the other seven.

Provisioning continued.

---

## 12. The silent `tee` bug — why `set -e` is not enough

Everything provisioned fine except one worker.

`worker-a3` completed with exit code 0 but only had 2 of 3 Ollama models. Its `ollama pull qwen3.5:0.8b` had hit a transient IPv6 network glitch to `registry.ollama.ai`, retried internally for about fifteen minutes, and returned a non-zero exit. My provisioning script had `set -euo pipefail` — `set -e` should have caught the failure and aborted the script.

It didn't. Because the script was being invoked as:

```
bash scripts/provision_laptop_vm.sh worker-a3 10.0.0.31 2>&1 | tee /tmp/provision-worker-a3.log
```

The pipe through `tee` for log capture.

`set -o pipefail` only propagates non-zero exits if the LAST command in a pipeline (`tee`) also fails. `tee` doesn't care whether the thing upstream succeeded. `tee` exited 0. The script's overall exit status was 0. The script thought all was well, skipped the whisper and venv steps (because `set -e` aborted at the ollama pull but didn't propagate to the outer shell's exit code), and the background process reported success.

Fix for worker-a3 specifically: re-run `ollama pull qwen3.5:0.8b` manually (succeeded on retry), then manually run the apt install / whisper build / venv creation steps.

Fix for the script: write the log inside the script (redirect to file from within) rather than using an external pipe. OR gate each critical step with an explicit `|| exit 1`. OR stop using `set -e` at all and check each command's exit code manually.

This bug cost about ten minutes to find and fix. It's the kind of bug that would have been much worse if we'd trusted the green exit and moved on.

---

## 13. Sequential discipline — why "one by one" was the right call

Nir picked sequential provisioning over parallel. He said: "definitely one by one, take your time, no rush, do not go around problems, solve them from the root very patiently please."

Sequential was slower — roughly three hours wall clock for eight VMs instead of maybe forty-five minutes if we'd fired all eight in parallel. It was also much easier to debug. When rajabee's disk filled up, I had time to stop, fix the root cause, and resize the others preemptively. When worker-a3's silent fail happened, I caught it at completion time rather than at the end of a simultaneous batch where eight confusing errors would have been interleaved.

Parallel would have finished faster and left a mess. Sequential finished slower and left a cluster that's known-good VM by VM.

This is the whole point of the "one by one" instruction. It's not about speed. It's about whether, when you're done, you trust what you have. Parallel gets you to "done" faster. Sequential gets you to "done and I know why" faster.

---

## 14. What the cluster looks like right now

Eight Laptop VMs. Plus seven Desktop VMs (built the previous day, vision swap earlier today). Fifteen total.

The Laptop half, with final IPs and per-tier loadouts:

| VM | IP | RAM | vCPU | Dense | MoE | Vision | STT |
|---|---|---|---|---|---|---|---|
| rajabee | 10.0.0.14 | 16 GB | 6 | qwen3:14b | granite3.1-moe:3b | qwen3.5:9b | whisper large-v3-turbo |
| giantqueen-a | 10.0.0.17 | 12 GB | 6 | qwen3:8b | granite3.1-moe:3b | qwen3-vl:8b | whisper small |
| dwarfqueen-a1 | 10.0.0.19 | 6 GB | 4 | phi4-mini:3.8b | granite3.1-moe:3b | gemma3:4b | whisper tiny |
| dwarfqueen-a2 | 10.0.0.25 | 6 GB | 4 | phi4-mini:3.8b | granite3.1-moe:3b | gemma3:4b | whisper tiny |
| worker-a1 | 10.0.0.27 | 4 GB | 2 | qwen3:1.7b | granite3.1-moe:1b | qwen3.5:0.8b | whisper tiny |
| worker-a2 | 10.0.0.29 | 4 GB | 2 | qwen3:1.7b | granite3.1-moe:1b | qwen3.5:0.8b | whisper tiny |
| worker-a3 | 10.0.0.31 | 4 GB | 2 | qwen3:1.7b | granite3.1-moe:1b | qwen3.5:0.8b | whisper tiny |
| worker-a4 | 10.0.0.33 | 4 GB | 2 | qwen3:1.7b | granite3.1-moe:1b | qwen3.5:0.8b | whisper tiny |

56 GB of guest RAM allocated on a 62 GiB host — 6 GB host headroom, matching the downgrade brief's "5-8 GB minimum" rule. 32 Ollama models plus 8 whisper models across the eight VMs. All reachable via SSH with `~/.ssh/phase3_ed25519`. All serving the Ollama API on `http://<vm-ip>:11434`.

---

## 15. Lessons worth keeping

Some of these are mine to remember; some are for whoever reads this after.

**Measure vision models. Never estimate them.** The `params × 0.6 GB` formula is for dense text. Vision models add an image encoder and a much larger KV cache. Qwen2.5vl:7b was three times bigger loaded than the formula predicted. The remedy is to pull the model on a throwaway host, load it CPU-only with `num_gpu: 0`, read `free -h` delta, and then delete it. Budget 10 minutes per measurement. Commit the result to GitHub so future-you can trust it.

**The user is a better reviewer than you are.** Nir caught the `gemma3:12b vs qwen3-vl:8b` quality reversal. Nir caught the `"familiar" feeling about qwen3.5`, which turned out to be legitimate: we had considered the qwen3.5 namespace in April's flagship plan. Nir caught the fabricated girlfriend name. Every mistake I made was caught by a non-programmer with ADD. The frontier-model label is not a permission to be sloppy — it is a promise to be unusually careful.

**Tee swallows exits.** `set -euo pipefail` is not enough if the script is invoked with an external pipe to `tee`. Either log inside the script, or gate every step with explicit `|| exit 1`, or audit pipelines for the exit-code path you actually care about.

**IPv6 link-local is a great fallback for bridged VM discovery.** When libvirt has no visibility and the LAN router won't tell you, every VM still advertises itself on IPv6 SLAAC using EUI-64 from its MAC. You can SSH to a newly-booted VM using only the MAC you already know.

**dhcpcd and ifupdown can fight over the same interface.** If a Debian host has dhcpcd running from boot AND you later configure ifupdown to own the physical interface as a bridge slave, dhcpcd will keep re-adding routes on the physical interface forever, poisoning your routing table every few minutes. `denyinterfaces` in `/etc/dhcpcd.conf` makes this permanent.

**Template-and-clone beats autoinstall-each.** Yesterday's Desktop build fought Ubuntu autoinstall for hours before switching to clone. Today's Laptop build went straight to clone from a single known-good template. Eight VMs in about five minutes once the template was clean. Clone is faster, more predictable, and lets you fix issues once.

**Size the template for the biggest tier, or parameterize disk at clone time.** 30 GB was fine for workers and dwarfqueens. It was catastrophically wrong for rajabee. Parameterize the clone script by tier so you don't discover this at the 98%-disk-full moment.

**Sequential provisioning is worth the wait.** Parallel provisioning is tempting because it's faster. It's the wrong choice when you actually need to trust the outcome. The rajabee disk crisis and the worker-a3 silent fail were both caught early and fixed calmly because we were going one by one. In parallel, they would have been two of eight simultaneous failure modes and we'd have blamed it on bad luck.

**The hardest problems are the ones where everything looks green.** Worker-a3 returned exit code 0. `ollama list` "looked normal" until I counted models and saw it was 2 instead of 3. Always verify the end state against the expected state, not against the script's claimed success.

---

## 16. What's next

The 15-VM cluster is built. The Laptop 8 and the Desktop 7 are both healthy. Every VM has the full LLM and STT loadout its tier requires. Every IP is known. Every SSH key works. Every Ollama endpoint responds.

The next step is the Phase 3 experiment itself — wiring up the KillerBee website and the WaggleDance server to treat these fifteen VMs as real bees in the hierarchy and running a real multimodal job end-to-end. That's for another session, another chapter.

For now, Nir goes to sleep. The bees wait.

---

*Written by Opus 4.7 xhigh on 2026-04-17 into the small hours of 2026-04-18. Canonical. Edit in place. Git is the time machine.*
