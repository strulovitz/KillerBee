#!/bin/bash
# Phase 3: autoinstall + boot + ollama install + verify, for one VM.
# Usage: full_cycle_one.sh <vm-name> <ram-MB>
set -euo pipefail

NAME="${1:?}"
RAM_MB="${2:?}"
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
SSH="ssh -i /home/nir/.ssh/phase3_ed25519 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=10 -o BatchMode=yes"

echo "====> $NAME: autoinstall"
bash "$SCRIPT_DIR/autoinstall_one.sh" "$NAME" "$RAM_MB"

echo "====> $NAME: boot"
sudo virsh start "$NAME"

echo "====> $NAME: wait for ARP"
MAC=$(sudo virsh domiflist "$NAME" | awk '/bridge/ {print $5}')
IP=""
for i in $(seq 1 60); do
  for j in $(seq 2 254); do (ping -c1 -W1 10.0.0.$j >/dev/null 2>&1 &) ; done
  sleep 3
  L=$( (ip neigh show dev br0 | grep -i "$MAC" | awk '{print $1}' | head -1) || true )
  if [ -n "$L" ]; then IP="$L"; break; fi
  sleep 2
done
if [ -z "$IP" ]; then echo "FAIL: $NAME no IP after 5min"; exit 1; fi
echo "$NAME IP=$IP"

echo "====> $NAME: wait for SSH"
for i in $(seq 1 30); do
  if $SSH "nir@$IP" 'echo ready' 2>/dev/null | grep -q ready; then break; fi
  sleep 5
done

echo "====> $NAME: install ollama"
$SSH "nir@$IP" 'curl -fsSL https://ollama.com/install.sh | sh' 2>&1 | tail -3

echo "====> $NAME: bind OLLAMA_HOST"
$SSH "nir@$IP" 'sudo mkdir -p /etc/systemd/system/ollama.service.d && printf "[Service]\nEnvironment=OLLAMA_HOST=0.0.0.0:11434\n" | sudo tee /etc/systemd/system/ollama.service.d/override.conf >/dev/null && sudo systemctl daemon-reload && sudo systemctl restart ollama'

echo "====> $NAME: verify"
sleep 2
V=$(curl -sS --max-time 5 "http://$IP:11434/api/version")
if echo "$V" | grep -q version; then
  echo "OK $NAME @ $IP: $V"
else
  echo "FAIL $NAME @ $IP: $V"; exit 1
fi
