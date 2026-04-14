#!/bin/bash
# Phase 3 V3 — autoinstall + swap check + Ollama install + verify for ALL 7 Desktop VMs.
# Sequential, one at a time. Uses (name, ram-MB, disk-GB, vcpu) quadruples per V3 plan §7.
# Does NOT pull models — model pulls are a separate step after all 7 VMs are up.
# Usage: full_cycle_all7_v3.sh
set -eu
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")

# Per PHASE3_REBUILD_PLAN_V3.md §5 summary table:
#   name              ram-MB  disk-GB  vcpu
#   giantqueen-b       8192    80       6
#   dwarfqueen-b1      6144    50       4
#   dwarfqueen-b2      6144    50       4
#   worker-b1..b4      4096    40       2
set -- \
  giantqueen-b   8192 80 6 \
  dwarfqueen-b1  6144 50 4 \
  dwarfqueen-b2  6144 50 4 \
  worker-b1      4096 40 2 \
  worker-b2      4096 40 2 \
  worker-b3      4096 40 2 \
  worker-b4      4096 40 2

while [ $# -ge 4 ]; do
  NAME="$1"; RAM="$2"; DISK="$3"; VCPU="$4"; shift 4
  echo "================================"
  echo "Starting $NAME (RAM=${RAM}M disk=${DISK}G vcpu=${VCPU})"
  echo "================================"
  bash "$SCRIPT_DIR/full_cycle_one.sh" "$NAME" "$RAM" "$DISK" "$VCPU"
done

echo "ALL 7 V3 VMs COMPLETE (autoinstall + swap + ollama bind + verify)"
sudo virsh list --all
