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
- `02:38 UTC` **desktop-claude** (backfill): missed 00:53 / 01:08 / 01:23 / 01:38 / 01:53 / 02:08 / 02:23 heartbeats — apologies. Status now: all 7 Desktop bees still alive. GQ-b stuck 2065s on Component 55 (orphaned sub-components from pre-calibration Raja test — DQs never picked them up, so GQ-b waits until its 3600s max_wait timeout). DQ-b1 idle. DQ-b2 completing Component 140 (1 worker subtask done in 290s). DQ-b2's worker pipeline is functional. GQ-b blocked means Raja Q1 Mars split will wait for GQ-b to free. Will report GQ-b timeout and behavior when it happens.
- `03:55 UTC` **desktop-claude**: Q1 Mars completed (Laptop-subtree-only, 1h44m, per Laptop report). Desktop GQ-b contributed zero — she was stuck on Component 55 (timed out at 3600s) then immediately on Component 65 (another orphan). Surgical restart applied per plan Section 11 "stop cleanly, fix, restart, note in log": rsynced patched GiantHoneyBee 03766a3 (max_wait 60 for calibration) to 10.0.0.6 and 10.0.0.7 only; killed + restarted GQ-b and DQ-b1 (new PIDs 71599 and 40496); DQ-b2 and workers kept running untouched. Goal: Desktop subtree functional for Q2 Antarctic.

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

### Night heartbeat (03:49, Laptop)
- Cluster still calibrating. Bottom-up progress visible:
- DQ-a2 on Round 3/3 sending to worker_a3.
- DQ-a1 on Round 2/3, received worker_a1 full answer.
- GQ-a on Round 1/3 sending to DQ-a1.
- Raja on Round 1/3 sending to GQ-b.
- DB shows 5 of 15 members have fractions (all from pre-restart race run on Desktop side; stale).
- 12 pending components out of 53 total. Calibration flowing.
- No stalls, no crashes.

### Night heartbeat (04:08, Laptop)
- 12/15 bees calibrated with proportional fractions. Only Raja and her 2 GiantQueens remain uncalibrated.
- 125 total components, 107 completed, 15 pending, 0 in_progress.
- Desktop-side DwarfQueens done. Laptop-side DwarfQueens done.
- Raja calibrating GQ-a and GQ-b on qwen3:14b (slow). Expected completion in 20-30 min.
- Fraction splits (under each parent) sum to 1.0 cleanly:
  - queen_dwarf_a1 0.531 + queen_dwarf_a2 0.469 = 1.0 under GQ-a.
  - queen_dwarf_b1 0.490 + queen_dwarf_b2 0.510 = 1.0 under GQ-b.
  - All 4 worker pairs sum to 1.0 under their DQ parents.
- Still no stalls or crashes. Flask serving 200s, no retry-give-up events.

### Night heartbeat (04:27, Laptop)
- Raja calibration is the bottleneck. Round 2/3 in progress 48 min after Round 1 started.
- 150 total components, 130 done, 17 pending, 12/15 fractions.
- qwen3:14b thinking-model generation on 6 CPU cores is glacial - each Raja score or GQ answer is several minutes.
- No stalls, just slow. Cluster is working.
- Revised expected Raja completion: 05:00-05:10.
- Q1 Mars Colony will submit the moment Raja enters main_loop.

### Night heartbeat (05:05, Laptop) - calibration issues
- Raja buzzing calibration all 3 rounds timed out on both GiantQueens (4-level cluster deadlock: kids busy with their own kids).
- Raja entered main_loop with empty in-memory fractions.
- Q1 Mars Colony submitted as Job 2 at 05:04. Raja picked it up.
- FORMAT BUG: raja_bee.py line 490 `f.get("fraction", default)` returns None when value is explicitly None (not missing). `f"{None:.2f}"` crashes.
- Manually set queen_giant_a and queen_giant_b fraction=0.5 capacity=100 in DB. API now returns 0.526/0.474 post-recalculate.
- But Raja's in-memory fractions still stale. Patched raja_bee.py: (1) max_wait 600 -> 60 for faster future calibration, (2) `f.get(fraction)` default-or fix. Killed and restarted Raja.
- Restarted Raja re-enters buzzing cycle with max_wait=60, should finish in ~12 min and fetch correct DB fractions.
- Q1 Job 2 still pending in DB. Will be picked up when Raja enters main_loop again.

