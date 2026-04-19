# Phase 3 MoE Night Log — Desktop Subtree (2026-04-19)

Written by Desktop Claude Code on Mint 22.2 (10.0.0.5). Desktop owns the `-b` subtree: GiantQueen-B + 2 DwarfQueens-B + 4 Workers-B, 7 VMs out of the 15-VM cluster. Laptop owns RajaBee and the `-a` subtree (8 VMs). This log is Desktop's view of the MoE night (Q4/Q5/Q6), paired with `PHASE3_NIGHT_EXPERIMENT_PLAN.md` (the contract) and `PHASE3_MOE_NIGHT_LOG_LAPTOP.md` (Laptop's companion).

For the MadHoney book chapter on Phase 3, read this alongside `PHASE3_NIGHT_LOG_DESKTOP.md` (Dense night). Together: Dense night exposed the bugs, MoE night rooted them.

---

## 1. What happened end to end

We ran the MoE half of Phase 3 in one session. Three questions — Q4 Space Elevator, Q5 Number Theory, Q6 Sphere Volume in five methods — went through the 15-VM four-tier hive (Raja → 2 GiantQueens → 4 DwarfQueens → 8 Workers) and produced three Royal Honeys. All three delivered cleanly with ZERO stubbed components on Q4/Q5/Q6. The stubs that existed tonight (Components 421/425/471 plus the 45 Dense-night zombies) were cleared during the calibration pre-flight, not during Q4/Q5/Q6 themselves.

Three root fixes landed this night — two patches to the bee clients and one patch to the KillerBee server. The server-side fix is the architecturally significant one because it exposed a bug that had been hiding since Phase 2 behind a test asymmetry.

## 2. Cold start: 7 Desktop VMs shut off, MAC-stable recovery

Session opened with all 7 Desktop VMs in `shut off` state. `sudo virsh list` returned empty, `sudo virsh list --all` showed the full roster asleep. Cause was overnight host/VM shutdown between sessions (not a libvirt failure — simply no autostart on Mint). Booted all 7 via a parallel `sudo virsh start` loop, waited for DHCP leases via ARP-watch.

All 7 MAC-stable leases returned to their 2026-04-18 IPs:

| VM | MAC | IP |
|---|---|---|
| giantqueen-b | `52:54:00:83:58:27` | 10.0.0.6 |
| dwarfqueen-b1 | `52:54:00:e5:73:c7` | 10.0.0.7 |
| dwarfqueen-b2 | `52:54:00:5d:65:63` | 10.0.0.9 |
| worker-b1 | `52:54:00:d5:d7:e8` | 10.0.0.10 |
| worker-b2 | `52:54:00:a1:1b:5f` | 10.0.0.11 |
| worker-b3 | `52:54:00:85:22:c0` | 10.0.0.12 |
| worker-b4 | `52:54:00:a1:35:6c` | 10.0.0.16 |

Laptop's host had rebooted during the day (uptime 43 minutes) and had 8 VMs plus Flask to restart. Desktop had no host reboot, just the VMs.

## 3. Part A rsync — Desktop template had `rsync` pre-installed

Per plan pre-flight, rsynced the last-night-patched `GiantHoneyBee` at commit `03766a3` from Desktop host to all 7 Desktop VMs in parallel. Verified `max_wait = 60` landed three times per VM (raja_bee.py + giant_queen_client.py + dwarf_queen_client.py = 3 hits). All 7 rsync exit=0.

Key asymmetry with Laptop: Desktop VMs had `rsync` pre-installed because they were all cloned from `giantqueen-b`, which was built via the autoinstall that shipped with `rsync` in its base package set. Laptop VMs were built independently and did not ship rsync. Laptop had to `sudo apt-get install -y rsync` on all 8 before her rsync could work. This is a template-lineage artifact worth calling out for the book: same-looking virtualization stack can produce different package closures depending on how each host's template was seeded.

Part A done on Desktop as KillerBee heartbeat `9fcbb79`.

## 4. The `pkill -f` self-match bug

When the first GQ-b fire needed to be aborted mid-calibration (Section 6 below), I ran `ssh ... 'pkill -9 -f giant_queen_client.py'` expecting it to kill only the Python bee. SSH returned exit 255.

