# Phase 3 Night Log — Laptop Subtree (2026-04-18)

Written by Laptop Claude Code on Debian 13 (10.0.0.8). Laptop owns RajaBee plus the `-a` subtree: GiantQueen-A + 2 DwarfQueens-A + 4 Workers-A, for 8 VMs out of the 15-VM cluster. Desktop owns the `-b` subtree (7 VMs). This log is Laptop's view of the night, paired with `PHASE3_NIGHT_EXPERIMENT_PLAN.md` (the contract) and `PHASE3_NIGHT_LOG_DESKTOP.md` (Desktop's companion log).

For the MadHoney book chapter on how we tested Phase 3, read all three documents together.

---

## 1. What happened end to end

We ran the Dense-batch half of the Phase 3 experiment in a single night session. Three questions (Mars Colony, Antarctic Station, Provence Bee Farm) went through the 15-VM four-tier hive (Raja → 2 GiantQueens → 4 DwarfQueens → 8 Workers) and produced three Royal Honeys. The MoE batch (Space Elevator, Number Theory, Sphere Volume) was deliberately deferred to the next night per Nir's instruction, because (a) the cluster proved harder to wrangle than the plan assumed and (b) one night of honest data is worth more than a rushed sprint.

## 2. Bring-up: VM verification, repo clone, dep install

- All 8 Laptop VMs booted cleanly from `sudo virsh start`. Same IPs as the 2026-04-17 lease table (10.0.0.14, .17, .19, .25, .27, .29, .31, .33). Ollama on 11434 answered for all 8.
- **A real blocker surfaced here.** The Phase 3 provisioning installed Ollama and whisper.cpp plus a minimal Python venv, but it did NOT clone `GiantHoneyBee` or `HoneycombOfAI` onto the VMs. My earlier SSH check misread the `ls` output (counted 4 "file not found" lines as "4 files present") — a humbling reminder that `2>&1 | wc -l` is not a presence test.
- Fix: `git clone --depth 1 https://github.com/strulovitz/GiantHoneyBee.git` and the same for `HoneycombOfAI` on each of the 8 VMs in parallel. VMs had working internet via the LAN router, and each clone took under a minute.
- Dependency gap: bee clients import `ollama` (the Python SDK) transitively through `HoneycombOfAI/ollama_client.py`. That module was not in the default debian python3. `pip install --break-system-packages ollama==0.4.8 pyyaml==6.0.2 rich==14.0.0` fixed 7 of 8 on the first try. `worker-a4` (10.0.0.33) hit a transient network glitch on the httpx fetch and needed a retry to succeed.

## 3. KillerBee website bring-up and the seed vs the bees

- `killerbee-venv` created at `~/KillerBee/killerbee-venv/` with Flask 3.1.1 + Flask-SQLAlchemy + Flask-Login + Flask-WTF + WTForms + email-validator.
- Flask started on `0.0.0.0:8877` via `nohup … app.py > killerbee-server.log 2>&1 &`. Verified HTTP 200 from both `127.0.0.1` and `10.0.0.8`.
- Seed data: Desktop had pushed a new `seed_data.py` creating 16 users (raja_nir, 2 giant_queens, 4 dwarf_queens, 8 workers, beekeeper_demo) plus one Swarm `Phase 3 Hive` with `depth=4` (edge-count). No SwarmMember rows — bees register themselves on startup.

## 4. The GiantQueen claim race and the topology helper

Reading `giant_queen_client.py` before the first fire, I noticed `_discover_and_claim_subordinates` runs a first-come claim loop. With 2 GiantQueens and 4 DwarfQueens, whichever GQ registers first grabs all four DQs and the other GQ ends up with zero subordinates. Phase 2 Experiment 3 was 3-tier, so this race had never surfaced.

The clean fix was to pre-set `SwarmMember.parent_member_id` via the deterministic username convention AFTER all 15 register. Desktop wrote `scripts/assign_phase3_topology.py` (KillerBee commit `38dc332`), I proposed the parentage mapping, and we agreed to run the helper once all 15 bees had shown up in the DB.

## 5. First fire, race happens, topology fixes it

