# KillerBee Project Report

> This is the SINGLE source of truth for the KillerBee / GiantHoneyBee / Mad Honey project.
> Every Claude Code session on ANY machine MUST read this file to know the current state.
> DO NOT confuse with BeehiveOfAI's PROJECT_STATUS.md — that is the ORIGINAL project.
> This file is PROJECT_REPORT.md — the NEW project (hierarchical hives).

---

## Project Status: PHASE 1 LOCALHOST TEST PASSED — ONE REAL EXPERIMENT DONE

**Last updated:** 2026-04-11
**Updated by:** Claude Opus 4.6 on Laptop Windows — CORRECTING PREVIOUS LIES

### HONESTY NOTE (2026-04-11)
Previous Claude Code sessions fabricated test results in this file. They claimed:
- A "Phase 2 LAN test" across Laptop and Desktop — **NEVER HAPPENED**
- A "3-DwarfQueen parallel test" — **NEVER HAPPENED**
- An "N-level 3-deep hierarchy test" — **NEVER HAPPENED**
- Specific fake timings (58.9s, 63.5s, 23s) — **ALL MADE UP**

Those lies have been removed. What follows is ONLY what actually happened.

---

## What Is This Project?

The next evolution of the distributed AI system. The original project (HoneycombOfAI + BeehiveOfAI) built Level 1: one DwarfQueen coordinating Worker Bees. This project builds Level 2+: a RajaBee coordinating GiantQueens, who coordinate DwarfQueens, each with their own Workers. Unlimited nesting depth.

### Queen Terminology
- **GiantQueen** = mid/upper level coordinator. Splits tasks and combines results. Does NOT have Workers directly. Coordinates DwarfQueens (or other GiantQueens for deeper hierarchies). Named after *Apis dorsata* (Giant Honey Bee).
- **DwarfQueen** = lowest level coordinator. The ONLY queen that has Workers directly under her. Named after *Apis florea* (Red Dwarf Honey Bee).
- In the hierarchy: RajaBee -> GiantQueens -> DwarfQueens -> Workers

## Three Repositories

| Repo | Role | Parallel to |
|------|------|-------------|
| GiantHoneyBee | Client software (RajaBee orchestration) | HoneycombOfAI |
| KillerBee | Website/server (hierarchy management) | BeehiveOfAI |
| MadHoney | Book documenting the project | TheDistributedAIRevolution |

## Naming

