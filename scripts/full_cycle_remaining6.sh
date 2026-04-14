#!/bin/bash
# Run full cycle (autoinstall + ollama + verify) for the remaining 6 Desktop VMs.
# Sequential, one at a time, per Laptop Claude's rule.
set -eu
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
set -- \
  dwarfqueen-b2 8192 \
  worker-b1 4096 \
  worker-b2 4096 \
  worker-b3 4096 \
  worker-b4 4096
while [ $# -ge 2 ]; do
  NAME="$1"; RAM="$2"; shift 2
  echo "================================"
  echo "Starting $NAME (RAM=$RAM)"
  echo "================================"
  bash "$SCRIPT_DIR/full_cycle_one.sh" "$NAME" "$RAM"
done
echo "ALL 6 REMAINING VMs COMPLETE"
sudo virsh list --all
