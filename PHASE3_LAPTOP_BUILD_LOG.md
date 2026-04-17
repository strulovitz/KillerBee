# Phase 3 Laptop Build Log

**Started:** 2026-04-17 after all model-fit measurements complete.

## Host prerequisites complete

- [x] KVM stack installed (qemu, libvirt, virt-install, qemu-utils, genisoimage). Required `apt --fix-broken install` to work around stale package index that referenced libcapstone5 5.0.6-1 (pool actually has 5.0.7-1).
- [x] libvirtd active, enabled at boot.
- [x] User `nir` added to groups: `libvirt`, `kvm`.
- [x] Directories created: `/home/killerbee-images/isos/`, `~/vm/laptop-template/seed/`.
- [x] SSH key pair generated: `~/.ssh/phase3_ed25519` (ed25519).
- [x] Debian 13 Trixie netinst ISO downloaded: `/home/killerbee-images/isos/debian-13-netinst.iso` (debian-13.4.0-amd64-netinst.iso, 790 MB).
- [x] libvirt pool `killerbee` defined + active + autostart, target `/home/killerbee-images/`.
- [x] br0 bridge configured via `/etc/network/interfaces` (classic ifupdown, NOT NetworkManager - enp129s0 was unmanaged by NM). Backup at `/etc/network/interfaces.pre-br0.backup`. Atomic switch succeeded: br0 got 10.0.0.8 via DHCP with cloned MAC (c8:53:09:be:bf:3a). Had to `ip addr flush dev enp129s0` after to clear stale IP.
- [x] libvirt network `br0` defined + active + autostart (forward mode=bridge).
- [x] Debian 13 preseed file written: `~/vm/laptop-template/seed/preseed.cfg` (canonical copy in repo: `PHASE3_DEBIAN13_PRESEED.cfg`).
- [x] NOPASSWD sudo rule in place (`/etc/sudoers.d/99-nir-temp`) - allows autonomous build work.

## VM build phase (in progress)

Template-and-clone strategy (same pattern Desktop used):
1. Build `laptop-template` VM (4 GB RAM, 2 vCPU, 30 GB disk) from Debian 13 preseed
2. Shut down cleanly after install
3. Clone per VM in the locked roster, resizing RAM / vCPU / hostname / machine-id

Current status: **laptop-template VM fully built + verified working** (2026-04-17). Debian 13.4, SSH works with phase3_ed25519 key, sudo NOPASSWD set up, curl + python3 + git + pip3 all present. Shut off cleanly. Ready to clone.

### Post-install fix history

The first boot had no network because:
1. Debian netinst wrote `allow-hotplug enp1s0` to /etc/network/interfaces (systemd predictable naming)
2. The `allow-hotplug` didn't fire at boot for the virtio NIC
3. Actual interface name was unpredictable

Fix via qemu-nbd mount of disk while VM was off:
- Added `net.ifnames=0 biosdevname=0` to kernel cmdline in both `/boot/grub/grub.cfg` and `/etc/default/grub` so interface is forced to `eth0`
- Rewrote `/etc/network/interfaces` with `auto eth0 / iface eth0 inet dhcp`
- Added `console=ttyS0,115200n8 console=tty0` to kernel cmdline so future debugging sees kernel output on serial

After boot via IPv6 (SLAAC worked while IPv4 DHCP was failing), SSHed in, verified everything, cleaned up multi-NIC fallback entries.

### Clone phase — COMPLETE 2026-04-17

All 8 VMs cloned from template, booted, SSH-accessible via phase3_ed25519 key. Each got a unique DHCP lease from the LAN router. **Current mapping** (IPs shifted after initial DHCP lease churn — IPs are stable by MAC but not static):

| VM | IP | RAM | vCPU | MAC |
|---|---|---|---|---|
| rajabee | 10.0.0.14 | 16 GB | 6 | 52:54:00:e1:a5:1b |
| giantqueen-a | 10.0.0.17 | 12 GB | 6 | 52:54:00:c9:b2:c0 |
| dwarfqueen-a1 | 10.0.0.19 | 6 GB | 4 | 52:54:00:08:98:0e |
| dwarfqueen-a2 | 10.0.0.25 | 6 GB | 4 | 52:54:00:fb:50:79 |
| worker-a1 | 10.0.0.27 | 4 GB | 2 | 52:54:00:ba:8f:9f |
| worker-a2 | 10.0.0.29 | 4 GB | 2 | 52:54:00:4b:7d:a7 |
| worker-a3 | 10.0.0.31 | 4 GB | 2 | 52:54:00:43:50:7d |
| worker-a4 | 10.0.0.33 | 4 GB | 2 | 52:54:00:96:4d:e3 |

### Network issue fixed during clone phase — `dhcpcd` on enp129s0 fighting with br0

During clone verification, host-to-VM IPv4 connectivity was failing. Root cause: the Laptop host had `dhcpcd` running on BOTH `enp129s0` (from system boot before the bridge) AND `br0` (from the bridge setup this afternoon). Both were claiming the same 10.0.0.8 lease, and enp129s0's route entries (metric 1002) kept taking precedence over br0's (metric 1004), causing ARP requests to go out enp129s0 instead of through the bridge.

Fix applied:
- Added `denyinterfaces enp129s0` to `/etc/dhcpcd.conf` (persists across reboots)
- Killed the running `dhcpcd: enp129s0` process
- Flushed IP + routes from enp129s0

After fix: `ip route` shows br0 as only 10.0.0.x path, ping to all VMs works, SSH direct to 10.0.0.14 (rajabee) etc. works cleanly.