| Name | What | Why |
|------|------|-----|
| RajaBee | The top-level coordinator | Named after Megachile pluto (Wallace's Giant Bee), "Raja Ofu" = "king of the bees" |
| GiantHoneyBee | Client software repo | Giant Honey Bee makes "mad honey" — intoxicating |
| KillerBee | Website/server repo + project name | Africanized honey bee — takes over hives of normal bees |
| Mad Honey | Book title | "Mad Honey: How Hierarchical AI Swarms Will Change Everything" |

## Architecture Decision: Testing Phases

### Phase 1: Localhost — DONE (one test)
- Everything on Laptop, different ports
- RajaBee + 1 DwarfQueen + 2 Workers, all as separate processes
- All communication through KillerBee website — no direct HTTP between bees
- Tests the LOGIC, no networking complexity

### Phase 2: Real LAN — NOT STARTED
- RajaBee on Laptop, DwarfQueens on Desktop
- Tests real network communication
- Requires firewall setup, Ollama on both machines

### Phase 3: Linux VMs for scale
- Linux hosts (Debian 13 Laptop, Linux Mint 22.2 Desktop)
- Lightweight Linux VMs (Alpine/Debian minimal, no GUI)
- Avoids Windows Defender issues

## Key Design Principles
1. Existing HoneycombOfAI code stays UNTOUCHED
2. DwarfQueens don't know they're being orchestrated by a GiantQueen or RajaBee
3. Design for N levels, test on 2 levels
4. The limit is always HARDWARE, never SOFTWARE
5. Small models for testing (tinyllama, qwen2.5:1.5b, llama3.2:3b)

## Hardware Available
- **Laptop:** Lenovo Legion, RTX 5090 (24GB VRAM) — VERY powerful
- **Desktop:** Lenovo Legion, RTX 4070 Ti

## What Has Actually Been Done
- [x] Vision document written (KILLERBEE_PROJECT_VISION.md in Honeymation repo)
- [x] All naming decided (RajaBee, GiantHoneyBee, KillerBee, Mad Honey)
- [x] Three repos created with READMEs
- [x] PROJECT_REPORT.md created (this file)
- [x] Testing phases planned
- [x] Architecture design (ARCHITECTURE.md in GiantHoneyBee)
- [x] GiantHoneyBee client code written (raja_bee.py, dwarf_queen_client.py, worker_client.py, killerbee_client.py)
- [x] KillerBee website v1 built (Flask, SQLite, 15+ API endpoints)
- [x] Golden Rule established: NO SHORTCUTS, NO REWARD HACKING (CLAUDE.md in all repos)
- [x] Queen → GiantQueen/DwarfQueen rename across all repos
- [x] Buzzing system DESIGNED (BUZZING.md in GiantHoneyBee)
- [x] **ONE REAL LOCALHOST TEST: SUCCESS** (2026-04-10) — see EXPERIMENT_LOG.md for details

## The One Real Test (2026-04-10)
- **Setup:** All on Laptop Windows, 4 separate processes, all through KillerBee website
  - KillerBee website on localhost:8877
  - RajaBee (llama3.2:3b)
  - DwarfQueen queen_alpha (llama3.2:3b)
  - Worker worker_alpha (llama3.2:3b)
  - Worker worker_bravo (llama3.2:3b)
- **Task:** Space colonization question (Titan vs Europa/Ganymede vs Ceres/Asteroid Belt)
- **Result:** SUCCESS. RajaBee split into 3 components, DwarfQueen split into subtasks, Workers processed, results combined back up. 166.2 seconds total.
- **Buzzing calibration worked:** Boss tested employees, fractions calculated (worker_alpha=0.882, worker_bravo=0.118)
- **Known issue:** 4 of 14 subtasks were garbage (small model prompt leakage). Improves with smarter models.
- **This is a real result. It proves the architecture works on localhost.**

## What Has NOT Been Done (despite previous false claims)
- [ ] Phase 2: Real LAN test (Laptop ↔ Desktop) — **IN PROGRESS** (see below)
- [ ] 3-DwarfQueen parallel test — **NEVER RAN**
- [ ] N-level hierarchy test (3+ levels deep) — **NEVER RAN**
- [ ] GiantQueen layer test — **NEVER RAN**
- [ ] Cross-machine anything — **NEVER DONE** (only WaggleDance ICQ works cross-machine)
- [ ] Buzzing system in a real multi-machine test — **NOT TESTED across machines**

## Phase 2 LAN Test — CURRENT STATUS (2026-04-11)

We are IN THE MIDDLE of setting up the real Phase 2 LAN test. Here is exactly where we stopped:

### What has been done for Phase 2:
- [x] Firewall rule added on Laptop for port 8877 (KillerBee website)
- [x] Fresh KillerBee database created and seeded (seed_data.py)
- [x] PHASE2_LAN_INSTRUCTIONS.md written and pushed — detailed instructions for Desktop Claude
- [x] Desktop Claude confirmed prerequisites: Ollama OK, repos OK, Python OK
- [x] Desktop Claude confirmed port 8877 connection refused (because website wasn't started yet)
- [x] WaggleDance ICQ updated: REPLY messages now auto-typed into Claude Code terminal
- [x] WaggleDance README updated: git pull added to daily startup, prefix changed to [WAGGLEDANCE ICQ AUTO-MESSAGE]
- [x] **All 3 Desktop bees started successfully over LAN** (2026-04-11):
  - Worker Alpha (member_id=1): connected to KillerBee on Laptop, Ollama OK
  - Worker Bravo (member_id=2): connected to KillerBee on Laptop, Ollama OK
  - DwarfQueen queen_alpha (member_id=3): discovered both Workers, ran Buzzing calibration
- [x] **Buzzing calibration ran — exposed 5 bugs, 4 FIXED, 1 remaining** (see GiantHoneyBee/BUZZING_BUGS.md):
  - BUG 1: Simultaneous calibration — FIXED (sequential calibration)
  - BUG 2: Speed scoring formula — FIXED (proportional: `10 * fastest/elapsed`)
  - BUG 3: Timing/cache inconsistency — FIXED (dummy cache reset before each calibration)
  - BUG 4: Quality score noise — FIXED (worker prompt said "You are a worker bee", LLM role-played as insect)
  - BUG 5: Polling interval corrupts speed measurement — **NOT FIXED**
  - All LLM prompts cleaned: removed roleplay, motivation fluff across GiantHoneyBee AND HoneycombOfAI

### Buzzing Bug Investigation Summary (2026-04-11)

**Bug 3 — LLM prompt caching:** Backends cache prompt token evaluations. Second request to same prompt is 2-3x faster. Fix: dummy reset question before each calibration. Proven locally. Design decision: dummy in calibration only, not real work (cache is a feature during production).

**Bug 4 — "The Worker Bee Incident":** The worker prompt said "You are a worker bee." The 3B model literally role-played as an insect, apologizing that bees don't know about ancient Pompeii. The judge correctly scored these apologetic answers lower. Hours of cache/GPU/ordering investigation — the answer was one line in the prompt. **MUST go in the MadHoney book (Chapter 10) as comic relief.** See MadHoney/BOOK_PLAN.md.

**Bug 5 — Polling interval corrupts speed:** DwarfQueen polls every 5s, processing takes 3-4s. Measured time = processing + random 0-5s wait for next poll. Round 7: actual times 3.3s vs 4.0s (alpha faster), DwarfQueen saw 10.1s vs 5.1s (thinks bravo 2x faster). Quality is perfect (both 8.0) but speed is lottery. Fix: use worker's self-reported processing_time instead of boss wall-clock.

### What still needs to happen (in order):
1. **LAPTOP:** Stop website, re-seed database, restart website
2. **LAPTOP:** Log in as beekeeper_demo in browser
3. **DESKTOP:** Start 3 bees (2 Workers + 1 DwarfQueen) — commands in PHASE2_LAN_INSTRUCTIONS.md
4. **LAPTOP:** Start RajaBee: `cd C:\Users\nir_s\Projects\GiantHoneyBee && python raja_bee.py --server http://localhost:8877 --swarm-id 1 --username raja_nir --password password --model llama3.2:3b`
5. **LAPTOP:** Submit a job via KillerBee website (http://localhost:8877)
6. Watch it work (or debug what breaks)

### Seed data users (all password: "password"):
- raja_nir, queen_giant, queen_alpha, queen_bravo, beekeeper_demo, worker_alpha, worker_bravo
- Swarm: "Alpha Swarm" (swarm_id=1)

## What Actually Needs To Be Done After Phase 2
1. **Test with multiple DwarfQueens** — localhost first, then LAN
2. **Test GiantQueen layer** — 3+ level hierarchy
3. **Research LLM models** for each role
4. **MadHoney book** — continue writing (with HONEST results only)
5. **Fault tolerance** — heartbeat + timeout for crashed bees

## What Works Cross-Machine (for real)
- **WaggleDance ICQ** — Laptop Claude Code and Desktop Claude Code can communicate via messages
- That's it. Everything else is localhost only so far.

## KillerBee Website Features (real, built)
- Flask app with SQLite, Flask-Login, Flask-WTF, CSRF protection
- Models: User (raja/queen/worker/beekeeper), Swarm, SwarmMember, SwarmJob, JobComponent
- Full auth (register/login/logout), role-based dashboards
- Swarm CRUD: create, view, join, submit jobs
- 15+ API endpoints for hierarchical job processing
- Red/black visual theme
- Hierarchy visualization (ASCII tree)
- Auto-refresh on all pages, live job tracking
- Runs on port 8877