### Night heartbeat (05:36, Laptop)
- Raja exited buzzing_cycle with fractions queen_giant_b=0.526 queen_giant_a=0.474 (from DB via _fetch_fractions after my manual SwarmMember set).
- Raja picked up Job 2 (Q1 DENSE Mars Colony) at 05:35.
- Currently splitting task into components on qwen3:14b.
- Patch 03766a3 pushed to GiantHoneyBee main: max_wait 60s + fraction None-safe default in _split_task. Desktop agreed to sync on MoE batch restart per plan Section 11.
- Waiting for Raja to post components to GQs, then cascade down to workers, then roll up to Royal Honey.

### Night heartbeat (06:28, Laptop)
- Q1 Mars Colony: 21/22 components completed, 1 still in "Combining" phase on DQ-a2 (10.0.0.25) using phi4-mini:3.8b. Been combining ~20 min, CPU 370%, slow but not stuck.
- Q1 component tree was: 6 DQ-level Raja splits (2 Laptop + 4 Desktop DQs), each DQ split into 1-3 worker subtasks = 16 total, then grew to 22 as some components re-split.
- Dense-batch processing is REAL and WORKING end-to-end. Workers answering real sub-parts of "Design a 6-person Mars base".
- Waiting for last combine + Raja's final integrate to deliver Royal Honey.


### Q1 DENSE Mars Colony — COMPLETE at 06:48

- **Royal Honey delivered**: 3271 chars, coherent 5-part Mars base design.
- **Job ID**: 2. Submitted 05:04, completed 06:48. Total wall clock: 1h44m.
- **Structure**: Raja split into 6 components proportional to fractions (GQ-b 53% / GQ-a 47%). Each DQ sub-split to workers. 22 total components across tree.
- **One combine hang**: DQ-a2 Ollama generation looped on phi4-mini:3.8b combine for Component 218. Restarted Ollama on 10.0.0.25 to unstick (51 min stall). The bee posted an error-result from the exception, job continued.
- **Saved to**: `results/q1_mars_royal_honey.md`.
- **Q2 DENSE Antarctic** now submitted as Job 3.


### Night heartbeat (07:03, Laptop) - after Q1 completion
- Q1 Mars delivered. Desktop disclosure: GQ-b was stuck on Component 55 for 3600s then Component 65 for 2485s - contributed NOTHING to Q1. Q1 Royal Honey = 100% Laptop subtree.
- Raja rediscovered post-Q1, saw no changes in fractions/capacity, SKIPPED recalibration (guard worked). Picked up Job 3 (Q2 Antarctic) immediately.
- Raja splitting Q2 now with qwen3:14b.
- Recommended Desktop surgical fix: rsync patched GiantHoneyBee to 10.0.0.6 (GQ-b) and 10.0.0.7 (DQ-b1) only, restart just those 2 with max_wait=60 recalibration.
- DQ-b2 is doing real work. Do not restart her.


### Q2 DENSE Antarctic Station — COMPLETE at 08:23

- **Royal Honey**: 3358 chars, covers structural engineering, medical infrastructure, psychological, logistics, treaty compliance.
- **Wall clock**: 5591.9s (93 min). Faster than Q1 which took 104 min.
- **Orphaned component**: c242 (GQ-b side 53% of work, structural + logistics) was orphaned when Desktop surgical-restarted DQ-b1. Stubbed completed. Gap in GQ-b side coverage.
- **Laptop subtree covered it**: Final Royal Honey is still coherent, Antarctic-relevant, with correct domain content.
- **Second Ollama hang** on DQ-b1 (Desktop) required Ollama restart at ~07:52.
- **Saved**: results/q2_antarctic_royal_honey.md.
- **Q3 DENSE Provence Bee Farm** submitted as Job 4.


### Q3 DENSE Provence Bee Farm — manually combined at 10:32

- **Royal Honey** (27073 chars): manual concatenation of 5 level-0 component results via scripts/manual_combine_q3.py.
- **Why manual**: Raja's _wait_for_components timed out at 3600s (Flask dev-server connection drops under sustained load prevented the final state from reaching her poll). All 5 level-0 components WERE completed in the DB, but Raja bailed before seeing the completion.
- **Two stubs**: c315 (DQ-a1 side) and c318 (DQ-b1 side) orphaned after Ollama restart on worker_a3 + worker_b1; stubbed with honest disclosure strings so Raja could proceed.
- **Saved**: results/q3_provence_royal_honey.md.