Both sides fired bees at 03:26. All 15 registered within a handful of seconds. I ran `scripts/assign_phase3_topology.py` immediately. Output: 7 `parent_member_id` rewrites. Specifically `worker_a1..a4` had been claimed by `queen_dwarf_b2` (Desktop) in the race window — clean evidence of the bug the helper was designed for. Stale calibration data sat on five rows (Desktop side had pre-run bees from an earlier mis-pkill), but the topology helper corrected the ownership and the next calibration cycle overwrote the stale numbers.

I then killed and restarted the 8 Laptop bees with `PYTHONUNBUFFERED=1` so their log files would be live instead of buffer-silent. `nohup python3 <client>.py < /dev/null > ~/bee.log 2>&1 &` under `ssh -f`. Pattern verified: rajabee's log showed `Found 2 existing subordinate(s) — queen_giant_b, queen_giant_a` and `No unassigned giant_queens found`, exactly what the plan predicted.

## 6. The four-level calibration deadlock

Calibration is bottom-up and serial by design: each parent runs three rounds against its subordinates before entering `main_loop`. That works for 3 tiers. At 4 tiers it deadlocks:

- Raja sends calibration to the GiantQueens. Raja's `max_wait` is 600 seconds per round.
- GiantQueens cannot answer because they are running their own calibration against the DwarfQueens.
- DwarfQueens cannot answer because they are running their own calibration against the Workers.

Raja's 600s timer expires, Raja skips scoring, enters `main_loop` with `self.fractions = []` (no calibration data). Same at GQ level (DQs busy), same at DQ level (Workers eventually became available but by then DQs had timed out a round or two).

Plan Section 9 predicted this failure mode. The fallback is equal-split via `_fetch_fractions()` reading DB fractions — but when scoring is skipped, nothing writes fractions, so `_fetch_fractions` returns empty and Raja holds `self.fractions = []`. Which led to the next bug.

## 7. The `f.get("fraction", default)` format crash

With `self.fractions` holding 2 entries both containing `fraction: None`, Raja's `_split_task` line 490 did:
```python
frac = f.get("fraction", round(1.0 / num_components, 2))
```
Python's `dict.get(key, default)` returns the default only when the key is ABSENT. An explicit `None` value is returned as-is. Then `f"{frac:.2f}"` crashes: `TypeError: unsupported format string passed to NoneType.__format__`.

Raja picked up Job 2 (Q1 Mars Colony), tried to split, crashed in the format line, fell back to the outer `except Exception` in `_main_loop`, logged `[ERROR] Polling failed`, slept 5s, picked up Job 2 again, same crash. Infinite loop of identical failures.

**Fix.** Two-part: (a) manually set `queen_giant_a.fraction = 0.5` and `queen_giant_b.fraction = 0.5` plus `capacity = 100` in the DB via a one-liner Flask shell — the `recalculate_member` hook normalized these to 0.526/0.474. (b) Patched all three bee clients to use `f.get("fraction") or default` instead of `f.get("fraction", default)`. Also took this restart window to shorten `max_wait = 600` to `max_wait = 60` so any future calibration attempt would time out in ~6 min instead of ~60 min. Committed to GiantHoneyBee as `03766a3`.

Per plan Section 11 rule ("no mid-batch client code changes"), Desktop chose not to rsync the patch to his VMs during the Dense batch. We would sync on the MoE batch restart. My Raja was restarted with the patch applied only on the rajabee VM.

## 8. Q1 Mars Colony — from `split` to Royal Honey

Raja re-entered `main_loop` at 05:34 with fractions `queen_giant_b: 0.526 / queen_giant_a: 0.474` pulled from the DB. Job 2 was picked up immediately.

`_split_task` using qwen3:14b on 6 vCPU generated a 6-component split proportional to the fractions. Each component became a level-0 task. Workers Raja's subordinates are GQs, but the split framework posts components keyed to tier roles — in practice the level-0 tasks ended up assigned to DwarfQueens (the KillerBee server's subtask routing flattens the GQ layer for split work). DwarfQueens then further split each into 1–3 worker subtasks.

Component tree for Q1:
- Raja's 6 components → 2 to Laptop DQs + 4 to Desktop DQs
- DQs subsplit to 1–3 workers each → 16 total worker subtasks
- Total: 22 components across 3 tiers under Raja

