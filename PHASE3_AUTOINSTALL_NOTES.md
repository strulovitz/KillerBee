# Phase 3 Autoinstall — Lessons Learned

**Purpose:** Save every hard-won insight about Ubuntu 24.04.4 autoinstall via virt-install so no future session wastes hours re-discovering them.

---

## The Setup That Works

The **original `autoinstall_one.sh` script works as-is.** The key virt-install command:

```bash
sudo virt-install \
  --name "$NAME" \
  --memory "$RAM_MB" \
  --vcpus "$VCPUS" \
  --cpu host-passthrough \
  --os-variant ubuntu24.04 \
  --disk "path=$DISK,format=qcow2,bus=virtio,size=${DISK_GB}" \
  --disk "path=$SEED_DST,device=cdrom" \
  --location "$ISO,kernel=casper/vmlinuz,initrd=casper/initrd" \
  --extra-args 'autoinstall ds=nocloud console=ttyS0,115200n8 serial' \
  --network bridge=br0,model=virtio \
  --graphics none \
  --noautoconsole \
  --noreboot \
  --wait -1
```

### Seed ISO (CIDATA)

Built with `genisoimage`:
```bash
genisoimage -quiet -output seed.iso -volid CIDATA -joliet -rock user-data meta-data
```

- Volume label MUST be `CIDATA` (case-sensitive)
- `user-data` starts with `#cloud-config` header, `autoinstall:` is top-level key
- `meta-data` can have `instance-id: <hostname>` (was empty in original, works either way)
- Seed ISO is the SECOND disk (`--disk path=...,device=cdrom`), install ISO is via `--location`

### Kernel args

`autoinstall ds=nocloud console=ttyS0,115200n8 serial`

That's it. Nothing else needed.

---

## Critical Timing — DO NOT KILL THE INSTALL

### The autoinstall has THREE slow phases:

1. **Startup delay: ~5 minutes of near-zero disk writes.** The installer boots, finds the squashfs on the ISO, starts Subiquity, discovers network, and initializes cloud-init. During this phase the qcow2 disk stays at ~12MB. **This looks like the install is stuck. IT IS NOT.** Wait at least 6-7 minutes before concluding something is wrong.

2. **Package installation: ~5-8 minutes.** Disk grows from ~12MB to ~4GB. This is the OS, our requested packages (curl, python3, python3-pip, git, ca-certificates), openssh-server, and cloud-init configuration.

3. **Security updates: ~5-20 minutes.** After packages are installed, `run_unattended_upgrades` downloads and installs security patches. Disk writes are slow/sporadic during this phase. The VM appears idle but is downloading from Ubuntu mirrors.

**Total expected time: 15-30 minutes per VM.** NOT 4 minutes.

### After all three phases complete, the VM should auto-poweroff (`shutdown: poweroff` in user-data). The `--noreboot --wait -1` flags mean virt-install blocks until this happens.

---

## What BREAKS the Installer (DO NOT DO THESE)

All of the following were tested on 2026-04-16 and caused the installer to stall at 12MB forever (no disk writes, no install progress):

1. **Adding `cloud-config-url=/dev/null` to kernel args** — breaks the installer's own cloud-init initialization. The installer needs its default cloud-config-url during boot.

2. **Using `ds=nocloud\;s=http://...` or `ds=nocloud;s=file:///`** — the semicolon causes shell/kernel quoting issues. Even when properly escaped, these alternative datasource paths interfere with the installer's boot sequence.

3. **Using `--initrd-inject` with user-data/meta-data** — did not help. The installer still couldn't find the config, and the modified initrd may have broken the boot.

4. **Removing `ds=nocloud` from kernel args** — without this arg, the installer doesn't know to look for the CIDATA seed at all.

5. **Using `--cloud-init` flag without `ds=nocloud` in extra-args** — the `--cloud-init` flag creates its own CIDATA ISO, but without `ds=nocloud` in the kernel args, the installer doesn't find it.

**The ONLY working combination is the original:** `autoinstall ds=nocloud console=ttyS0,115200n8 serial` with a CIDATA seed.iso as a second CDROM.

---

## Debugging Tips

- **Check disk allocation** to see if the install is progressing:
  ```bash
  sudo virsh domblkinfo <vm-name> vda | grep Allocation
  ```
  - ~12MB = still in startup phase (wait 5+ minutes)
  - Growing past 500MB = install is running
  - Flat at ~4GB = install done, doing security updates or finished

- **Check console** (only from a real terminal, not from Claude Code):
  ```bash
  sudo virsh console <vm-name>
  ```
  Press Enter to see output. You'll see Subiquity progress messages like:
  - `subiquity/Install/install/postinstall/install_openssh-server` = packages installing
  - `subiquity/Install/install/postinstall/run_unattended_upgrades` = security updates (slow)

- **DO NOT use `virsh console` from Claude Code** — it requires a controlling TTY.

---

## Known Issue: `late-commands` Don't Execute

The `late-commands` section in user-data (which sets up passwordless sudo) does NOT execute in this autoinstall setup. The autoinstall applies identity, SSH, packages, and storage correctly, but `late-commands` are silently skipped.

**Workaround:** After autoinstall completes and before first boot, mount the qcow2 from the host and add the sudoers file manually:

```bash
sudo bash -c 'modprobe nbd max_part=8 && \
  qemu-nbd --connect=/dev/nbd0 /home/killerbee-images/<VM-NAME>.qcow2 && \
  sleep 2 && mkdir -p /tmp/vm-mount && \
  mount /dev/nbd0p2 /tmp/vm-mount && \
  echo "nir ALL=(ALL) NOPASSWD: ALL" > /tmp/vm-mount/etc/sudoers.d/90-nir && \
  chmod 0440 /tmp/vm-mount/etc/sudoers.d/90-nir && \
  umount /tmp/vm-mount && \
  qemu-nbd --disconnect /dev/nbd0 && \
  echo "DONE"'
```

This requires the host user's sudo password (Nir must run it from a terminal). The `nbd` module, `qemu-nbd`, and `mount` all need root. The partition is typically `nbd0p2` (the root filesystem).

**This must be done for EVERY VM after autoinstall, before first boot.** Add to `full_cycle_one.sh` as a post-autoinstall step (requires Nir to enter sudo password once per session).

### Known Issue: `shutdown: poweroff` Doesn't Fire

The `shutdown: poweroff` directive in user-data does not reliably trigger auto-poweroff after install in Ubuntu 24.04.4. The VM finishes installing but sits running. Workaround: send ACPI shutdown from host after detecting flat disk writes:

```bash
virsh shutdown <vm-name>
```

`virsh shutdown` does NOT require a password (libvirt has its own NOPASSWD rules). This should also be added to `full_cycle_one.sh` — poll for flat disk, then force shutdown.

---

## Verification After Boot

After the VM auto-poweroffs and is booted (`virsh start`):

1. **Hostname should be the VM name** (e.g., `giantqueen-b`), NOT `ubuntu-server`
2. **SSH should work** with the phase3 key:
   ```bash
   ssh -i ~/.ssh/phase3_ed25519 nir@<ip>
   ```
3. **User `nir` should exist** with passwordless sudo
4. **Packages should be installed:** `curl`, `python3`, `python3-pip`, `git`

If hostname is `ubuntu-server`, the CIDATA seed was not found — check the seed.iso volume label and contents.

---

*Canonical. Edit in place. Git is the time machine.*