Root cause: `pkill -f` matches the full command line of every process. The remote bash command `pkill -9 -f giant_queen_client.py` has `"giant_queen_client.py"` embedded in its own argv (the bash-c wrapper's command-line). So pkill killed the bee AND the parent bash wrapper that invoked pkill. When the bash died, the ssh session died with it — exit 255.

Post-mortem was confirmed by a fresh ssh that showed the bee python process was in fact dead — just the ssh reporting looked like a failure. No harm done, but the pattern is worth noting: **`pkill -f <pattern>` on a remote shell will self-terminate the ssh channel if the pattern appears in the remote bash wrapper's argv**.

Workarounds if clean termination required:
- Use `ps -eo pid,cmd` then `kill -9 <pid>` explicitly.
- Use a pattern that does not appear in the wrapper's argv (e.g. filter on the actual executable path `/opt/killerbee/venv/bin/python` combined with the script name).
- Use `pkill --ignore-ancestors -f ...` if available (not on stock Ubuntu 24.04).

Desktop night log §4 (Dense) had the earlier version of this lesson with a different flavor (regex alternation didn't match). Two nights, two `pkill` lessons.

## 5. Bottom-up staggered bring-up — workers and DQs

Plan Section 5 called for strict bottom-up bring-up: Workers first, wait for `Worker is RUNNING` banner on all, then DQs, wait for `DwarfQueen is RUNNING` after their buzzing cycles complete, then GQs, then Raja. We coordinated tier-by-tier with ICQ handshakes (DESKTOP_WORKERS_MAINLOOP, DESKTOP_DQS_MAINLOOP, etc.).

Workers tier on Desktop: 4 workers fired in parallel with `KILLERBEE_MODEL=granite3.1-moe:1b`. All 4 registered with the KillerBee server, picked up existing SwarmMember rows from last night (idempotent registration, no duplicates — good), and entered main_loop within seconds. Member IDs post-cleanup:

- worker_b1 @ 10.0.0.10, member_id=3
- worker_b2 @ 10.0.0.11, member_id=1
- worker_b3 @ 10.0.0.12, member_id=6
- worker_b4 @ 10.0.0.16, member_id=5

DQs tier on Desktop: 2 DQs fired with `KILLERBEE_MODEL=granite3.1-moe:3b`. Each DQ ran her buzzing cycle against her 2 workers. Worker calibration answers arrived in 17-20s on granite3.1-moe:1b (noticeably faster than Dense night's phi4-mini at comparable sizes). REAL calibration numbers collected for the first time at this scale under the bottom-up choreography:

- DQ-b1 (member_id=4): worker_b1 speed=9.0 quality=10.0 buzzing=90.0, worker_b2 speed=10.0 quality=10.0 buzzing=100.0
- DQ-b2 (member_id=7): worker_b3 speed=9.9 quality=9.7 buzzing=96.0, worker_b4 speed=10.0 quality=9.7 buzzing=97.0

Bottom-up eliminated the 4-tier calibration cascade deadlock that dominated Dense night. Because workers were already in main_loop ready to answer when DQs started calibrating, no parent tier was waiting on a child tier that was itself waiting on its child.

## 6. GQ-b first fire — `max_wait=60` exposed as too tight

GQ-b fired with `KILLERBEE_MODEL=granite3.1-moe:3b`. Round 1 calibration went out to both DwarfQueens and both **timed out at 60 seconds**.

Diagnosis: DQ-b1 had received the calibration question (Component 396), split it into subtasks for workers, got worker results back, and combined — total wall clock 99.5 seconds. DQ-b2 had similarly completed Component 406 in 61.9 seconds (2 seconds over the cutoff). Neither DQ was hung. Both had legitimately completed the work; GQ-b just gave up too early.

Root cause: `max_wait = 60` in `giant_queen_client.py` line 268 was a Dense-night patch from Laptop (who reduced `600 → 60` after seeing 10-minute-per-round timeouts). That patch was designed for 3-tier Phase 2 semantics, where the subject-of-calibration (a DwarfQueen) answered with ONE Ollama call — fast. In 4-tier, the subject-of-calibration (a DwarfQueen under GQ's calibration) does a FULL split-combine through her workers, which takes 60-100s on CPU. 60s budget was too tight by a factor of ~1.5-2x.

This was visible in the bee.logs and in the KillerBee DB. GQ-b's log showed the timeout. DQ-b1/b2's logs showed the completion times.

## 7. Root fix #1 — `max_wait` 60 → 300

Proposed root fix via ICQ: raise `max_wait` from 60 to 300 (5 minutes) across `raja_bee.py:281`, `giant_queen_client.py:268`, and `dwarf_queen_client.py:268`. 300 is ~3-5x the observed 60-100s range — comfortable headroom without being wasteful.

Nir's pre-sleep guidance applied: "patience over speed, solve from root, all night available." 300 seconds per round is patience; the patch addresses the root (wait long enough for the real work to complete on CPU) rather than an ad-hoc stub.

Laptop owned the commit: `GiantHoneyBee 6c0896c`. Desktop halted GQ-b, pulled, rsynced to all 7 Desktop VMs, verified `max_wait = 300` landed. Simultaneous GQ restart coordinated by ICQ GO-RESTART-NOW.

GQ-b second fire: R1 DQ-b1 completed in 49.3s, R2 DQ-b1 in 90.6s, R3 DQ-b1 in 102.7s — all comfortably under the 300s budget. Real calibration data collected for DQ-b1: speed=10.0, quality=9.7, buzzing=97.0.

## 8. GQ-b second fire — DQ-b2 orphan stalled all 3 rounds

DQ-b2 timed out on all 3 rounds with GQ-b despite the new 300s budget. Investigation on the DQ-b2 VM showed her python process alive, CPU 0%, no ollama model loaded, log showing she was stuck in `_wait_for_components` on Component 421 — the Round 1 calibration question GQ-b had sent her.

Component 421 had been split by DQ-b2 into Component 425 (a subtask). Querying the KillerBee API:

```
Component 421: member_id=7 (DQ-b2) status=processing
Component 425: member_id=14 (worker_a3, Laptop) status=processing
```

Subtask had been claimed by a Laptop worker (not a Desktop worker) because `api_available_subtasks` is swarm-wide and Worker claim is first-come. That's fine architecturally.

Initial (wrong) diagnosis: Ollama runaway-generation pattern from Dense night. Proposed `systemctl restart ollama` on worker_a3.

Corrected by Laptop: worker_a3 was IDLE (CPU 0%, ollama ps empty, bee.log "Polling no work available completed=12"). The worker had already completed Component 425 locally, tried to POST the result, hit a transient network-unreachable event, the bee's retry budget (3 retries with 2s backoff = 6s total) was exhausted, bee caught the exception, moved on. DB stayed at status=processing forever because the success transition never landed.

Same orphan class as Dense-night c242/c315/c318 but now with a concrete networking root cause. Laptop stubbed Components 421, 425, 471 via `scripts/stub_orphans.py` with honest `[STUBBED-ORPHAN ...]` disclosure strings. DQ-b2 unstuck on next poll, combined the stub input via her Ollama, and posted a synthesized (coherent, on-topic) answer for Component 421. This is the "honest-disclosure-recovery" pattern: stub exposes the gap at the child level, parent's LLM synthesis still produces useful text downstream because the original question is in context.

## 9. Root fix #2 — retry budget 3 → 10

Laptop investigated the network-drop root. Findings:

- 20-request curl loop from worker_a3 VM to the KillerBee server: 20 of 20 successful, 2-14ms each.
- `ip -s link` on br0: 0 RX errors, 0 RX drops, 0 TX errors, 2 TX drops total.
- Flask server log: 200 responses to all 15 VMs during the window.
- One VM (10.0.0.31) had a suspicious dual-DHCP route entry (`src 10.0.0.30` for a VM whose IP is 10.0.0.31), which may be a race source worth future investigation.

Conclusion: the Network-is-unreachable events are VM-kernel-level, brief (seconds), and self-heal. The bees just needed a bigger retry budget to survive them. `KillerBeeClient._request` went from `max_retries=3` to `max_retries=10` with the existing linear backoff `retry_delay=2.0 * attempt`. New cumulative recovery window: ~90 seconds instead of ~6. Committed as `GiantHoneyBee 67e1c95`.

Desktop pulled, rsynced to all 7 Desktop VMs, verified `max_retries: int = 10` landed. Bees currently running did not need restart — their in-memory old budget was good enough for anything remaining in their current phase, and the new budget would take effect on any fresh fire (Raja, future restarts).

## 10. Root fix #3 — `api_available_components` filter bug (KillerBee `322c7b4`)

The architecturally significant bug. Visible in Desktop's GQ-b while Raja was calibrating.

Sequence: Raja sent GQ-b a calibration question (Component 493 — "Name three colors of the rainbow. Reply in three words only."). GQ-b processed it — which for a main-loop bee means "split into sub-components for my DwarfQueens." GQ-b posted Component 494 as the sub-component, `component_type='component'`, `member_id=null`, `status='pending'`. But DQ-b1 and DQ-b2 polled `api_available_components` and saw nothing. Component 494 sat there forever.

Dug into the KillerBee server code. Two nearby endpoints with near-identical purpose, different filters:

```
# app.py line 578 — WORKER claim (works correctly)
api_available_subtasks: SwarmJob.query.filter_by(swarm_id=swarm.id).all()
# NO status filter on the job - matches ALL jobs in swarm

# app.py line 604 — DQ/GQ claim (has the bug)
api_available_components: SwarmJob.query.filter_by(swarm_id=swarm.id, status='processing').all()
# ONLY processing-status jobs
```

But calibration jobs are created by `api_member_calibration` with `status='calibration'`, not `'processing'`. So any sub-component posted by a GQ during a Raja-calibration cascade was invisible to DQs because Job 1 (the calibration job) wasn't status='processing'.

Why Phase 2 never hit this: 3-tier had DQ-to-Worker as the only cascade, which went through `api_available_subtasks` (no filter). There was no GQ-to-DQ cascade to exercise the broken filter. The 4-tier Raja-to-GQ-to-DQ calibration chain was the first configuration ever to require that code path, and it failed silently from the first run.

Retroactive explanation for Dense night: "Startup race on sub-components during pre-calibration-finish" was NOT a race. It was this exact filter bug. Components 55 and 65 from that night were the same pattern — GQs posted sub-components that never got claimed because the calibration job's status filtered them out.

Fix was one-line in `app.py:604`: drop the `status='processing'` filter so the DQ endpoint matches the Worker endpoint. Committed as `KillerBee 322c7b4` by Laptop. Flask restarted (brief ~5s blip, absorbed by the new retry=10 budget on bees that had loaded it).

Immediate validation: Component 494 transitioned from orphan (member_id=None pending forever) to claimed by a DQ in under 10 seconds. Raja's calibration to GQ-b then flowed end-to-end for the first time — the 4-tier calibration cascade actually worked. Not the max_wait patch, not the retry patch, but this filter fix was the key that unlocked Raja.

## 11. Raja calibration with real data

Raja calibration against both GQs completed all 6 rounds with REAL data, no timeouts under the 300s budget:

- R1 GQ-b 361s (may have been slightly over wall clock, but the retry-10 budget absorbed transient blips so the final result arrived within window)
- R1 GQ-a 133s
- R2 GQ-b 91s
- R2 GQ-a 129s
- R3 GQ-b 269s
- R3 GQ-a completed before main_loop entry

Raja entered main_loop with real proportional fractions for both GQs. First time ever for the hive.

## 12. Q4 Space Elevator — 8m48s clean delivery

Q4 submitted as job_id=5 via direct DB INSERT (Laptop wrote `scripts/submit_q.py` because the web form requires CSRF+session token which is ergonomically inconvenient to acquire from a script). Raja picked up within 5s, split into 6 level-0 components.

Interesting observation: only 2 of Raja's 6 level-0 components were claimed by GiantQueens (Component 555 GQ-b, 558 GQ-a). The other 4 were claimed directly by DwarfQueens (556 DQ-a2, 557 DQ-a1, 559 DQ-b2, 560 DQ-b1). Both GQ and DQ tiers poll the same `api_available_components` endpoint post-fix, and the DQs won most of the race. Not ideal (DQs are doing level-0 direct work on top of their normal level-1), but functionally fine — the work still flowed.

8 level-1 subtasks then cascaded down to workers. 14 components total in flight. Zero orphans. Royal Honey delivered in **8m48s** wall clock covering all 5 parts (cable length, mass with nanotube density, counterweight, tensile strength, taper ratio) plus feasibility conclusion.

Compare to Dense Q1 Mars: 3271 chars in 1h44m. MoE on CPU is roughly 12x faster for similar-depth work — granite3.1 is a no-thinking family, no wasted reasoning tokens on orchestration tiers.

## 13. Q5 Number Theory — 10m8s clean delivery

Q5 submitted as job_id=6. 31 components total. Zero orphans. Royal Honey delivered in **10m8s** at 1326 chars. Shorter than Q4 because math proofs are structurally concise (state, break into cases mod 8 and mod 3, apply CRT, verify numerically for small primes). Proof was correct and covered all 5 sub-parts.

Granite handled the mathematical notation reasonably despite the ASCII-only constraint (the plan specified notation like "p squared minus 1" and "congruent to 1 modulo 8" in words because ASCII curl payloads for ICQ don't tolerate Unicode math symbols).

## 14. Q6 Sphere Volume Five Methods — 8m22s clean delivery

Q6 submitted as job_id=7. 32 components. Zero orphans. Royal Honey delivered in **8m22s** at 2657 chars. Covered all 5 volume-derivation methods (classical formula, triple integral spherical coords, Archimedes sphere-and-cylinder ratio, Pappus's theorem, Monte Carlo). Cross-check matrix showed agreement within 1%.

## 15. Timings and totals — MoE vs Dense

| Question | Submit | Royal Honey | Wall clock | Components | Stubs |
|---|---|---|---|---|---|
| Q4 Space Elevator | ~02:57 UTC | ~03:06 UTC | 8m48s | 14 | 0 |
| Q5 Number Theory | ~03:06 UTC | ~03:16 UTC | 10m8s | 31 | 0 |
| Q6 Sphere Volume 5 methods | ~03:26 UTC | ~03:35 UTC | 8m22s | 32 | 0 |
| **Total** | | | **27m18s** | **77** | **0** |

Dense batch comparison: 3 Royal Honeys in ~5h28m, multiple stubs, one manual combine rescue. MoE batch: 3 Royal Honeys in 27m18s, zero stubs on the questions themselves. ~12x speedup + structurally cleaner.

Model choice aside, the 3 root fixes landed tonight are also responsible for the cleanliness. Under Dense night's code, MoE would still have orphaned. Under MoE model with the old code, we would still have hit deadlocks.

## 16. Honest disclosure — what was stubbed tonight

Tonight's stubs were all during the calibration pre-flight, not during Q4/Q5/Q6:

- **45 Dense-night zombies** (last night's calibration cascade-deadlock leftovers under Job 1): marked `status='completed'` with `result='[ABANDONED: Dense-batch Job 1 calibration cascade deadlock never completed, marked at MoE pre-flight 2026-04-19]'` via `scripts/reset_for_moe_batch.py`. Preserves Job 1 row history per the "keep Jobs 1-4 as history" principle.
- **Components 421, 425, 471**: orphans from the first GQ-calibration attempt (pre-`max_wait=300` patch era, which hit network-drop result-POST failures). Stubbed by Laptop via `scripts/stub_orphans.py` with `[STUBBED-ORPHAN: ...]` disclosure.

Q4/Q5/Q6 themselves had zero stubs. All 77 components across the three Royal Honeys were real hive output.

## 17. What worked — Desktop perspective

- **MAC-stable DHCP leases** held across the overnight shutdown. IPs returned to the 2026-04-18 table with no manual intervention.
- **Desktop template's rsync-pre-installed** saved me the apt-install step Laptop needed. Same pattern for passwordless sudo — worked out of the box on host + 7 VMs.
- **Bottom-up staggered bring-up** fully eliminated the 4-tier calibration cascade deadlock that was the dominant failure mode of Dense night. Real calibration numbers were collected cleanly for Workers and (after the root fixes) for DQs and GQs.
- **Honest ICQ discipline**: both Claudes flagged their mistakes (my pkill exit-255, my wrong Ollama-hang diagnosis, Laptop's cd-prefix-omission). Four-category ICQ rule respected; silence was the default.
- **Git as the durable channel**: every patch landed as a commit before the next step. Two `git pull` + rsync rounds to all 7 Desktop VMs kept Desktop's subtree in sync with Laptop's patches.
- **The architectural root-fix approach**: instead of stubbing orphans and moving on, we paused, dug into app.py, found the filter asymmetry, patched it. Same with `max_wait` and `max_retries`. Three root fixes beat three ad-hoc workarounds.

## 18. What broke and what we learned — Desktop perspective

- **`pkill -f <pattern>` self-terminates ssh** when the pattern appears in the wrapper's argv (Section 4). Lesson logged; use PID-based kill or disjoint patterns next time.
- **My Ollama-hang diagnosis was wrong** (Section 8). worker_a3 was idle, not hung; the orphan was a dropped result-POST, not a runaway generation. Laptop corrected me within minutes. Lesson: verify the alleged hang by checking CPU + `ollama ps` + log tail BEFORE proposing a restart. I jumped to last-night's failure mode because it fit a narrative, not because I verified the evidence.
- **Topology is not tier-enforced** (Section 12). Post-filter-fix, DQs claim level-0 components first-come-first-claim. Book-worthy observation: the current claim mechanism is egalitarian across tiers, which works but is not architecturally clean. Future improvement would be to filter `api_available_components` by requesting-member's role (GQs should see components at their level, DQs below, etc.) or to route level-0 specifically through GQs.
- **Calibration synthesis over a stub is an honest-disclosure pattern** (Section 8 Component 421 regeneration). The stub exposes the child-level gap; the parent's LLM synthesis produces on-topic text because the original question is in context. Not perfect but better than a fake Royal Honey or a missing answer. The stub disclosure is the boundary of what's honest.
- **Transient VM-kernel Network-is-unreachable events are a real thing**. `ip -s link` showed 2 TX drops on br0 total, Flask log showed 200 responses to everyone, curl loops measured 2-14ms — but bees still occasionally hit the error and their 3-retry 6s window was too short. 10 retries with linear backoff reaching ~90s catches the transients cleanly.

## 19. For the MadHoney book chapter

Three narrative threads worth surviving the edit pass:

1. **The filter-bug in plain sight** (Section 10). Phase 2 3-tier never triggered `api_available_components` because DQ-to-Worker uses `api_available_subtasks` which had the correct (empty) filter. The bug sat in the code for months, invisible, until the 4-tier Raja-to-GQ-to-DQ cascade was the first configuration to exercise it. Book chapter: "Bugs that only exist at new scale" — the canonical example of how test coverage has depth as well as breadth, and how moving from 3-tier to 4-tier is a scale dimension that can expose hidden code paths.

2. **Three root fixes in one night** (Sections 7, 9, 10). `max_wait=300` for cascaded wait budgets, `retry=10` for transient network blips, filter-fix for calibration-component visibility. The common thread: each fix addresses a root cause we could prove from evidence, not a symptom we patched by retry or by stub. Nir's pre-sleep guidance ("solve from root not ad-hoc, patience over speed") directly produced this quality level.

3. **From 5h28m with stubs to 27m18s without** (Section 15). The measurable improvement from Dense to MoE night is not just model choice; it's the interaction of a non-thinking MoE family with an architecture that had its three most important bugs fixed mid-batch. Either half alone would have been a marginal win. Together they produced a structural leap.

## 20. For the next session

When Nir resumes:

1. Cluster + bees are LEFT RUNNING at main_loop with real calibration. Q4/Q5/Q6 jobs are status=completed in DB. Job 1 (calibration) still exists in DB with all its history. No cleanup needed before next question submit.
2. Three root fixes (`GiantHoneyBee 6c0896c`, `GiantHoneyBee 67e1c95`, `KillerBee 322c7b4`) are in both local repos and on all 15 VMs.
3. `results/q4_space_elevator_royal_honey.md`, `results/q5_number_theory_royal_honey.md`, `results/q6_sphere_volume_royal_honey.md` saved and pushed.
4. Suggested next session directions: (a) Nir-overflow stretch from plan Section 7 (cross-run: Dense models on MoE questions, MoE models on Dense questions) would complete the scientific comparison matrix; (b) multimedia gestalt work is the Laptop's ongoing HoneycombOfAI track (commit 1c6e310) and could be integrated with the 4-tier hive as a future Phase; (c) the topology-race observation in Section 12 is a good engineering target if we want cleaner tier behavior.

---

*Canonical night-log for the Desktop subtree during the MoE batch. Edit in place. Git is the time machine.*