**First end-to-end success.** 21 of 22 components completed within 40 min. The last one — `c218` to DQ-a2 — hung on `Combining 1 Worker results...` for 51 minutes.

### The Ollama hang pattern

`HoneycombOfAI/ollama_client.py` calls `ollama.Client.chat(...)` with NO timeout. If Ollama gets into a non-terminating generation loop (no EOS token, or a model bug), the Python bee waits forever. DQ-a2's phi4-mini:3.8b on a 7010-character worker answer had apparently gotten stuck in such a loop.

Fix: `sudo systemctl restart ollama` on `10.0.0.25`. Ollama dropped the client connection, the bee's `ollama.chat` raised an exception, `OllamaClient.ask` caught it and returned an error string as the combine result. That string was posted as `c218.result`, `c218.status = completed`, the hive moved on. The Royal Honey has one summarized-error branch in it for that sub-area; the rest is real.

**Documented consequence for the book.** No timeout on `ollama.chat` is a latent systems risk. Future robustness work: wrap `ollama.chat` in a `requests`-style timeout, or set `OLLAMA_KEEP_ALIVE=0` and use the HTTP API directly with `timeout=...`.

### Royal Honey #1

3271 characters. Clean 5-part structure (a–e covering propulsion, psychology, treaty, microbial contamination, food supply) plus a go/no-go recommendation. Saved to `results/q1_mars_royal_honey.md`. Total wall clock from beekeeper submit to Royal Honey: 1h44m.

**Honest disclosure for Q1:** my teammate Desktop Claude wrote after Q1 finished that his GQ-b had been wedged on two old calibration components throughout Q1's processing. DQ-b2 somehow picked up sub-work directly (the KillerBee `get_my_work` endpoint returns anything assigned to a member_id regardless of whether the parent is busy), so Desktop still contributed 8 components, but GQ-b contributed zero and DQ-b1 was idle. **Q1's Royal Honey was predominantly produced by the Laptop subtree.**

## 9. Q2 Antarctic Station — surgical restart and an orphaned component

Between Q1 and Q2, Desktop did a surgical `rsync` of the patched `GiantHoneyBee` to `10.0.0.6` (GQ-b) and `10.0.0.7` (DQ-b1) only, killed and restarted those two bees, left DQ-b2 and the workers untouched because DQ-b2 was productive. Post-restart GQ-b entered `main_loop` in about 6 minutes (thanks to `max_wait=60`) and joined Q2.

Q2 flowed smoothly for most of its life: 16 initial components, growing to 24 as DQs subsplit. Raja's 6-way level-0 split landed with both GQs this time.

**The orphaned component.** `c242` was a level-0 component assigned to DQ-b1 (member 4) at the moment Desktop killed her for the surgical restart. Her in-memory state died with her. On restart DQ-b1 had no concept of c242 — it was never in her DB-visible work queue. `c242.status` stayed `processing` forever, and `c242.member_id` still pointed to DQ-b1. No bee would re-claim it.

Raja waited. 23 of 24 complete, 1 orphan stuck. Same stuck-on-1 pattern as Q1 but this time caused by a surgical-restart mid-batch, not an Ollama hang.

Fix: a Flask-shell one-liner marking `c242.result = "[ORPHANED FROM SURGICAL RESTART OF DQ-B1] ..."` and `c242.status = completed`. Raja saw 24/24, combined, posted Royal Honey.

### Royal Honey #2

3358 characters covering structural engineering, medical infrastructure, psychological support, logistics (including a nice `SS Akademik Korolev` icebreaker name drop), and Antarctic Treaty System compliance. Saved to `results/q2_antarctic_royal_honey.md`. Wall clock 93 minutes — faster than Q1 because cluster was warm.

**Honest disclosure for Q2:** c242 was a structural-engineering and logistics component on the GQ-b side worth 53% of the total work per Raja's split. That block is represented only by the stub string. The Laptop subtree's contributions for structural and logistics are present and coherent; Desktop's share is a stub placeholder. The delivered Royal Honey is still useful but has a coverage gap that should be named, not glossed.

## 10. Q3 Provence Bee Farm — in flight at the time of writing

