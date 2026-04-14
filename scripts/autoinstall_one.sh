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
: > "$STAGE/meta-data"
genisoimage -quiet -output "$STAGE/seed.iso" -volid CIDATA \
    -joliet -rock "$STAGE/user-data" "$STAGE/meta-data"

# Move the seed iso into a place libvirt-qemu can read.
sudo mkdir -p "$BIG/vm/$NAME"
SEED_DST="$BIG/vm/$NAME/seed.iso"
sudo mv "$STAGE/seed.iso" "$SEED_DST"

DISK="$BIG/$NAME.qcow2"
# If a prior failed run left a 0-byte qcow2, drop it so virt-install can
# re-allocate. sudo mv to /tmp just to rename it out of the way.
if [ -e "$DISK" ]; then sudo mv "$DISK" "/tmp/phase3-stage/stale-$NAME.qcow2"; fi

echo "=== starting autoinstall for $NAME (RAM=${RAM_MB}M, disk=${DISK_GB}G, vcpus=${VCPUS}) ==="
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

echo "=== virt-install returned (autoinstall done) for $NAME ==="
sudo virsh list --all | grep -E "^ *-? +$NAME"
