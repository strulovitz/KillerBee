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

## For the Book (MadHoney)

These experiments belong in the chapter about real-world testing of the hierarchical system. Key narrative points:

1. **The architecture is real** — not simulated, not shortcuts, not in-process threads
2. **The Buzzing system prevents cheating** — boss tests employee, not self-reporting
3. **Small models (3B parameters) can do this** — imagine what larger models achieve
4. **The system is resilient** — start order doesn't matter, bees discover each other
5. **One website coordinates everything** — KillerBee is the matchmaker, no bee talks to another directly
6. **Proportional splitting means weaker machines still contribute** — they just get less work