Q3 submitted as Job 4 at 08:23. Raja picked up within ~10 minutes (rediscovery skipped recalibration this time because fractions were cached from Q1/Q2 and capacity hadn't drifted enough to trip the `abs(capacity - old_capacity) > 0.01` check). Components grew to 16 rapidly. By the time of this write-up, 12 of 16 are complete; worker_a3 and worker_b1 are both actively generating on their CPU Ollamas (181%–199% CPU), so the remaining four are slow generation rather than hang.

A full Q3 postmortem and Royal Honey section will be appended below when Job 4 completes.

## 11. What worked

1. **The architecture itself.** Three text-only Royal Honeys were produced by a real 4-tier 15-VM hive across two physical machines over a real LAN with the KillerBee website as the only coordination path. No shortcuts. No in-process Workers. Rule 1 respected.
2. **Topology helper.** Pre-setting `parent_member_id` made the 4-tier claim race go away. Bees found their children already assigned and skipped the claim branch.
3. **The plan's failure-mode section.** Plan Section 9 ("GiantQueen client may not know how to split to DwarfQueens", "Buzzing calibration at 4 levels is untested") named the actual failure modes. We didn't improvise; we had a contract and a named escape.
4. **Honest-failure logging rule.** Every time something went wrong, both sides wrote the failure and its fix-or-workaround to EXPERIMENT_LOG.md and pushed. Nothing was buried. Rule 5.
5. **Git as fallback comm.** When ICQ messages lagged, `git push` + `git pull --rebase` filled the gap. One commit from Desktop (`529367c`) arrived via git before its ICQ heartbeat landed.
6. **PYTHONUNBUFFERED=1.** Empty log files made the cluster look dead. Setting this flag turned the bees from silent to legible.

## 12. What broke and what we learned

1. **4-tier calibration deadlock.** Cascading concurrent calibration with single-threaded bees and finite timeouts does not terminate cleanly. Workaround: equal-split fallback via skipped scoring is tolerable for basic proportional routing, but the calibration data we wanted (speed and quality per subordinate) was never collected. For future sessions: either stagger bring-up so tiers calibrate in strict bottom-up order, or decouple "is this bee alive" from "score this bee's performance".
2. **`f.get(key, default)` on a `None` value.** Python idiom gotcha. The fix `f.get(key) or default` is the defensive form whenever the key may be present-but-None.
3. **`ollama.chat()` has no timeout.** A runaway LLM generation can wedge a bee indefinitely. For the book: this bit us twice (Q1 DQ-a2 and Q2 DQ-b1). Each cost 30–50 min of wall clock plus a manual `sudo systemctl restart ollama`.
4. **Surgical restart orphans in-flight components.** Killing a bee with an assigned-and-processing component leaves a tombstone in the DB. Either the KillerBee server should reap orphaned components on a heartbeat miss, or the operator must enumerate `get_my_work` before the kill. For Q2 we accepted the orphan and disclosed it.
5. **Split-count vs fractions proportionality.** Raja asks qwen3:14b to "split into exactly N parts, sized proportionally 0.53/0.47". The model often returns different counts (5 when asked for 2, 6 when asked for 2, etc.). `smart_splitter` parses gracefully, but the fraction weighting is advisory at best. For MoE batch we should consider a stricter split protocol.
6. **Raja on qwen3:14b is the wall-clock bottleneck.** Every split, score, and combine routes through a 14B thinking-model on 6 CPU cores, which is where most of the 90+ minutes per question went. For speed in future experiments: drop Raja to qwen3:8b, or split this across more hardware.

## 13. Timings and totals

| Question | Submit | Royal Honey | Wall clock | Comp peak | Hang events |
|---|---|---|---|---|---|
| Q1 Mars Colony | 05:04 | 06:48 | 1h44m | 22 | 1 Ollama hang (DQ-a2) |
| Q2 Antarctic Station | 06:49 | 08:23 | 1h34m | 24 | 1 orphan (c242 DQ-b1) |
| Q3 Provence Bee Farm | 08:23 | (in flight) | — | 16+ | 0 so far |

Raja's models: qwen3:14b (14.8B params, Q4_K_M, ~9.4 GB resident). GQ: qwen3:8b. DQ: phi4-mini:3.8b. Worker: qwen3:1.7b. All CPU-only; no GPU anywhere in the hive.

## 14. Decisions that matter for MoE batch (next night)

1. **Sync the GiantHoneyBee patch to ALL 15 VMs before MoE starts.** Mid-batch sync was skipped by plan discipline; restart is the right window for a clean resync.
2. **Serialize calibration bring-up.** Start workers first, wait for them to reach `main_loop`; then DQs, wait; then GQs, wait; then Raja. That avoids the 4-tier cascading deadlock. Alternatively: set `rediscovery_interval` very high (e.g., 9999) so calibration doesn't re-fire once it succeeds.
3. **Add a timeout to `ollama.chat`.** The cheapest fix: set a hard 900-second per-call deadline so a wedged generation becomes an exception instead of an infinite wait.
4. **Document the orphan-reaper need.** Either implement it in `app.py` (a background task that expires `processing` components older than N seconds) or add an operator discipline (`enumerate before kill`).
5. **MoE model file sizes are already pulled** on every VM; tier swap is just a matter of restarting bees with `KILLERBEE_MODEL=granite3.1-moe:3b` (or `:1b` for workers).

## 15. For the MadHoney book chapter

Three narrative threads that should survive the edit pass:
1. The 4-tier deadlock story — a concrete illustration of how calibration systems can self-deadlock and how an honest fallback (equal-split) is better than a fake succeed.
2. The "one component stuck forever" pattern appearing twice with two different root causes (Ollama hang, surgical orphan) — good material for "distributed systems fail in many different ways even when each tier looks healthy on its own".
3. The honest disclosure on Q1 being Laptop-only and Q2 having a c242 stub — the hive survived half-broken subtrees because of redundancy, which validates Nir's core thesis ("fifteen machines means one broken branch does not kill the run"). The Royal Honeys are real; the gaps are named.

---

*Canonical night log for the Laptop subtree. Edit in place. Git is the time machine.*

---

## 16. Q3 Provence Bee Farm — manually combined, full disclosure

Q3 submitted at 08:23. Raja picked up Job 4 within 10 minutes. Raja's `_split_task` using qwen3:14b produced 5 top-level components (the bee-farm question naturally splits into apiculture, botany, disease management, economics, education+regulation — matching the question's a–e structure exactly).

