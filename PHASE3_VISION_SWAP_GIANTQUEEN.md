# Phase 3 Vision Model Swap — giantqueen-b ONLY

**Author:** Laptop Linux Claude (Opus 4.7 xhigh), 2026-04-17.
**For:** Desktop Linux Claude (Mint 22.2), once Nir boots into Linux and starts ICQ.
**Scope:** ONE change on ONE VM. Nothing else on Desktop is touched.

---

## 1. Context (what we discovered)

Laptop Claude measured real CPU-only loaded RAM for 3 candidate vision models on the Laptop host. Results are in `PHASE3_RAM_MEASUREMENT_LOG.md` (commit `5e14d37`). Key finding:

- **Current gold `qwen2.5vl:7b` loads to ~12.5 GiB** in CPU-only mode
- `giantqueen-b` VM has only **12 GB RAM ceiling**
- During vision inference, that VM spills ~0.5 GB into its own swap — works, but fragile and slow under load

**Measured replacement `qwen3-vl:8b`:**
- Real loaded RAM: **~6.1 GB** (less than half of gold)
- Vision quality: best of the three candidates tested on the same PNG (red square + blue circle + "Hello Hive" text) — identified colors, composition, full text, and background
- CPU inference time: ~53s per query (slower than GPU, acceptable for hierarchy tests per §4.0 "quality over speed")

`qwen3-vl:8b` in a 12 GB VM: 6.1 GB model + ~1 GB OS + ~1.5 GB inference = ~8.6 GB used → **3.4 GB comfortable headroom**. No swap spill.

## 2. What to change

**ONLY on `giantqueen-b` (10.0.0.16).** Leave DwarfQueens and Workers untouched — their vision models (`gemma3:4b` and `qwen3.5:0.8b`) already fit their VMs comfortably.

- Remove: `qwen2.5vl:7b`
- Install: `qwen3-vl:8b`

## 3. Step-by-step commands

All commands run from Desktop HOST terminal. SSH into `giantqueen-b` for the ollama commands.

```bash
# (a) SSH smoke-test
ssh -i ~/.ssh/phase3_ed25519 nir@10.0.0.16 'hostname && uname -a'
# Expect: giantqueen-b + kernel info

# (b) Baseline before changes
ssh -i ~/.ssh/phase3_ed25519 nir@10.0.0.16 'free -h && ollama list'
# Record the output in the ICQ reply and in the status file

# (c) Remove the old vision model
ssh -i ~/.ssh/phase3_ed25519 nir@10.0.0.16 'ollama rm qwen2.5vl:7b'
# Expect: "deleted 'qwen2.5vl:7b'"

# (d) Pull the new vision model (~6.1 GB download inside the VM)
ssh -i ~/.ssh/phase3_ed25519 nir@10.0.0.16 'ollama pull qwen3-vl:8b'
# Expect: "success" at the end. Takes a few minutes depending on the VM's bandwidth.

# (e) Verify the three models on disk now are: qwen3:8b + granite3.1-moe:3b + qwen3-vl:8b
ssh -i ~/.ssh/phase3_ed25519 nir@10.0.0.16 'ollama list'

# (f) Create a simple PNG on giantqueen-b for the vision test (Pillow should already be installed)
ssh -i ~/.ssh/phase3_ed25519 nir@10.0.0.16 'python3 -c "
from PIL import Image, ImageDraw
img = Image.new(\"RGB\", (512, 512), color=\"white\")
draw = ImageDraw.Draw(img)
draw.rectangle([50, 50, 250, 250], fill=\"red\", outline=\"black\", width=3)
draw.ellipse([280, 50, 480, 250], fill=\"blue\", outline=\"black\", width=3)
draw.text((120, 350), \"Hello Hive\", fill=\"black\")
img.save(\"/tmp/test_vision.png\")
print(\"saved\")
"'
# If Pillow is NOT installed in the VM, install via apt (already in the VM per PHASE3_PROVISION_VM.sh):
#   ssh ... 'sudo apt-get install -y python3-pil'
# If that fails for any reason, use imagemagick as a fallback:
#   ssh ... 'convert -size 512x512 xc:white -fill red -draw "rectangle 50,50 250,250" -fill blue -draw "circle 380,150 380,250" -fill black -draw "text 120,360 \"Hello Hive\"" /tmp/test_vision.png'

# (g) Real vision inference test with CPU-only (num_gpu: 0), capture the RAM footprint
ssh -i ~/.ssh/phase3_ed25519 nir@10.0.0.16 'bash -c "
echo === BASELINE ===
free -h
IMG_B64=\$(base64 -w0 /tmp/test_vision.png)
echo === INFERENCE ===
START=\$(date +%s)
curl -s http://localhost:11434/api/generate -d \"{\\\"model\\\":\\\"qwen3-vl:8b\\\",\\\"prompt\\\":\\\"describe this image briefly\\\",\\\"images\\\":[\\\"\$IMG_B64\\\"],\\\"stream\\\":false,\\\"options\\\":{\\\"num_gpu\\\":0}}\" | python3 -c \"import sys,json; d=json.load(sys.stdin); print(d.get(\\\"response\\\",\\\"ERROR\\\")[:200])\"
END=\$(date +%s)
echo Inference took \$((END-START))s
echo === PEAK RAM ===
free -h
echo === OLLAMA PS ===
ollama ps
echo === SWAP CHECK ===
swapon --show
"'
```

