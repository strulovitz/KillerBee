# KillerBee Experiment Log

> Record of all real experiments for documenting in the MadHoney book.

---

## Experiment 1: First Real Distributed Hierarchy Test (2026-04-10)

### Setup
- **KillerBee website** running on localhost:8877
- **RajaBee**: llama3.2:3b, polling KillerBee for jobs
- **DwarfQueen (queen_alpha)**: llama3.2:3b, polling for components, splitting into subtasks
- **Worker 1 (worker_alpha)**: llama3.2:3b, polling for subtasks
- **Worker 2 (worker_bravo)**: llama3.2:3b, polling for subtasks
- **All 4 bees** as separate processes, communicating ONLY through KillerBee website
- **No direct HTTP** between any bees
- **Buzzing calibration** ran before real work: DwarfQueen tested both Workers, RajaBee tested DwarfQueen

### Architecture
```
RajaBee (process 1)
    │ (via KillerBee website)
    └── DwarfQueen queen_alpha (process 2)
            │ (via KillerBee website)
            ├── Worker worker_alpha (process 3)
            └── Worker worker_bravo (process 4)
```

### Buzzing Calibration Results
- worker_alpha: speed=10.0, quality=6.0, buzzing=60.0
- worker_bravo: speed=1.0, quality=8.0, buzzing=8.0
- Fractions: worker_alpha=0.882, worker_bravo=0.118 (sum=1.000)
- DwarfQueen queen_alpha: speed=10.0, quality=6.0, buzzing=60.0

### Test Question
"what place in the Solar System from the 3 following places, is the best for humans to try space colonization? please tell me pros and cons for each place: (1) Titan (Saturn's Moon) ; (2) Europa & Ganymede (Jupiter's Moons) ; (3) Ceres & the Asteroid Belt"

### Results
- **Total time**: 166.2 seconds
- **Total components**: 14 (3 top-level from RajaBee + 11 subtasks from DwarfQueen)
- **RajaBee split into 3 components** (one per celestial body — correct!)
- **DwarfQueen split each component into subtasks** for Workers
- **Workers processed subtasks in 2-4 seconds each**
- **DwarfQueen combined** Worker results per component
- **RajaBee combined** all 3 component results into final Royal Honey

### Quality Assessment
- **Context drift: MOSTLY FIXED** — answer actually gives pros and cons for each place (the original question was preserved through all levels)
- **Structure: GOOD** — clear sections for each location with pros/cons lists
- **Conclusion: PRESENT** — recommends Ceres & Asteroid Belt with reasoning
- **Known issue**: 4 of 14 subtasks were garbage (small model leaked prompt text as "Here are the two subtasks:" instead of actual subtask content). This is a prompt engineering / model quality issue that improves with smarter models.

### What This Proves
1. **Real distributed AI hierarchy works** — RajaBee → DwarfQueen → Workers, all through a central website
2. **No shortcuts** — every bee is a separate process with its own Ollama, all communication through KillerBee
3. **Buzzing calibration works** — boss tested employees, fractions calculated, proportional splitting applied
4. **Context preservation works** — original question flows through split AND combine at every level
5. **Dynamic discovery works** — bees can start in any order, find each other, calibrate, then work
6. **The website shows everything live** — auto-refreshing dashboard, job view with hierarchy and status

### Previous Test (same day, before Buzzing)
- Same setup but without calibration/proportional splitting
- Question: "which one should humans try to colonize first: the moon, Mars, Venus' atmosphere — pros and cons"
- Total time: 147.8 seconds
- Result quality was good but subtasks drifted (DwarfQueen created "design a landing site" instead of "list pros and cons")
- This led to implementing the original_task context passing fix

---

## Experiment 2: First REAL Cross-Machine LAN Test — Phase 2 (2026-04-11)

