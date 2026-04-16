#!/bin/bash
# Phase 3: Fresh autoinstall of one KillerBee VM.
# Everything lives under /home/killerbee-images so libvirt-qemu can reach it
# without needing traverse perms on /home/nir (which is 750).
# Usage: autoinstall_one.sh <vm-name> <ram-MB> <disk-GB> <vcpus>
# Example: autoinstall_one.sh giantqueen-b 8192 80 6
set -euo pipefail

NAME="${1:?missing vm name}"
RAM_MB="${2:?missing ram MB}"
DISK_GB="${3:?missing disk GB (e.g. 80)}"
VCPUS="${4:?missing vcpu count (e.g. 6)}"

BIG=/home/killerbee-images
ISO="$BIG/isos/ubuntu-24.04.4-live-server-amd64.iso"
TEMPLATE_SEED=/home/nir/vm/desktop-template/seed
STAGE=/tmp/phase3-stage/$NAME

# Build a fresh seed.iso locally with the hostname substituted.
rm -rf "$STAGE"
mkdir -p "$STAGE"
sed "s/hostname: desktop-template/hostname: $NAME/" \
    "$TEMPLATE_SEED/user-data" > "$STAGE/user-data"
echo "instance-id: $NAME" > "$STAGE/meta-data"
genisoimage -quiet -output "$STAGE/seed.iso" -volid CIDATA \
    -joliet -rock "$STAGE/user-data" "$STAGE/meta-data"

# Move the seed iso into a place libvirt-qemu can read.
sudo mkdir -p "$BIG/vm/$NAME"
SEED_DST="$BIG/vm/$NAME/seed.iso"
sudo mv "$STAGE/seed.iso" "$SEED_DST"

DISK="$BIG/$NAME.qcow2"
# If a prior failed run left a qcow2, drop it so virt-install can re-allocate.
if [ -e "$DISK" ]; then sudo mv "$DISK" "/tmp/phase3-stage/stale-$NAME.qcow2"; fi

echo "=== starting autoinstall for $NAME (RAM=${RAM_MB}M, disk=${DISK_GB}G, vcpus=${VCPUS}) ==="

# Launch virt-install in the background. Ubuntu 24.04's shutdown: poweroff
# does not reliably fire, so we cannot use --wait -1 (it hangs forever).
# Instead we poll disk allocation and send ACPI shutdown when writes stop.
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
  --wait -1 &
VIRT_PID=$!

# Poll disk allocation. The autoinstall has 3 phases:
# 1. ~5 min startup (disk stays ~12MB — NOT stuck, just slow)
# 2. ~5-8 min package install (disk grows to ~4GB)
# 3. ~5-20 min security updates (slow/sporadic writes, disk reaches ~5GB)
# After all 3 phases, disk goes flat. We detect "flat for 3 minutes" and
# send ACPI shutdown.
echo "=== polling disk writes (expect 15-30 min total) ==="
PREV_ALLOC=0
FLAT_COUNT=0
FLAT_THRESHOLD=18  # 18 x 10s = 3 minutes of no writes
MIN_SIZE=500000000  # don't trigger until at least 500MB written (install started)

while kill -0 $VIRT_PID 2>/dev/null; do
  ALLOC=$(sudo virsh domblkinfo "$NAME" vda 2>/dev/null | awk '/Allocation/ {print $2}') || ALLOC=0
  MB=$((ALLOC / 1048576))
  echo "  disk: ${MB}MB"

  if [ "$ALLOC" -gt "$MIN_SIZE" ]; then
    if [ "$ALLOC" -eq "$PREV_ALLOC" ]; then
      FLAT_COUNT=$((FLAT_COUNT + 1))
    else
      FLAT_COUNT=0
    fi

    if [ "$FLAT_COUNT" -ge "$FLAT_THRESHOLD" ]; then
      echo "=== disk flat for 3 min at ${MB}MB — sending ACPI shutdown ==="
      virsh shutdown "$NAME" 2>/dev/null || true
      break
    fi
  fi

  PREV_ALLOC=$ALLOC
  sleep 10
done

# Wait for virt-install to return (it will once the VM shuts off)
wait $VIRT_PID 2>/dev/null || true

echo "=== autoinstall done for $NAME ==="
sudo virsh list --all | grep -E "^ *-? +$NAME"
