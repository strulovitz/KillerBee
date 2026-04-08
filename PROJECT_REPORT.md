# KillerBee Project Report

> This is the SINGLE source of truth for the KillerBee / GiantHoneyBee / Mad Honey project.
> Every Claude Code session on ANY machine MUST read this file to know the current state.
> DO NOT confuse with BeehiveOfAI's PROJECT_STATUS.md — that is the ORIGINAL project.
> This file is PROJECT_REPORT.md — the NEW project (hierarchical hives).

---

## Project Status: PLANNING PHASE

**Last updated:** 2026-04-08
**Updated by:** Claude Opus 4.6 on Laptop Windows

---

## What Is This Project?

The next evolution of the distributed AI system. The original project (HoneycombOfAI + BeehiveOfAI) built Level 1: one Queen Bee coordinating Worker Bees. This project builds Level 2+: a RajaBee coordinating multiple Queen Bees, each with their own Workers. Unlimited nesting depth.

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

### Phase 1: Localhost (NEXT)
- Everything on Laptop, different ports
- Port 5000: Queen 1 + workers (small model)
- Port 5001: Queen 2 + workers (small model)
- Port 5002: RajaBee (slightly bigger model)
- Tests the LOGIC, no networking complexity

### Phase 2: Real LAN
- RajaBee on Laptop, Queens on Desktop
- Tests real network communication

### Phase 3: Linux VMs for scale
- Linux hosts (Debian 13 Laptop, Linux Mint 22.2 Desktop)
- Lightweight Linux VMs (Alpine/Debian minimal, no GUI)
- Avoids Windows Defender issues

## Key Design Principles
1. Existing HoneycombOfAI code stays UNTOUCHED
2. Queens don't know they're being orchestrated by a RajaBee
3. Design for N levels, test on 2 levels
4. The limit is always HARDWARE, never SOFTWARE
5. Small models for testing (tinyllama, qwen2.5:1.5b, llama3.2:3b)

## Hardware Available
- **Laptop:** Lenovo Legion, RTX 5090 (24GB VRAM) — VERY powerful
- **Desktop:** Lenovo Legion, RTX 4070 Ti

## What Has Been Done
- [x] Vision document written (KILLERBEE_PROJECT_VISION.md in Honeymation repo)
- [x] All naming decided (RajaBee, GiantHoneyBee, KillerBee, Mad Honey)
- [x] Three repos created with READMEs
- [x] PROJECT_REPORT.md created (this file)
- [x] Testing phases planned
- [ ] Architecture design (detailed)
- [ ] GiantHoneyBee code
- [ ] KillerBee website
- [ ] Mad Honey book — Chapter 1

## What Needs To Be Done Next
1. Detailed architecture plan for GiantHoneyBee
2. Design the RajaBee → Queen communication protocol
3. Start coding Phase 1 (localhost test)