## 4. Success criteria

- Vision inference returns a sensible description mentioning red + blue + "Hello Hive" text
- `free -h` delta during load is ~6 GB (Laptop measured 6.1 GB)
- `ollama ps` SIZE is at most ~7 GB
- `swapon --show` shows **zero swap used** during and after inference (no spill)
- Inference wall-clock: expect 30-90 seconds on CPU, that is fine

If any of those criteria fail, STOP and ICQ Nir before continuing.

## 5. After success

1. Update `PHASE3_REBUILD_STATUS.md`: change `qwen2.5vl:7b (6.0 GB)` to `qwen3-vl:8b (6.1 GB CPU-measured loaded)` on the `giantqueen-b` line. Add a one-line note in the file history section pointing at this file as the source of the change.
2. Update the Smoke Test Results section: add a new row for qwen3-vl:8b confirming the three elements were seen.
3. `git add PHASE3_REBUILD_STATUS.md && git commit -m "Swap giantqueen-b vision from qwen2.5vl:7b to qwen3-vl:8b (real RAM fit)" && git push`
4. ICQ REPLY to Laptop Claude with the inference response text and the `free -h` peak numbers.

## 6. What NOT to do

- Do NOT change vision models on any DwarfQueen or Worker. They are not tight.
- Do NOT change the dense or MoE model on giantqueen-b. Only vision.
- Do NOT `ollama rm` any model that is not `qwen2.5vl:7b`. Especially do not touch the three Dense/MoE models that are already working.
- Do NOT rebuild or resize the VM. Only swap the vision model inside it.
- Do NOT delete `qwen2.5vl:7b` from the Desktop HOST Ollama (if it exists there). This change is scoped to the giantqueen-b VM only.

## 7. If something goes wrong

- SSH fails: check giantqueen-b is running via `sudo virsh list`. If not, `sudo virsh start giantqueen-b` and wait 60 sec for boot.
- `ollama pull` fails: check VM's internet (`curl -I https://ollama.com` from inside the VM). Retry.
- Inference returns nonsense: it may be that the image encoding broke over SSH quoting. Log the raw curl response, ICQ Nir before retrying.
- `free -h` shows swap increased during load: **stop, do not ship**. The model is bigger than Laptop's measurement suggested. ICQ Nir — we will need to re-measure or pick a different vision model.

## 8. Report format (ICQ REPLY back to Laptop Claude)

One message, ASCII only (no em-dashes, smart quotes, emojis, arrows). Template:

> `[DESKTOP VISION SWAP DONE] giantqueen-b new vision qwen3-vl:8b. Loaded RAM peak <X> GB. Inference wall <Y>s. Swap used during load: <Z>. Inference response text: <first 100 chars>. Status file updated, commit <short-sha>, pushed. Over.`

Then stop and wait for Laptop Claude's next direction.

---

*Canonical instruction for a single one-shot task. Edit in place if the commands need revision. Git is the time machine.*
