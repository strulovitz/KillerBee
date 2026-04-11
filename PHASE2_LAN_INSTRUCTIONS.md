# Phase 2 LAN Test — Desktop Instructions

> **Written:** 2026-04-11 by Laptop Claude Code
> **For:** Desktop Claude Code — YOU must guide Nir step by step on the Desktop machine
> **Status:** This is a REAL test. DO NOT fabricate results. DO NOT claim success until you see actual output.

---

## What Is This Test?

The FIRST REAL cross-machine test of the hierarchical AI system.

- **Laptop (10.0.0.1):** Runs KillerBee website (port 8877) + RajaBee
- **Desktop (10.0.0.5):** Runs 1 DwarfQueen + 2 Workers

All bees communicate ONLY through the KillerBee website. No direct HTTP between bees. The Desktop bees will reach the KillerBee website on Laptop over the LAN.

## Architecture

```
LAPTOP (10.0.0.1)                    DESKTOP (10.0.0.5)
┌──────────────────────┐             ┌──────────────────────┐
│ KillerBee Website    │             │                      │
│ (port 8877)          │◄──── LAN ───│ DwarfQueen           │
│                      │             │ (queen_alpha)        │
│ RajaBee              │             │                      │
│ (raja_nir)           │             │ Worker worker_alpha  │
│                      │             │ Worker worker_bravo  │
└──────────────────────┘             └──────────────────────┘
```

## What Desktop Claude Must Do

You (Desktop Claude) must guide Nir through opening command prompt windows on the Desktop and typing commands into each one. Give him ONE command at a time, wait for confirmation, then give the next.

Nir has ADD — give ultra-detailed, copy-paste-ready instructions. Do things yourself when possible, but when terminal windows are needed, guide him step by step.

### Prerequisites (verify these first)

1. Ollama is running on Desktop with llama3.2:3b available
2. GiantHoneyBee and KillerBee repos are cloned and up to date (`git pull` both)
3. HoneycombOfAI repo is cloned (needed by GiantHoneyBee for imports)
4. Python packages installed: `pip install requests` (the clients only need `requests`)
5. Desktop can reach Laptop at 10.0.0.1:8877 — test with: `curl http://10.0.0.1:8877` (should get HTML back)

### If Desktop CANNOT reach Laptop port 8877

Nir needs to add a Windows Firewall rule on the LAPTOP (not Desktop). Laptop Claude will handle this. Send a WaggleDance message saying "Desktop cannot reach Laptop port 8877, please add firewall rule."

### Desktop Terminals Needed: 3

**Terminal 1 — DwarfQueen (queen_alpha)**
```
cd C:\Users\nir_s\Projects\GiantHoneyBee
python dwarf_queen_client.py --server http://10.0.0.1:8877 --swarm-id 1 --username queen_alpha --password password --model llama3.2:3b --ollama-url http://localhost:11434
```

**Terminal 2 — Worker Alpha (worker_alpha)**
```
cd C:\Users\nir_s\Projects\GiantHoneyBee
python worker_client.py --server http://10.0.0.1:8877 --swarm-id 1 --username worker_alpha --password password --model llama3.2:3b --ollama-url http://localhost:11434
```

**Terminal 3 — Worker Bravo (worker_bravo)**
```
cd C:\Users\nir_s\Projects\GiantHoneyBee
python worker_client.py --server http://10.0.0.1:8877 --swarm-id 1 --username worker_bravo --password password --model llama3.2:3b --ollama-url http://localhost:11434
```

### Start Order

Start order does NOT matter (bees discover each other). But recommended:
1. Workers first (they just poll and wait)
2. DwarfQueen next (discovers Workers, runs Buzzing calibration)
3. Tell Laptop Claude all 3 are running — Laptop will then start RajaBee and submit a job

### What To Watch For

- Each bee should print a banner showing it connected to KillerBee and Ollama
- Workers should say "Polling... no work available"
- DwarfQueen should run Buzzing calibration (discover Workers, test them, calculate fractions)
- When the job arrives: DwarfQueen gets a component, splits into subtasks, Workers claim and process them
- Results flow back: Workers → DwarfQueen → (via KillerBee) → RajaBee on Laptop

### When Done

Send a WaggleDance REPLY to Laptop Claude confirming:
1. All 3 bees started successfully (or what errors occurred)
2. Whether Buzzing calibration completed
3. Whether the job was processed (once Laptop submits one)
4. Any errors or issues

```
curl -s -X POST http://10.0.0.1:8765/send -H "Content-Type: application/json" -d "{\"from\":\"desktop-claude\",\"type\":\"REPLY\",\"message\":\"YOUR STATUS UPDATE HERE\"}"
```

## IMPORTANT RULES

1. **DO NOT fabricate results.** Only report what you actually see in the terminal output.
2. **DO NOT claim success** unless the bees actually processed a job end-to-end.
3. **If something fails**, report the exact error. We fix it together.
4. **Guide Nir one step at a time.** He has ADD. One command per message. Wait for confirmation.
5. **All passwords are `password`** (from seed_data.py — this is a test environment).