**Note:** IPs do not match the aspirational 10.0.0.11-18 range in `PHASE3_LINUX_VM_SETUP.md` §5. The LAN router's DHCP pool handed out whatever was available. This is stable by MAC, but if IP stability is needed, add static DHCP reservations on the router. Desktop had the same pattern (see `PHASE3_REBUILD_STATUS.md`).

**Verification:** SSHed into rajabee, confirmed Debian 13 kernel 6.12.74, 15 GiB RAM available (of 16 GB allocated), 6 CPUs, 1.6 GB swap, eth0 on DHCP.

### Clone discovery trick (for future clones)

libvirt DHCP leases don't work for bridged VMs (no libvirt dnsmasq). To find a clone's IP right after boot:
1. Get its MAC from `sudo virsh domiflist <vm> | awk '/bridge/ {print $NF}'`
2. Compute the IPv6 link-local EUI-64 address: flip the 2nd bit of MAC's first byte, insert `ff:fe` in middle, prepend `fe80::`
3. SSH via link-local with `%br0` scope: `ssh -6 nir@fe80::<eui64>%br0`
4. Once in, `ip -br addr show eth0` shows the IPv4 lease

### Post-clone disk resize (2026-04-17)

First provisioning attempt on rajabee filled its 30 GB VM disk to 98% (only 625 MB free) because rajabee holds the biggest model set (qwen3:14b + qwen3.5:9b + granite3.1-moe:3b = ~18 GB, plus whisper large-v3-turbo = 1.6 GB, plus OS = ~7 GB, plus apt cache, etc).

**Root cause:** The template was created with 30 GB disk. When cloned, every VM inherited that size. 30 GB was fine for Desktop's rebuild plan (§2.3 in `PHASE3_REBUILD_PLAN.md` calls for 40 GB workers and larger) but the Laptop clone used template-default.

**Fix:** resized each VM's qcow2 + filesystem using `virt-resize --expand /dev/sda1` (from libguestfs-tools). Handles swap partition correctly. New sizes matched to tier needs:

| VM | New disk | Rationale |
|---|---|---|
| rajabee | 60 GB | biggest model pile, plus generous headroom |
| giantqueen-a | 50 GB | medium models + whisper small |
| dwarfqueen-a1, a2 | 40 GB | smaller models |
| worker-a1..a4 | 30 GB (unchanged) | tiny models fit easily |

Process per VM (captured for future reference):
1. `sudo virsh shutdown <vm>` then wait for "shut off"
2. `sudo qemu-img create -f qcow2 <new>.qcow2 <size>G`
3. `sudo virt-resize --expand /dev/sda1 <old>.qcow2 <new>.qcow2`
4. `sudo mv <old>.qcow2 <old>-backup.qcow2 && sudo mv <new>.qcow2 <old>.qcow2`
5. `sudo chown libvirt-qemu:kvm <old>.qcow2 && sudo chmod 600 <old>.qcow2`
6. `sudo virsh start <vm>` and verify via `ssh nir@<ip> 'df -h /'`
7. Delete backup once confirmed working.

**Lesson for future builds:** set appropriate disk size per tier at clone time, not after. Update `scripts/clone_laptop_vms.sh` to take a per-VM disk-size parameter.

### Next step — provisioning

Each VM needs Ollama installed + the tier-specific Dense/MoE/Vision/STT models pulled. That is what `scripts/provision_laptop_vm.sh` does. Running 8 VMs in sequence takes multiple hours because of the model downloads. Running in parallel saturates the LAN and host CPU but is faster end-to-end. Nir to decide timing.

## Key infra details

- **Laptop host IP:** 10.0.0.8/24 (via br0)
- **Host MAC cloned to br0:** c8:53:09:be:bf:3a
- **SSH key for VMs:** `~/.ssh/phase3_ed25519` (pubkey injected into preseed late_command)
- **VM user:** `nir` (with NOPASSWD sudo, SSH-key-only auth, password disabled)

## Rollback paths

- **br0 rollback:** `sudo cp /etc/network/interfaces.pre-br0.backup /etc/network/interfaces && sudo systemctl restart networking`
- **NOPASSWD revoke:** `sudo rm /etc/sudoers.d/99-nir-temp`
- **Remove libvirt pool/network:** `sudo virsh pool-destroy killerbee && sudo virsh pool-undefine killerbee && sudo virsh net-destroy br0 && sudo virsh net-undefine br0`

## Roster target (from PHASE3_LAPTOP_ROSTER_LOCKED.md)

| VM | RAM | vCPU | Dense | MoE | Vision | STT |
|---|---|---|---|---|---|---|
| rajabee | 16 GB | 6 | qwen3:14b | granite3.1-moe:3b | qwen3.5:9b | whisper large-v3-turbo |
| giantqueen-a | 12 GB | 6 | qwen3:8b | granite3.1-moe:3b | qwen3-vl:8b | whisper small |
| dwarfqueen-a1 | 6 GB | 4 | phi4-mini:3.8b | granite3.1-moe:3b | gemma3:4b | whisper tiny |
| dwarfqueen-a2 | 6 GB | 4 | phi4-mini:3.8b | granite3.1-moe:3b | gemma3:4b | whisper tiny |
| worker-a1..a4 | 4 GB | 2 | qwen3:1.7b | granite3.1-moe:1b | qwen3.5:0.8b | whisper tiny |

---

*Canonical build log. Edit in place. Git is the time machine.*