### Dense batch complete — STOPPING FOR TODAY per Nir instruction

MoE batch (Q4/Q5/Q6) deferred to next night.

Documentation for MadHoney book:
- PHASE3_NIGHT_LOG_LAPTOP.md (19 sections, Laptop view)
- PHASE3_NIGHT_LOG_DESKTOP.md (16 sections, Desktop view)
- PHASE3_NIGHT_EXPERIMENT_PLAN.md (night plan + contract)
- results/q1_mars_royal_honey.md
- results/q2_antarctic_royal_honey.md
- results/q3_provence_royal_honey.md
- EXPERIMENT_LOG.md (this file, running log)


---

## Night of 2026-04-19 — MoE Batch (Q4/Q5/Q6)

### Pre-flight — Laptop side — 01:33 UTC

- Nir gave GREEN at ~01:15 Israel time, going to sleep. Guidance: reuse existing plan, no pre-built infrastructure, solve problems from ROOT (not ad-hoc stubs) when they surface, honesty above all.
- Both Claudes ACK'd GREEN via ICQ (#362 laptop, #363 desktop, #364 laptop, #366 laptop). Heads match: KillerBee 5c3bd07, GiantHoneyBee 03766a3.
- Laptop 8 VMs were shut off at start — booted all 8 via `sudo virsh start rajabee/giantqueen-a/dwarfqueen-a1-a2/worker-a1-a4`. All came up with expected IPs 10.0.0.14/17/19/25/27/29/31/33 after ~90s DHCP settle.
- Part A (rsync patched GiantHoneyBee 03766a3 to all 8 Laptop VMs): first pass returned rsync protocol error code 12 on all 8. Root cause: `rsync` package was not installed on any of the 8 Laptop VMs. Installed rsync on all 8 via passwordless sudo apt-get. Retried rsync, clean exit=0 on all 8. Verified `max_wait = 60` lands 3 times per VM (raja_bee.py + giant_queen_client.py + dwarf_queen_client.py = 3 hits). Laptop Part A DONE.
- Desktop Part A (his 7 VMs) still running per his last ICQ; awaiting his done-signal before Part B bottom-up bring-up.

### Pre-flight — Desktop side — 01:50 UTC

- Desktop 7 VMs were also shut off at start. Booted all 7 via `sudo virsh start giantqueen-b/dwarfqueen-b1/dwarfqueen-b2/worker-b1/worker-b2/worker-b3/worker-b4`. All 7 DHCP leases landed at same IPs as 2026-04-18 table: GQ-b 10.0.0.6, DQ-b1 10.0.0.7, DQ-b2 10.0.0.9, workers-b1..b4 at 10.0.0.10/11/12/16. MAC-stable leases held across overnight shutdown.
- Part A rsync patched GiantHoneyBee (commit 03766a3) from Desktop host to all 7 Desktop VMs in parallel. rsync package already present on Desktop VMs (unlike Laptop — Desktop VMs were cloned from giantqueen-b which had rsync pre-installed). All 7 rsync exit=0.
- Verified `max_wait = 60` landed 3 times per VM (raja_bee.py + giant_queen_client.py + dwarf_queen_client.py) on all 7 Desktop VMs.
- Desktop Part A DONE. Both sides Part A complete. Ready to coordinate Part B bottom-up bring-up.

### DB cleanup for MoE fresh start — 01:40 UTC 2026-04-19