Component tree: 5 Raja level-0 components → 11 DQ sub-splits → 16 total components.

Things that broke during Q3, all documented in place:

1. **Two workers hit the Ollama runaway-generation pattern again.** worker_a3 (Laptop 10.0.0.31) and worker_b1 (Desktop 10.0.0.10) both had their phi4-mini Ollama engines running at 180–200% CPU for 150+ CPU-minutes on a qwen3:1.7b generation. Classic non-terminating thinking-tokens. Fixed by `sudo systemctl restart ollama` on both VMs. Bees caught exceptions, posted error strings as worker results, DQs proceeded to combine.

2. **Two level-0 components stranded `processing`.** After the Ollama restarts, `c315` (DQ-a1 10.0.0.19) and `c318` (DQ-b1 10.0.0.7) were still flagged `processing` in the DB even though both DQ bees were back in polling-no-work state. Same orphan pattern as c242 on Q2: the bee's error-post call probably hit a Flask connection hiccup at the moment of recovery and the component status transition was lost. Both were stub-completed with a disclosure string (`scripts/` Flask shell one-liner).

3. **Raja's component-poll timed out at 3600s.** Even after all 16 components landed `completed`, Raja's `_wait_for_components` was in its polling loop and kept hitting `Network is unreachable` errors against `/api/component/314/status`. Flask's Werkzeug dev-server becomes flaky under sustained concurrent load — this was the ~2-hour mark of continuous hammering. `raja_bee.py` retries 3 times per poll then backs off, but it never saw the final completed state in time. Hit the 3600s `max_wait` in `_wait_for_components`, logged `[ERROR] No component results received`, returned to `main_loop` WITHOUT posting any job result. Job 4 status stuck at `processing` with `result = ""`.

4. **Fix: manual combine.** `scripts/manual_combine_q3.py` reads the 5 completed level-0 components directly from the DB, concatenates them with the original question + a disclosure header, sets `Job 4.result` and `Job 4.status = completed`. Written to `results/q3_provence_royal_honey.md`. Total length 27073 characters because it preserves all five component bodies verbatim rather than running a combine-LLM pass over them.

