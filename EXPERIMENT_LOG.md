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

### What Needs Fixing
1. **Splitting prompt/JSON parsing** — RajaBee must produce exactly 2-4 clean component strings, not nested JSON
2. **The splitting prompt is too minimal** — after cleaning roleplay, it may need more structure guidance for JSON output

### Royal Honey (Final Answer)
The combined answer covered: wormholes, Alcubierre warp drive, light sails, nuclear pulse propulsion, fusion propulsion, antimatter propulsion, radiation shielding, life support (hibernation, closed-loop, ISRU), navigation (gravitational slingshots), and communication (quantum, laser, radio). Each with pros and cons. Coherent and comprehensive despite the splitting bug.

---

## For the Book (MadHoney)

These experiments belong in the chapter about real-world testing of the hierarchical system. Key narrative points:

1. **The architecture is real** — not simulated, not shortcuts, not in-process threads
2. **The Buzzing system prevents cheating** — boss tests employee, not self-reporting
3. **Small models (3B parameters) can do this** — imagine what larger models achieve
4. **The system is resilient** — start order doesn't matter, bees discover each other
5. **One website coordinates everything** — KillerBee is the matchmaker, no bee talks to another directly
6. **Proportional splitting means weaker machines still contribute** — they just get less work
