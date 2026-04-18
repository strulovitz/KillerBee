# Phase 3 Night Experiment Plan

**Date written:** 2026-04-18, night, while Nir prepares to sleep.
**Scope:** text-only. No audio, no vision, no multimodal extension work tonight.
**Participants:** Laptop Claude Code (this host, 10.0.0.8) and Desktop Claude Code (10.0.0.5). Two Claudes, fifteen VMs, two WaggleDance ICQ agents, one KillerBee website.
**Autonomy level:** Nir is going to sleep and wants both Claudes to execute this plan without needing him. No fake results, no shortcuts. If we get stuck we log it and wait.

This file is the canonical contract for the night. Any change after Nir is asleep is an edit in place, a new commit, and an ICQ ping to the other Claude.

---

## 1. Current known-good state (verified 2026-04-18 ~02:35)

- **15 VMs running.** All reachable by SSH with `~/.ssh/phase3_ed25519`. All Ollama endpoints answer on port 11434.
  - Laptop side (8 VMs):
    - rajabee 10.0.0.14
    - giantqueen-a 10.0.0.17
    - dwarfqueen-a1 10.0.0.19
    - dwarfqueen-a2 10.0.0.25
    - worker-a1 10.0.0.27
    - worker-a2 10.0.0.29
    - worker-a3 10.0.0.31
    - worker-a4 10.0.0.33
  - Desktop side (7 VMs, per Desktop's ICQ 2026-04-18 02:32):
    - giantqueen-b 10.0.0.6
    - dwarfqueen-b1 10.0.0.7
    - dwarfqueen-b2 10.0.0.9
    - worker-b1 10.0.0.10
    - worker-b2 10.0.0.11
    - worker-b3 10.0.0.12
    - worker-b4 10.0.0.16
- **45 Ollama models pulled across the 15 VMs.** Dense, MoE, Vision at every tier. Tonight uses only Dense and MoE.
- **KillerBee website up** on Laptop host at `http://10.0.0.8:8877`. Fresh SQLite DB seeded with 16 users (raja_nir, queen_giant_a, queen_giant_b, queen_dwarf_a1..b2, worker_a1..b4, beekeeper_demo). Swarm "Phase 3 Hive" created with `depth=4`. No members registered yet.
- **WaggleDance ICQ** up on both sides at http://localhost:8765. Agents watching each other's windows.
- **Nir's git repo** at github.com/strulovitz is the durable fallback channel.

## 2. Hierarchy map (the tree we are testing)

```
                    rajabee (10.0.0.14, Laptop)
                    /                       \
     giantqueen-a (10.0.0.17)        giantqueen-b (10.0.0.6, Desktop)
         /          \                    /            \
 dq-a1 (.19)    dq-a2 (.25)       dq-b1 (.7)      dq-b2 (.9)
   /    \        /    \            /    \          /    \
 wa1   wa2    wa3   wa4         wb1   wb2       wb3   wb4
(.27) (.29)  (.31) (.33)       (.10) (.11)     (.12) (.16)
```

This is the FIRST four-level hierarchy test ever. Phase 2 Experiment 3 was three levels (Raja, one DwarfQueen, two Workers). GiantQueens have never been in a real run before. Expect the first attempt to need adjustment.

## 3. Tier-to-model mapping

Every VM already has Dense, MoE, and Vision pulled into its local Ollama. The experiment flips which model the bee client asks Ollama to use. No re-downloading, no model management.

| Tier          | Dense               | MoE                   | Vision (unused tonight) |
|---------------|---------------------|-----------------------|-------------------------|
| Raja          | qwen3:14b           | granite3.1-moe:3b     | qwen3.5:9b              |
| GiantQueen-A  | qwen3:8b            | granite3.1-moe:3b     | qwen3-vl:8b             |
| GiantQueen-B  | qwen3:8b            | granite3.1-moe:3b     | qwen2.5vl:7b            |
| DwarfQueens   | phi4-mini:3.8b      | granite3.1-moe:3b     | gemma3:4b               |
| Workers       | qwen3:1.7b          | granite3.1-moe:1b     | qwen3.5:0.8b            |

## 4. Bee-client model selection mechanism

The bee clients in the GiantHoneyBee repo (raja_bee.py, giant_queen_client.py, dwarf_queen_client.py, worker_client.py) need to accept the Ollama model name as an environment variable or CLI flag. Whichever mechanism Desktop thinks is cleanest. Hard-coded model constants must come out.

Proposed minimum change per client: read `KILLERBEE_MODEL` from the environment at startup, fall back to a sensible tier default only if unset. No runtime branching on model type. The bee client stays dumb.

After the change, starting a bee on a VM looks like:
```
ssh nir@<vm-ip> \
    'cd ~/GiantHoneyBee && \
     KILLERBEE_MODEL=<model-name> \
     KILLERBEE_URL=http://10.0.0.8:8877 \
     OLLAMA_URL=http://localhost:11434 \
     nohup python3 <client>.py > ~/bee.log 2>&1 &'
```

Between batches, we stop every bee process and restart it with the new `KILLERBEE_MODEL` value. No config files on disk that persist across batches.

## 5. Tonight's six questions

Three for the Dense batch (multi-domain planning) and three for the MoE batch (math / physics). All text-only. All in English.

### Batch A (Dense) — Q1. Mars Colony

```
Design a 6-person, 2-year Mars base. Cover in equal depth:
(a) rocket propulsion tradeoffs for crew and cargo transport,
(b) crew psychological selection and conflict management in isolation,
(c) international treaty issues around off-world resource extraction,
(d) bidirectional microbial contamination risk (Earth to Mars and Mars to Earth),
(e) closed-loop food supply mathematics for 6 people for 730 days.
Conclude with a go or no-go recommendation for a 2032 launch.
```

### Batch A (Dense) — Q2. Antarctic Research Station

```
Design a 40-person year-round Antarctic research station at the South Pole.
Cover in equal depth:
(a) structural engineering against minus 80 Celsius and katabatic winds,
(b) medical infrastructure for 6-month darkness with no evacuation,
(c) psychological screening and crew cohesion over a 12-month winter-over,
(d) logistics chain for annual resupply via icebreaker plus LC-130,
(e) environmental and treaty compliance under the Antarctic Treaty System.
Conclude with an estimate of annual operating cost in 2026 US dollars.
```

### Batch A (Dense) — Q3. Provence Honey Bee Conservation Farm

```
Design a 500-hive honey bee conservation farm in Provence, France,
focused on rescuing threatened Apis mellifera mellifera (the native
French black bee) from Colony Collapse Disorder. Cover in equal depth:
(a) apiculture: hive management, queen breeding, swarm prevention,
    overwintering in the Mediterranean climate,
(b) botany: pollinator corridor across 20 hectares with lavender,
    sunflower, phacelia, and wildflower meadows, synchronized for
    nectar flow March through October,
(c) disease management: Varroa destructor, American foulbrood,
    Nosema ceranae, pesticide exposure from neighbouring sunflower farms,
(d) economics: revenue from honey plus pollination services plus rescue
    bee sales plus agritourism; target break-even in year 3; CAP
    (Common Agricultural Policy) subsidies,
(e) education and regulation: school visits, beekeeper training,
    certification under French Abeilles de France and EU apiculture directives.
Conclude with a 10-year capital and operating plan.
```

### Batch B (MoE) — Q4. Space Elevator Physics

```
A space elevator cable reaches from the Earth's surface (6378 km)
to geosynchronous orbit (35786 km). Compute and justify:
(a) total cable length,
(b) total mass assuming carbon nanotubes with density 1.3 g per cm cubed
    and cable radius 1 cm,
(c) mass of the counterweight beyond GEO needed to keep the cable under tension,
(d) tensile strength required at the cable's strongest point, and how this
    compares to the measured strength of carbon nanotubes today,
(e) taper ratio from Earth end to GEO end.
Conclude: is a space elevator physically feasible with 2026 materials?
```

### Batch B (MoE) — Q5. Number Theory Proof

```
Prove that for every prime p greater than 3, the number p squared minus 1
is divisible by 24. Structure the proof as:
(a) show p squared is congruent to 1 modulo 8,
(b) show p squared is congruent to 1 modulo 3,
(c) argue 8 and 3 are coprime so by the Chinese Remainder Theorem the
    result is congruent to 1 modulo 24,
(d) verify numerically for p equals 5, 7, 11, 13, 17, 19, 23,
(e) compose (a) through (c) into the final proof with no gaps.
```

### Batch B (MoE) — Q6. Sphere Volume, Five Methods

```
Compute the volume of a sphere of radius 10 cm in five independent ways,
then cross-check they all agree to within one percent:
(1) the classical formula V equals four thirds pi r cubed,
(2) a triple integral in spherical coordinates with full derivation,
(3) Archimedes' sphere-and-cylinder ratio,
(4) Pappus's theorem applied to rotation of a semicircle,
(5) a Monte Carlo estimate of volume by sampling a cube, including
    reasoning about expected variance.
Report each method's answer in cubic cm, then the agreement matrix,
then flag any method that disagrees by more than one percent.
```

## 6. Execution order

The order is batches first, then within each batch the questions are fired sequentially so logs are clean.

1. **Preparation step.** Desktop edits GiantHoneyBee bee clients to accept `KILLERBEE_MODEL` env var. Desktop commits and pushes. Laptop pulls.
2. **Dense batch bring-up.** Both Claudes SSH into their VMs and start bee processes with the tier's Dense model. Each bee self-registers into the Phase 3 Hive swarm via the KillerBee website. Wait until all 15 are registered before running the first question.
3. **Buzzing calibration (Dense).** Calibration runs bottom up: DwarfQueens calibrate Workers, GiantQueens calibrate DwarfQueens, Raja calibrates GiantQueens. This is the first four-level calibration ever.
4. **Q1 Mars Colony** submitted as beekeeper_demo through the website. Wait for Royal Honey. Log timing and answer.
5. **Q2 Antarctic** same pattern.
6. **Q3 Provence Bee Farm** same pattern.
7. **Stop all 15 bees.**
8. **MoE batch bring-up.** Same as step 2 but with MoE model names per tier.
9. **Buzzing calibration (MoE).**
10. **Q4 Space Elevator** submitted.
11. **Q5 Number Theory Proof.**
12. **Q6 Sphere Volume Five Methods.**
13. **Stop all 15 bees.**

## 7. Stretch plan (only if both batches finish cleanly and it is still dark)

Nir's overflow idea: run each question on the model it was NOT designed for. That gives us the full cross comparison: Dense vs MoE on the SAME question, same hive, same calibration methodology. The scientific value is high and the work is just re-runs, no new code.

- **Cross run Dense on MoE questions.** Spin up Dense bees again and run Q4 Space Elevator, Q5 Number Theory, Q6 Sphere Volume.
- **Cross run MoE on Dense questions.** Spin up MoE bees again and run Q1 Mars, Q2 Antarctic, Q3 Bee Farm.

If a cross run starts but does not finish before morning, log what ran, stop cleanly, and leave the rest for Nir.

Cross runs are optional. The primary goal is the six questions in Section 5. Do not skip any of those for the stretch.

## 8. Logging rules

Every run produces an appendix in `EXPERIMENT_LOG.md` in the KillerBee repo. Append, never overwrite. Every appendix contains:

- Question ID (Q1..Q6 plus a cross tag if applicable).
- Exact model per tier, so the run is reproducible.
- Timestamp started, timestamp finished, elapsed seconds.
- Top-level split from Raja (how many components).
- Per-component split from each DwarfQueen (how many subtasks).
- Royal Honey text in full. No editing. No summarizing. If it is junk, it is junk, log the junk.
- Any bee that crashed, hung, or returned gibberish. Which VM, which model, which phase.

Commit and push after each question completes. Do not batch commits — if the machine loses power mid run, at least the previous answers survive.

## 9. Failure handling

Expect the first four-level hierarchy run to break. Possible failure modes:
- GiantQueen client does not know how to split work to DwarfQueens because Phase 2 Experiment 3 only had a DwarfQueen directly under Raja. The GiantQueen role is new code territory.
- Buzzing calibration may assume a single level below, not two levels.
- qwen3 and phi4-mini have different output formats than llama3.2:3b. smart_splitter may trip.
- A single Worker or DwarfQueen hangs. Cluster has redundancy: 2 DwarfQueens per GiantQueen, 2 Workers per DwarfQueen. Losing one of each tier is survivable, losing a whole branch kills a component but not the whole run.

If a question hangs for more than 15 minutes with no component progress in the website logs, kill the job and move to the next question. Log the hang honestly as a failed run with the exact hang point.

If the 4-level hierarchy is fundamentally broken (first question never completes), stop. Do not try to patch live. Log the failure, ICQ each other, wait for Nir. Better to wake up to "we hit a wall at the GiantQueen split step" than to "we faked a Royal Honey." No reward hacking. Ever.

## 10. Communication discipline

- **Primary channel: WaggleDance ICQ.** Short messages only. Use ASCII, no emojis, no smart quotes.
- **Secondary channel: git.** Any decision worth more than a one-line ICQ goes into the KillerBee repo as a commit and push. `git pull` every 5 minutes on the idle side if ICQ feels stale.
- **Heartbeat.** Every 15 minutes each Claude appends a one-line status to `EXPERIMENT_LOG.md` under a "Night heartbeat" section so the other side knows the first is still alive. Commit and push the heartbeat.
- **No long speeches over ICQ.** If it is long, commit to the repo and ICQ the commit hash.

## 11. What NOT to do tonight

- Do NOT invent new orchestrator code to do multimodal. Audio and vision are off the table tonight.
- Do NOT bypass the KillerBee website. Every bee to bee message goes through it. Rule 1 in `KillerBee/CLAUDE.md`.
- Do NOT fake, summarize, or prettify Royal Honeys. Log them exactly as returned.
- Do NOT change tier model assignments mid run. A batch is Dense or MoE from start to finish.
- Do NOT keep retrying a broken run silently. Log the failure and move on.
- Do NOT push changes to the bee client code after the Dense batch has started. If the clients need a bug fix, stop the batch cleanly, fix, restart, and note the restart in the log.

## 12. Green light contract

Before any bee process starts, both Claudes must:

1. Pull the latest KillerBee repo and confirm they see this file at its current commit hash.
2. Reply via ICQ with the literal string `GREEN` plus the short commit hash they saw.
3. Agree on who writes which clients' model-selection patch (most likely Desktop, since the code lives in GiantHoneyBee which was built there).
4. Confirm the KillerBee website is still up and reachable from both sides.

If either side is not green, nobody starts. Nir wakes up to a file that says who was not green and why.

## 13. Wake-up report

When Nir is up, one of us writes the summary to `EXPERIMENT_LOG.md` in a section titled `Night of 2026-04-18 summary`. The summary states:
- Which batches ran.
- Which questions completed, which hung, which were faked (should be zero).
- Total wall clock.
- Short qualitative note on Dense vs MoE: did MoE cover more domains, did Dense reason deeper on the math, did either just fail.
- Honest list of what broke and what was not attempted.

No marketing. No "we did it." Numbers and facts.

---

*Canonical plan for the night of 2026-04-18. Edit in place. Git is the time machine.*
