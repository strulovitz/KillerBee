#!/usr/bin/env bash
# KillerBee Phase 3 Laptop - provision ONE VM with Ollama + the right models per its tier.
# Runs via SSH into the VM, so the VM must be up + reachable via phase3_ed25519 key.
#
# Usage: ./provision_laptop_vm.sh <hostname> <ip>
#   hostname must match one of: rajabee, giantqueen-a, dwarfqueen-a1, dwarfqueen-a2, worker-a1..a4
#   ip is the DHCP-assigned IPv4 address on br0 (10.0.0.x)

set -euo pipefail

if [[ $# -ne 2 ]]; then
    echo "Usage: $0 <hostname> <ip>"
    exit 1
fi

NAME="$1"
IP="$2"
SSH_KEY="$HOME/.ssh/phase3_ed25519"
SSH="ssh -i $SSH_KEY -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"

# Per-tier model list (Dense, MoE, Vision). STT is whisper.cpp handled separately.
declare -A DENSE_MODEL=(
    [rajabee]="qwen3:14b"
    [giantqueen-a]="qwen3:8b"
    [dwarfqueen-a1]="phi4-mini:3.8b"
    [dwarfqueen-a2]="phi4-mini:3.8b"
    [worker-a1]="qwen3:1.7b"
    [worker-a2]="qwen3:1.7b"
    [worker-a3]="qwen3:1.7b"
    [worker-a4]="qwen3:1.7b"
)
declare -A MOE_MODEL=(
    [rajabee]="granite3.1-moe:3b"
    [giantqueen-a]="granite3.1-moe:3b"
    [dwarfqueen-a1]="granite3.1-moe:3b"
    [dwarfqueen-a2]="granite3.1-moe:3b"
    [worker-a1]="granite3.1-moe:1b"
    [worker-a2]="granite3.1-moe:1b"
    [worker-a3]="granite3.1-moe:1b"
    [worker-a4]="granite3.1-moe:1b"
)
declare -A VISION_MODEL=(
    [rajabee]="qwen3.5:9b"
    [giantqueen-a]="qwen3-vl:8b"
    [dwarfqueen-a1]="gemma3:4b"
    [dwarfqueen-a2]="gemma3:4b"
    [worker-a1]="qwen3.5:0.8b"
    [worker-a2]="qwen3.5:0.8b"
    [worker-a3]="qwen3.5:0.8b"
    [worker-a4]="qwen3.5:0.8b"
)
declare -A STT_MODEL=(
    [rajabee]="large-v3-turbo"
    [giantqueen-a]="small"
    [dwarfqueen-a1]="tiny"
    [dwarfqueen-a2]="tiny"
    [worker-a1]="tiny"
    [worker-a2]="tiny"
    [worker-a3]="tiny"
    [worker-a4]="tiny"
)

if [[ -z "${DENSE_MODEL[$NAME]:-}" ]]; then
    echo "ERROR: unknown VM name: $NAME"
    exit 1
fi

echo "=========================================="
echo "Provisioning $NAME at $IP"
echo "Dense: ${DENSE_MODEL[$NAME]}"
echo "MoE:   ${MOE_MODEL[$NAME]}"
echo "Vision:${VISION_MODEL[$NAME]}"
echo "STT:   whisper ${STT_MODEL[$NAME]}"
echo "=========================================="

# 1. Smoke-test SSH
$SSH "nir@$IP" 'hostname && free -h'

# 2. Install Ollama on the VM
$SSH "nir@$IP" 'curl -fsSL https://ollama.com/install.sh | sh' || {
    echo "Ollama install failed on $NAME"
    exit 1
}

# 3. Bind Ollama to 0.0.0.0 so it's reachable from the host + other VMs
$SSH "nir@$IP" 'sudo mkdir -p /etc/systemd/system/ollama.service.d && \
    printf "[Service]\nEnvironment=OLLAMA_HOST=0.0.0.0:11434\n" | sudo tee /etc/systemd/system/ollama.service.d/override.conf && \
    sudo systemctl daemon-reload && sudo systemctl restart ollama'

# 4. Pull the 3 Ollama models
for MODEL in "${DENSE_MODEL[$NAME]}" "${MOE_MODEL[$NAME]}" "${VISION_MODEL[$NAME]}"; do
    echo "  -> pulling $MODEL on $NAME"
    $SSH "nir@$IP" "ollama pull $MODEL"
done

# 5. Verify from host
echo "=== verify Ollama API on $NAME ==="
curl -s "http://$IP:11434/api/tags" | python3 -c "import sys, json; m=[x['name'] for x in json.load(sys.stdin)['models']]; print('Models on VM:', m)"

# 6. Install system deps for whisper.cpp build + run
$SSH "nir@$IP" 'sudo apt-get install -y ffmpeg build-essential cmake git python3 python3-pip python3-venv'

# 7. Build whisper.cpp + download STT model
$SSH "nir@$IP" "sudo mkdir -p /opt/killerbee/src && sudo chown nir:nir /opt/killerbee/src && \
    cd /opt/killerbee/src && \
    git clone --depth 1 https://github.com/ggerganov/whisper.cpp.git && \
    cd whisper.cpp && make -j\$(nproc) && \
    bash ./models/download-ggml-model.sh ${STT_MODEL[$NAME]}"

# 8. Create Python venv with the helper packages
$SSH "nir@$IP" 'sudo mkdir -p /opt/killerbee/venv-parent && sudo chown nir:nir /opt/killerbee/venv-parent && \
    python3 -m venv /opt/killerbee/venv-parent/venv && \
    /opt/killerbee/venv-parent/venv/bin/pip install numpy soundfile Pillow pytest requests'

echo "=========================================="
echo "Provisioning complete for $NAME."
echo "=========================================="