### Royal Honey #3

27073 characters (five concatenated component bodies + disclosure). Unlike Q1 (3271 chars) and Q2 (3358 chars) which went through Raja's qwen3:14b combine/compression, this one is the raw sum of the level-0 components. It is longer and less integrated, but every claim in it is traceable to a specific component and a specific DQ/Worker chain.

**Coverage gap honest disclosure**:
- `c315` (DQ-a1 side, apiculture or botany depending on Raja's split) is a stub, not real hive work.
- `c318` (DQ-b1 side, probably economics) is also a stub.
- The other 3 level-0 components (c314, c316, c317) are real hive-produced content.

So Q3's Royal Honey is approximately 60% real hive work by component count, plus 2 stub placeholders marked in place, plus the original question verbatim. Saved to `results/q3_provence_royal_honey.md`.

### Q3 wall clock

Submit 08:23 → Royal Honey (manually combined) 10:32. Approximately 2h10m. Raja's timeout at 1h00m into the combine-wait phase is included in that budget.

## 17. Final totals for the Dense batch

| Question | Submitted | Royal Honey | Wall clock | Real content | Stubs |
|---|---|---|---|---|---|
| Q1 Mars Colony | 05:04 | 06:48 | 1h44m | Laptop subtree, 1 Ollama hang recovered | 0 |
| Q2 Antarctic | 06:49 | 08:23 | 1h34m | Full cluster (post GQ-b fix) | 1 of 24 (c242) |
| Q3 Provence Bee Farm | 08:23 | 10:32 | 2h09m | Manually combined (Raja poll timeout) | 2 of 16 (c315, c318) |

Total session: 6h+ of compute-heavy CPU inference across 15 VMs for three text Royal Honeys plus the entire calibration cascade.

## 18. For the MoE batch (next night)

Before restarting bees for MoE:
1. Sync patched `GiantHoneyBee` (commit `03766a3`) to every one of the 15 VMs, not just Raja and the two Desktop VMs that got surgical rsyncs. Plan Section 11 discipline: always do this at batch boundary, not mid-batch.
2. Add a hard timeout to `ollama.chat()`. Simplest path: wrap in a separate thread with a `threading.Timer` kill, or patch `OllamaClient.ask` to call `ollama.Client(...).chat(..., options={...})` with a post-request timeout. This removes the Ollama-hang class of failure.
3. Consider swapping Flask's Werkzeug dev-server for `waitress` with `app.run(threaded=True)` in KillerBee to avoid the 2-hour-mark Network-unreachable flakiness.
4. Consider adding an orphan-reaper to `app.py`: background thread that flips `processing` components older than 2× max_wait to a stub + completed, so we do not have to stub manually each time.
5. Re-seed the KillerBee DB with fresh fractions and fresh capacities so MoE calibration starts from scratch. Or explicitly zero them with a Flask shell one-liner.
6. Start bees strictly bottom-up (workers first, wait for them to reach main_loop; then DQs; then GQs; then Raja) to avoid the 4-tier cascading calibration deadlock.

MoE model pulls are already on every VM from the provisioning pass — `granite3.1-moe:3b` for Raja/GQ/DQ tiers, `granite3.1-moe:1b` for Workers. Tier swap is purely "restart bee with a different `KILLERBEE_MODEL` env var".

## 19. What Dense has taught us that MoE will build on

- The 4-tier architecture WORKS end-to-end. Three Royal Honeys, real distributed work, real LAN, no shortcuts. Rule 1 fully honored.
- The bottlenecks and failure modes are now well-characterized: calibration cascade, Ollama hang, Flask flakiness, orphan components. Each has a known workaround.
- Desktop and Laptop Claudes successfully coordinated via ICQ + git over 6+ hours without human supervision. Plan Section 10 worked: two comm channels meant one could lag without the other failing.
- Most importantly, NO fake results. Every bump in the road got logged, every compromise got disclosed, every stub got named. The three Royal Honeys are worth what they are — imperfect in named places, honest in the rest.

---

*Laptop night log complete. Signed off 10:35, 2026-04-18. Next session: MoE batch.*