### Setup
- **Laptop (10.0.0.1, RTX 5090)**: KillerBee website (port 8877) + RajaBee (llama3.2:3b)
- **Desktop (10.0.0.5, RTX 4070 Ti)**: DwarfQueen queen_alpha + Worker alpha + Worker bravo (all llama3.2:3b, all sharing Desktop's Ollama)
- **Communication**: ALL through KillerBee website over LAN. No direct HTTP between bees.
- **First time EVER**: bees on different physical machines

### Architecture
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

### Buzzing Calibration — 5 Bugs Found and Fixed During Setup

The calibration system was debugged extensively before this test could run. Full details in GiantHoneyBee/BUZZING_BUGS.md. Summary:

| Bug | Problem | Fix |
|-----|---------|-----|
| Bug 1 | Simultaneous calibration (workers compete for Ollama) | Sequential calibration |
| Bug 2 | Speed formula destroys actual ratios | Proportional: `10 * fastest/elapsed` |
| Bug 3 | Ollama prompt cache makes 2nd worker 2-3x faster | Dummy reset question before each measurement |
| Bug 4 | Worker prompt "You are a worker bee" → LLM role-plays as insect | Remove roleplay from all prompts |
| Bug 5 | 5s polling interval adds random noise bigger than signal | 1s polling + 3 big questions + averaged scores |

**"The Worker Bee Incident" (Bug 4)**: The funniest bug of the entire project. The LLM apologized that its expertise lies in nectar and pollen when asked about ancient Pompeii. Hours of cache/GPU investigation — the answer was one line in the prompt. MUST go in the MadHoney book as comic relief.

### Final Calibration Results (Round 8, after all 5 fixes)
- **DwarfQueen calibrating Workers**: 3 rounds of big questions, 1s polling
  - worker_alpha: avg speed = ~equal, quality = 8.0, fractions: 0.523
  - worker_bravo: avg speed = ~equal, quality = 7.3, fractions: 0.477
  - Nearly equal for identical workers — calibration is fair
- **RajaBee calibrating DwarfQueen**: 3 rounds, all quality 8.0, speed 10.0

### Test Question
"what solutions and concepts can humans use to do Interstellar travel (to go from our solar system to the nearest solar system which is Alpha Centauri? please give pros and cons for each."

### Results
- **Total time**: 2780.6 seconds (~46 minutes)
- **Total components**: 448 (42 top-level from RajaBee + 406 subtasks from DwarfQueen)
- **Status**: COMPLETED — Royal Honey delivered

### Known Issues
- **RajaBee split into 42 components instead of 2-4.** The LLM returned a nested JSON with "description", "pros", "cons" as separate entries. Each JSON field became a separate component. This is a splitting/JSON parsing bug — NOT an architecture bug.
- **448 total subtasks is way too many.** With proper 2-4 splitting, this would be ~20-30 subtasks total. The excess components wasted time and produced redundant work.
- **The final answer is still coherent** despite the bad splitting — the combining step recovered well. But this masks the waste.

### What This Proves
1. **Cross-machine hierarchy WORKS** — Laptop ↔ Desktop over real LAN, real network
2. **All communication through KillerBee** — no direct HTTP between any bees
3. **Buzzing calibration works fairly** — 0.523 vs 0.477 for identical workers after thorough testing
4. **The system is resilient** — even with 42 components (a bug), it completed successfully
5. **Two different GPUs coordinated** — RTX 5090 (Laptop) orchestrating, RTX 4070 Ti (Desktop) working

### What Was Fixed After This Run
1. **Splitting** — replaced JSON-based splitting with smart_splitter.py (see Experiment 3)
2. **Prompt cleanup** — removed all roleplay and JSON format instructions from all prompts

### Royal Honey (Final Answer)
The combined answer covered: wormholes, Alcubierre warp drive, light sails, nuclear pulse propulsion, fusion propulsion, antimatter propulsion, radiation shielding, life support (hibernation, closed-loop, ISRU), navigation (gravitational slingshots), and communication (quantum, laser, radio). Each with pros and cons. Coherent and comprehensive despite the splitting bug.

---

## Experiment 3: Phase 2 LAN Test — SUCCESSFUL (2026-04-11)

### What Changed Since Experiment 2
- **smart_splitter.py**: Replaced JSON-based splitting. LLM writes however it wants (numbered list, bullets, headers, paragraphs, anything). Parser detects the format automatically by looking for repeating non-alphanumeric patterns at line starts. Prefers less common patterns (section headers) over more common ones (sub-item bullets). Tested with 12 format types.
- **All prompts cleaned**: No roleplay ("You are a worker bee"), no motivation ("thoroughly and concisely"), no format instructions ("Return ONLY a JSON array"). Just the question and the data.
- **Thorough calibration**: 3 big questions, 1-second polling, averaged scores across all rounds.
- **Dummy cache reset**: Before each calibration measurement to flush LLM prompt cache.

### Setup
Same as Experiment 2:
- **Laptop (10.0.0.1, RTX 5090)**: KillerBee website (port 8877) + RajaBee (llama3.2:3b)
- **Desktop (10.0.0.5, RTX 4070 Ti)**: DwarfQueen queen_alpha + Worker alpha + Worker bravo (all llama3.2:3b)
- **Communication**: ALL through KillerBee website over LAN

### Buzzing Calibration
- Workers: 0.500 vs 0.500 (perfect for identical hardware)
- DwarfQueen quality: all 8.0 (6 out of 6 judgments)
- RajaBee calibrating DwarfQueen: quality 6.0 (one round got 2.0 because the LLM confused "buzzing calibration" with hardware troubleshooting — known bug, needs fix)

### Test Question
Same as Experiment 2: "what solutions and concepts can humans use to do Interstellar travel (to go from our solar system to the nearest solar system which is Alpha Centauri? please give pros and cons for each."

### Results

| | Experiment 2 (broken) | Experiment 3 (fixed) |
|---|---|---|
| Components | 448 | 20 |
| Total time | 2780.6s (46 min) | 179.9s (3 min) |
| Splitting | 42 from RajaBee (nested JSON bug) | 5 from RajaBee (4 parts + intro) |
| Subtasks | 406 (redundant waste) | 15 (2-3 per component) |

### Splitting Detail
RajaBee split into 5 components:
1. Intro line ("Here's a suggested breakdown...")
2. Part 1: Propulsion Concepts (light sails, nuclear pulse, fusion, antimatter)
3. Part 2: Interstellar Travel Methods (generation ships, hibernation, solar sails)
4. Part 3: Interstellar Travel Challenges (radiation, distance, life support)
5. Part 4: Alpha Centauri-Specific Considerations (environment, distance)

DwarfQueen split each component into 2-3 subtasks for the 2 Workers.

### Royal Honey (Final Answer)
Comprehensive answer covering: propulsion concepts (light sails, nuclear pulse, fusion, antimatter with pros/cons), travel methods (generation ships, hibernation, solar sails), challenges (radiation, distance, life support), Alpha Centauri specifics, communication (antennas, quantum), navigation (gravitational slingshots), and mission design (phased missions, swarm missions). All with pros and cons.

### What This Proves
1. **smart_splitter works** — LLM writes naturally, parser detects the format, proper 4-5 components instead of 42
2. **15x faster** with proper splitting (3 min vs 46 min)
3. **20 total components** instead of 448 — no wasted work
4. **Clean prompts work** — no roleplay, no JSON, no motivation. Just the question.
5. **Cross-machine hierarchy confirmed** — Laptop orchestrates, Desktop processes, results flow back

### Known Issues Still Open
1. **"Buzzing" word leaks into calibration context** — the LLM sees "buzzing calibration" and confuses it with hardware troubleshooting. Got quality=2 on one round because of this. Needs fix.
2. **Intro line becomes a component** — "Here's a suggested breakdown..." gets treated as component #1. Harmless but adds unnecessary work.

---

## Night heartbeat — 2026-04-18 (Phase 3 first run)

- `00:38 UTC` **desktop-claude**: 7 Desktop bees alive, giantqueen-b calibrating. Topology helper confirmed working (GQ-b sees 2 DwarfQueens, no claim race). Waiting for Raja cluster-wide calibration.

---

## For the Book (MadHoney)

These experiments belong in the chapter about real-world testing of the hierarchical system. Key narrative points:

1. **The architecture is real** — not simulated, not shortcuts, not in-process threads
2. **The Buzzing system prevents cheating** — boss tests employee, not self-reporting
3. **Small models (3B parameters) can do this** — imagine what larger models achieve
4. **The system is resilient** — start order doesn't matter, bees discover each other
5. **One website coordinates everything** — KillerBee is the matchmaker, no bee talks to another directly
6. **Proportional splitting means weaker machines still contribute** — they just get less work
7. **"The Worker Bee Incident"** — MUST INCLUDE as comic relief. See MadHoney/BOOK_PLAN.md Chapter 10.
8. **smart_splitter** — let the LLM write naturally instead of forcing formats. A general principle: adapt to the tool, don't force the tool to adapt to you.
9. **5 bugs found and fixed in Buzzing** — real engineering, real debugging, real solutions. Each bug has a story.
10. **15x improvement** from fixing splitting alone — the difference between a good architecture and good implementation

---

## Night of 2026-04-18 — Phase 3 (in progress)

### Pre-run state (03:34)

- All 15 VMs up (8 Laptop, 7 Desktop).
- KillerBee website at http://10.0.0.8:8877, swarm id=1 "Phase 3 Hive", depth=4.
- GiantHoneyBee + HoneycombOfAI cloned on all 15 VMs.
- Bee clients patched with KILLERBEE_MODEL env + CLI override (commit 4d9625d).
- Topology helper (commit 38dc332) applied: race fixed, 7 parent_member_id rewrites.

### Bee bring-up (03:26-03:34)

- First Laptop fire: bees registered but initial claim race did happen. queen_dwarf_b2 grabbed worker_a1..a4; queen_dwarf_b1 grabbed worker_b3..b4.
- Desktop disclosed zombie bees from pre-sleep launch; all pkill'd clean.
- Topology helper run on Laptop host, 7 parents corrected.
- Laptop bees killed and restarted with PYTHONUNBUFFERED=1 for live logs. Restart cleanly used the corrected topology on second registration.
- rajabee log confirms: found 2 existing giant_queen subordinates, no unassigned, starting calibration with qwen3:14b.
- Desktop pending restart of 7 bees.

### Night heartbeat (03:44, Laptop)
- All 15 bees alive after kill-and-restart with PYTHONUNBUFFERED=1. Desktop confirmed 7/7 running, Laptop 8/8 running.
- Topology (commit 38dc332) applied clean, no duplicate rows.
- Calibration in progress: Raja qwen3:14b generating Q1, GQ-a qwen3:8b generating Q1, DQ-a1 phi4-mini already past Q3 generation into Round 1.
- One transient blip: dq_a1 hit brief Network unreachable retries during Laptop Flask restart window, moved past.
- Ollama on rajabee 554% CPU, 9.4 GB resident, qwen3:14b q4_K_M loaded.
- Expected Raja calibration completion 20-40 min from now. Q1 Mars Colony follows.

