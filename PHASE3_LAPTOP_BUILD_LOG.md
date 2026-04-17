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

Current status: `laptop-template` install launched via `virt-install` with initrd-inject preseed and `auto=true priority=critical` kernel args. Install expected to take 15-30 min. Progress visible via `sudo virsh domblkinfo laptop-template vda`.

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
