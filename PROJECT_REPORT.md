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
- [ ] Phase 2: Real LAN test (Laptop ↔ Desktop) — **NOT STARTED**
- [ ] 3-DwarfQueen parallel test — **NEVER RAN**
- [ ] N-level hierarchy test (3+ levels deep) — **NEVER RAN**
- [ ] GiantQueen layer test — **NEVER RAN**
- [ ] Cross-machine anything — **NEVER DONE** (only WaggleDance ICQ works cross-machine)
- [ ] Buzzing system in a real multi-machine test — **NOT TESTED across machines**

## What Actually Needs To Be Done Next
1. **Phase 2: Real LAN test** — RajaBee on Laptop, DwarfQueens on Desktop (10.0.0.5)
2. **Test with multiple DwarfQueens** — localhost first, then LAN
3. **Test GiantQueen layer** — 3+ level hierarchy
4. **Research LLM models** for each role
5. **MadHoney book** — continue writing (with HONEST results only)
6. **Fault tolerance** — heartbeat + timeout for crashed bees

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
