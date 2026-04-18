#!/bin/bash
# Start all 8 Laptop-side bees on their respective VMs.
# Usage: start_laptop_bees.sh <batch>
# <batch> is "dense" or "moe" and selects the tier model name.
set -euo pipefail

BATCH="${1:-dense}"
SERVER="http://10.0.0.8:8877"
SWARM_ID=1
SSH_KEY="$HOME/.ssh/phase3_ed25519"
SSH_OPTS="-i $SSH_KEY -o StrictHostKeyChecking=no -o BatchMode=yes -o ConnectTimeout=10"

case "$BATCH" in
  dense)
    RAJA_MODEL="qwen3:14b"
    GQ_MODEL="qwen3:8b"
    DQ_MODEL="phi4-mini:3.8b"
    W_MODEL="qwen3:1.7b"
    ;;
  moe)
    RAJA_MODEL="granite3.1-moe:3b"
    GQ_MODEL="granite3.1-moe:3b"
    DQ_MODEL="granite3.1-moe:3b"
    W_MODEL="granite3.1-moe:1b"
    ;;
  *)
    echo "Unknown batch '$BATCH' (use dense or moe)" >&2
    exit 1
    ;;
esac

echo "Starting Laptop bees in $BATCH mode against $SERVER (swarm $SWARM_ID)"
echo "  Raja $RAJA_MODEL, GQ $GQ_MODEL, DQ $DQ_MODEL, W $W_MODEL"

start_bee() {
  local ip="$1" user="$2" model="$3" script="$4"
  ssh $SSH_OPTS "nir@$ip" "bash -lc '
    cd ~/GiantHoneyBee &&
    pkill -f \"python3 ${script}\" 2>/dev/null; sleep 1;
    rm -f ~/bee.log;
    nohup python3 ${script} \
      --server ${SERVER} \
      --swarm-id ${SWARM_ID} \
      --username ${user} \
      --password password \
      --model ${model} \
      < /dev/null > ~/bee.log 2>&1 &
    sleep 1; echo PID=\$!
  '" &
}

# Top-down start so parents register before children.
start_bee 10.0.0.14 raja_nir        "$RAJA_MODEL" raja_bee.py
start_bee 10.0.0.17 queen_giant_a   "$GQ_MODEL"   giant_queen_client.py
start_bee 10.0.0.19 queen_dwarf_a1  "$DQ_MODEL"   dwarf_queen_client.py
start_bee 10.0.0.25 queen_dwarf_a2  "$DQ_MODEL"   dwarf_queen_client.py
start_bee 10.0.0.27 worker_a1       "$W_MODEL"    worker_client.py
start_bee 10.0.0.29 worker_a2       "$W_MODEL"    worker_client.py
start_bee 10.0.0.31 worker_a3       "$W_MODEL"    worker_client.py
start_bee 10.0.0.33 worker_a4       "$W_MODEL"    worker_client.py

wait
echo "All 8 Laptop bee start commands issued."
