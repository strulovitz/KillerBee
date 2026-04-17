#!/usr/bin/env bash
# KillerBee Phase 3 Laptop - clone laptop-template into 8 VMs per the locked roster.
# Runs AFTER laptop-template install completes and the template VM is shut off.
#
# Strategy (same as Desktop used for giantqueen-b clone path):
#   1. Copy qcow2 per VM
#   2. qemu-nbd mount, change /etc/hostname + /etc/hosts + regenerate machine-id
#   3. virt-install --import to define with the right RAM / vCPU
#   4. Start VM, wait for SSH via key, smoke test hostname
#
# Roster (from PHASE3_LAPTOP_ROSTER_LOCKED.md):

set -euo pipefail

TEMPLATE="/home/killerbee-images/laptop-template.qcow2"
POOL_DIR="/home/killerbee-images"
SSH_KEY="$HOME/.ssh/phase3_ed25519"
MOUNT="/tmp/vm-mount"

if [[ ! -f "$TEMPLATE" ]]; then
    echo "ERROR: template qcow2 not found at $TEMPLATE"
    exit 1
fi

# Ensure template VM is shut off
if sudo virsh list --state-running --name | grep -qx "laptop-template"; then
    echo "ERROR: laptop-template is still running. Shut it down first."
    exit 1
fi

# Roster: name | RAM (MB) | vCPU
ROSTER=(
    "rajabee|16384|6"
    "giantqueen-a|12288|6"
    "dwarfqueen-a1|6144|4"
    "dwarfqueen-a2|6144|4"
    "worker-a1|4096|2"
    "worker-a2|4096|2"
    "worker-a3|4096|2"
    "worker-a4|4096|2"
)

for row in "${ROSTER[@]}"; do
    NAME="${row%%|*}"
    rest="${row#*|}"
    RAM="${rest%%|*}"
    VCPUS="${rest#*|}"

    TARGET="$POOL_DIR/$NAME.qcow2"

    echo "=========================================="
    echo "Cloning $NAME (RAM ${RAM} MB, vCPU $VCPUS)"
    echo "=========================================="

    if sudo virsh list --all --name | grep -qx "$NAME"; then
        echo "  -> VM $NAME already defined. Skipping."
        continue
    fi

    # Copy qcow2
    sudo cp --reflink=auto "$TEMPLATE" "$TARGET"
    sudo chown libvirt-qemu:kvm "$TARGET"

    # Mount via qemu-nbd to rewrite hostname + machine-id
    sudo modprobe nbd max_part=8
    sudo qemu-nbd --disconnect /dev/nbd0 2>/dev/null || true
    sudo qemu-nbd --connect=/dev/nbd0 "$TARGET"
    sleep 2

    sudo mkdir -p "$MOUNT"
    # Debian 13 preseed atomic recipe creates a single root partition at /dev/nbd0p1
    sudo mount /dev/nbd0p1 "$MOUNT"

    # Rewrite hostname + hosts
    echo "$NAME" | sudo tee "$MOUNT/etc/hostname" > /dev/null
    sudo sed -i "s/debian-template/$NAME/g" "$MOUNT/etc/hosts"
    # Clear machine-id so it regenerates on first boot
    sudo truncate -s 0 "$MOUNT/etc/machine-id"
    [[ -f "$MOUNT/var/lib/dbus/machine-id" ]] && sudo truncate -s 0 "$MOUNT/var/lib/dbus/machine-id"

    sudo umount "$MOUNT"
    sudo qemu-nbd --disconnect /dev/nbd0
    sleep 1

    # Define the VM via virt-install --import
    sudo virt-install \
        --name "$NAME" \
        --memory "$RAM" \
        --vcpus "$VCPUS" \
        --cpu host-passthrough \
        --os-variant debian12 \
        --disk "path=$TARGET,format=qcow2,bus=virtio" \
        --network bridge=br0,model=virtio \
        --graphics none \
        --noautoconsole \
        --import \
        --noreboot

    # Start the VM
    sudo virsh start "$NAME"

    # Wait up to 120s for SSH
    echo "  -> waiting for VM $NAME SSH..."
    for i in {1..24}; do
        # Find IP via libvirt net-dhcp-leases for br0 (or arp)
        IP=$(sudo virsh domifaddr --source agent "$NAME" 2>/dev/null | awk '/ipv4/ {print $4}' | cut -d/ -f1 | head -1)
        if [[ -z "$IP" ]]; then
            IP=$(sudo virsh domifaddr --source lease "$NAME" 2>/dev/null | awk '/ipv4/ {print $4}' | cut -d/ -f1 | head -1)
        fi
        if [[ -z "$IP" ]]; then
            # Fallback: ARP lookup by MAC
            MAC=$(sudo virsh domiflist "$NAME" | awk '/bridge/ {print $NF}' | head -1)
            IP=$(ip neigh | awk -v mac="$MAC" '$5 == mac && $3 == "br0" {print $1}' | head -1)
        fi
        if [[ -n "$IP" ]] && ssh -i "$SSH_KEY" -o ConnectTimeout=5 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null nir@"$IP" 'hostname' 2>/dev/null | grep -q "$NAME"; then
            echo "  -> VM $NAME is up at $IP with hostname confirmed"
            break
        fi
        sleep 5
    done

    echo "  -> $NAME clone complete."
    echo ""
done

echo "=========================================="
echo "All 8 Laptop VMs cloned + started."
echo "=========================================="
sudo virsh list --all