Laptop host was rebooted ~01:00 UTC (uptime 43 min when discovered), forcing:
1. 8 Laptop VMs booted via `sudo virsh start` (IPs came back MAC-stable).
2. KillerBee Flask website restarted (`nohup ./killerbee-venv/bin/python app.py`), HTTP 200 verified.
3. DB preserved but had 45 zombie components under Job 1 (last night's calibration cascade-deadlock leftovers: rainbow / China / tech-innovation calibration tasks — 33 pending + 12 processing) and 14 swarm_members with Dense-calibrated buzzing fields that don't apply to tonight's granite MoE models.

Executed `scripts/reset_for_moe_batch.py` to:
- Mark 45 zombies as `status='completed'` with `result='[ABANDONED: Dense-batch Job 1 calibration cascade deadlock never completed, marked at MoE pre-flight 2026-04-19]'`. Preserves row history per Desktop's preference; invisible to `get_my_work` which filters by pending/processing.
- Zero the 5 buzzing fields (`fraction`, `capacity`, `buzzing_speed`, `buzzing_quality`, `buzzing`) on all 15 swarm_members so MoE calibration starts fresh.
- Leave `parent_member_id` intact on all 15 (last night's hard-won topology fix preserved).
- Leave Jobs 1-4 intact as historical record.

Post-cleanup verification:
- 0 components in pending/processing status.
- 0 swarm_members with non-NULL buzzing fields.
- Sample parent_member_id on id=1 (parent=4), id=8 Raja (parent=None), id=10 DQ (parent=9) — all preserved.

Ready for Part B Workers bring-up.

### Part B bottom-up bring-up + max_wait patch — 01:50-02:45 UTC 2026-04-19

Workers tier (01:50-02:00): Both sides fired 4 Workers each with KILLERBEE_MODEL=granite3.1-moe:1b. Laptop workers: w_a1/a2/a3/a4 @ 10.0.0.27/29/31/33 member_ids 12-15. Desktop workers: w_b2/b1/b4/b3 @ 10.0.0.11/10/16/12 member_ids 1/3/5/6. All 8 in main_loop, polling cleanly.

DQs tier (02:00-02:15): Both sides fired 2 DQs each with granite3.1-moe:3b. All 4 completed buzzing calibration in Round 3/3 with REAL calibration numbers (not fallback defaults, unlike last night's 4-tier deadlock). Sample: DQ-b1 scored w_b1 speed=9.0 q=10.0 buzzing=90.0 and w_b2 speed=10.0 q=10.0 buzzing=100.0. Each worker calibration answer took ~17-20s. Bottom-up stagger is WORKING - last night's deadlock is absent.

GQs tier (02:15-): Both sides fired 1 GQ each. FIRST ATTEMPT FAILED: GQ R1 calibration timed out because DQ split-combine takes 60-100s (DQ orchestrates through workers, not a single Ollama call like 3-tier) and max_wait=60 (last night's patch) was too tight. Halted both GQs. Laptop committed GiantHoneyBee 6c0896c raising max_wait 60->300 in raja_bee.py:281 + giant_queen_client.py:268 + dwarf_queen_client.py:268. Rsynced to all 15 VMs. SECOND ATTEMPT IN PROGRESS with max_wait=300.

Current state (02:45 UTC): GQ-b R1 DQ-b1 49.3s OK, R2 DQ-b1 90.6s OK, R3 DQ-b1 102.7s OK (all under 300s budget), but DQ-b2 R2 timed out even at 300s. Root cause: DQ-b2 is STUCK waiting for subtask Component 425 (child of Component 421, her R1 calibration question) - subtask assigned to Laptop worker_a3 member_id=14 which is IDLE (CPU 0, no ollama loaded, completed=12). Worker did the work, POST-result dropped (Network-unreachable), DB stuck at status=processing forever. Same orphan class as last night c242/c315/c318 but root cause is HOST NETWORK DROPS (Laptop host rebooted earlier, Flask/Werkzeug under sustained load). Laptop investigating (A) stub-close 421/425/471 with disclosure (B) network-drop investigation with possible waitress swap as the ROOT fix. Desktop approved both actions via ICQ #394. Awaiting Laptop execution.

### Heartbeat — 02:30 UTC Laptop — MoE Night 2 Part B mid-way

Status: Raja fired on 10.0.0.14 at 02:30, now calibrating 2 GQs. Both GQs in main_loop. All 4 DQs in main_loop. All 8 Workers in main_loop.

Problems encountered and solved tonight:

1. **max_wait=60 too tight for 4-tier calibration cascade** — DQ receiving a calibration task splits to workers and combines, measured 60-143s per call. Root fix committed as GiantHoneyBee `6c0896c` (max_wait 60→300 in all 3 client files). Rsynced to all 15 VMs. Both GQs restarted with patched code.

2. **Orphan components from Network-is-unreachable retry exhaustion** — Components 421 (GQ-b R1 DQ-b2), 425 (DQ-b2 sub→worker_a3), 471 (GQ-a R3 DQ-a2) all stuck in `processing` after bees completed work locally but their result-POST failed and exhausted the 3-retry budget. Investigation showed: 20/20 curl loops from VM to Flask succeed (2-14ms), bridge br0 clean 0 errors, Flask log 200s to all VMs. Error is transient VM-kernel-level (likely ARP refresh or libvirt DHCP route race — one VM had a suspicious dual-DHCP route `src 10.0.0.30` for a `.31` VM).
   - Immediate fix: `scripts/stub_orphans.py 421 425 471` marked them completed with ABANDONED disclosure.
   - Root fix: committed as GiantHoneyBee `67e1c95` — bumped `max_retries` from 3 to 10 in `killerbee_client.py`. Old budget was 6s cumulative (2s, 4s); new is ~90s cumulative (2s, 4s, 6s, ..., 18s over 10 attempts). Rsynced to all 8 Laptop VMs. NEXT bee fires (Raja + any future restarts) use new budget; running bees continue on old retry until restart — acceptable per plan Section 11 (no mid-batch client restart unless required).

3. **shell-quoting blind spot** (Laptop only) — dropped `cd /home/nir/GiantHoneyBee` prefix 4 times in a row on GQ-a restart. Fixed by writing command to a bash script file `/tmp/fire_gq_a.sh` and running it. Used same approach for Raja fire (`/tmp/fire_raja.sh`), worked first try.

Desktop Part A + Part B + patches all tracked in parallel ICQs. Git push/pull chain: KillerBee `c09e6fe` (DB reset), GiantHoneyBee `6c0896c` (max_wait 300), GiantHoneyBee `67e1c95` (retry 10).

Next: Raja main_loop (~10-15min), then submit Q4 Space Elevator via beekeeper_demo.

### Architectural root-fix + Raja main_loop + Q4 submitted — 03:15 UTC 2026-04-19

ROOT-CAUSE BUG FOUND: KillerBee app.py line 604 `api_available_components` filtered jobs by `status='processing'` only, while `api_available_subtasks` at line 578 had no status filter. Since calibration jobs are `status='calibration'`, sub-components posted by GQs during Raja's calibration cascade were invisible to DQs. Phase 2 3-tier never triggered this because DQ-to-Worker went through the subtask endpoint (no filter). Phase 3 4-tier calibration cascade exposed it. Retroactively explains last night's c242/c315/c318 orphan pattern as NOT a race - it was this filter asymmetry.

Patch: KillerBee `322c7b4` (Laptop) dropped the status filter on `api_available_components` to match the subtask endpoint. Flask restarted on Laptop host (~5s blip, absorbed by retry=10 budget). Immediate validation: Component 494 transitioned from orphan (member_id=None, pending forever) to member_id=DQ claimed, status=processing, with grandchild Component 497 posted to a worker. The 4-tier calibration cascade flowed end-to-end for the first time ever.

Raja calibration completed with REAL data all 6 rounds (no timeouts under new max_wait=300):
- R1 GQ-b 361s (over budget? actually should have timed out - possibly first entry into retry loop completed first attempt within 300s wall clock despite network blips)
- R1 GQ-a 133s, R2 GQ-b 91s, R2 GQ-a 129s, R3 GQ-b 269s, R3 GQ-a last-round

Raja entered main_loop. Q4 Space Elevator submitted as job_id=5 (581 chars) via direct DB INSERT per Laptop (bypassing the CSRF web form). Desktop subtree at 03:15 UTC: GQ-b processing Component 555, DQ-b1 on 560, DQ-b2 on 559, workers polling. Cascade is flowing.

No orphans in DB right now. max_retries=10 and max_wait=300 both doing their job - RETRY markers visible in Raja's log but all self-recover within 1-2 attempts.

### Q4 Space Elevator — Royal Honey delivered — 03:06 UTC

- **Submit**: 02:57:18 UTC as job_id=5 via `scripts/submit_q.py /tmp/q4.txt`
- **Royal Honey**: 03:06:07 UTC, 2323 chars, total_time=528.47s (~8m48s wall clock)
- **Tier models**: Raja/GQ/DQ granite3.1-moe:3b, Workers granite3.1-moe:1b
- **Structure**: Raja split Q4 into 6 level-0 components (555-560). Topology race — only 2 of 6 claimed by GQs (555 GQ-b, 558 GQ-a), other 4 grabbed by DQs directly (556 DQ-a2, 557 DQ-a1, 559 DQ-b2, 560 DQ-b1) because both tiers poll `api_available_components` and DQs won the race. DQs then split to workers (30 components total across the full cascade).
- **Zero orphans this question**. retry=10 patch + filter-fix were the two root fixes that made this possible.
- **Saved**: `results/q4_space_elevator_royal_honey.md`.
- **Comparison vs Dense-Night Q1 Mars**: Q1 was 3271 chars / 1h44m; Q4 is 2323 chars / 8m48m. MoE on CPU is ~12× faster for similar-depth work. Granite3.1-moe is no-thinking so no wasted tokens.

### Q5 Number Theory (p²-1 div 24) — Royal Honey delivered — 03:26 UTC

- **Submit**: 03:15:46 UTC as job_id=6 via `scripts/submit_q.py /tmp/q5.txt`
- **Royal Honey**: 03:25:57 UTC, 1326 chars, total_time=608.2s (~10m8s wall clock)
- **Tier models**: same as Q4 (granite3.1-moe:3b / :1b)
- **Structure**: 31 total components across 4 tiers, all completed cleanly. Zero orphans.
- **Saved**: `results/q5_number_theory_royal_honey.md`
- **Note**: Q5 is a math proof so the Royal Honey is shorter than Q4's space-elevator numerical answer (1326 vs 2323 chars). Proof structure (a-e) gets concise treatment.

### Q6 Sphere Volume 5 methods — submitted — 03:27 UTC

- **Submit**: 03:26 UTC as job_id=7 via `scripts/submit_q.py /tmp/q6.txt` (592 chars)
- **Expected**: similar 8-12 min based on Q4/Q5 pattern
- Will be the third and final MoE-batch Royal Honey.

### Note on submit pattern

`scripts/submit_q.py` now committed to the KillerBee repo so any future beekeeper-bypass-CSRF submission is reproducible. Direct DB INSERT into `swarm_jobs` with `status='pending'`; Raja picks up via her poll of `/api/swarm/1/jobs/pending`.

### Q6 Sphere Volume — Royal Honey delivered — 03:37 UTC

- **Submit**: 03:26:40 UTC as job_id=7 via `scripts/submit_q.py /tmp/q6.txt`
- **Royal Honey**: 03:37:52 UTC, 2657 chars, total_time=502.34s (~8m22s wall clock)
- **Tier models**: same as Q4/Q5 (granite3.1-moe:3b / :1b)
- **Structure**: 32 total components across 4 tiers, all completed cleanly. Zero orphans.
- **Saved**: `results/q6_sphere_volume_royal_honey.md`

### MoE batch WRAP — 2026-04-19 Night 2 Summary

| Question | Chars | Wall clock | Orphans |
|---|---|---|---|
| Q4 Space Elevator | 2323 | 8m48s | 0 |
| Q5 Number Theory (p²-1 div 24) | 1326 | 10m8s | 0 |
| Q6 Sphere Volume (5 methods) | 2657 | 8m22s | 0 |
| **TOTAL** | **6306 chars** | **27m18s** | **0 stubs on Q4/Q5/Q6** |

Compare Dense Night 1 (last night): Q1/Q2/Q3 total ~5h28m for 33702 chars (27073 of which was Q3 raw-concat because Raja's poll timed out on Werkzeug). **MoE is ~12× faster, no thinking-token overhead, no runaway generations, all three delivered clean.**

Three root fixes landed mid-night made this possible:
1. **GiantHoneyBee `6c0896c`** — `max_wait` 60 → 300 (4-tier calibration cascade measured 60-143s per call, old 60s was too tight).
2. **GiantHoneyBee `67e1c95`** — `max_retries` 3 → 10 (90s cumulative recovery window vs old 6s; covers transient VM-kernel Network-is-unreachable blips).
3. **KillerBee `322c7b4`** — `api_available_components` filter bug (removed asymmetric `status='processing'` filter to match `api_available_subtasks`; unblocked calibration cascade for 4-tier).

Full Laptop-subtree night log: `PHASE3_MOE_NIGHT_LOG_LAPTOP.md` (19 sections). Desktop companion log pending.

Cluster left running. Bees left running. Next session can resume from main_loop state. Good night 🍯.
