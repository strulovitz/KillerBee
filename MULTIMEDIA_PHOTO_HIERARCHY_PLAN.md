# Multimedia Photo Hierarchy Plan — KillerBee + GiantHoneyBee

**Status:** Planning complete. Implementation not started.
**Author:** Nir + Opus 4.7 (planning session 2026-04-19).
**Scope:** Photo only. Audio and video have their own plans (to be written after photo lands).
**Venue:** Laptop host (10.0.0.8), Debian 13, RTX 5090 (24 GB VRAM). NOT the 15-VM Phase 3 cluster.

---

## 1. Purpose

Yesterday (2026-04-18) the 1-level hive (BeehiveOfAI + HoneycombOfAI) gained multimedia capabilities: a single QueenBee processes photo/audio/video and integrates Worker results into a Royal Honey. See `HoneycombOfAI/MULTIMEDIA_GESTALT_PLAN.md`.

Today extends the same capability to the multi-level hive (KillerBee + GiantHoneyBee): RajaBee → GiantQueens → DwarfQueens → Workers. Each non-leaf tier applies the book's recursive sub-sampling principle — low-fidelity gestalt on its own region, high-fidelity cut pieces dispatched to children, text reports integrated on return.

This plan covers **photo only**. Audio and video follow the same architecture but with different cut functions and models; they will be addressed in sibling plans after photo is proven.

---

## 2. Architectural principles (from The Distributed AI Revolution, Chapters 12-15)

The following are non-negotiable and must be honored in every piece of the implementation:

1. **Every tier perceives with its own vision model on a downsampled view of its region.** (Chapter 15, Slippery Point 2.) Raja perceives the whole photo at low fidelity; a GiantQueen perceives her quadrant at low fidelity; a DwarfQueen perceives her sub-quadrant; a Worker perceives her full-fidelity tile. Upper tiers are NOT blind waiters.
2. **Each tier runs the biggest model its role can support.** (Chapter 15, Slippery Point 3.) In this plan the tier-to-model mapping is derived from `PHASE3_LAPTOP_ROSTER_LOCKED.md`, where the progression from Raja down to Worker is already documented.
3. **Every tier-to-tier hop goes through the KillerBee HTTP API.** No shared-filesystem shortcuts, even when all processes run on one host. (HoneycombOfAI `CLAUDE.md` Rule #1 + our design discussion.)
4. **Workers are leaves.** They do NOT cut further. They process their tile, produce text, return it up.
5. **Grid A + Grid B offset cuts at every non-leaf tier.** (Chapter 12.) Objects sliced by Grid A are recovered by Grid B. Eight children per cut.
6. **The mesh stores insights, not raw observations.** (Chapter 15, Slippery Point 4.) For photo v1 we do not build a vector mesh (out of scope — requires real physical sensors converging on real objects). We just let text reports flow up the tree. The mesh concept is noted so future work knows where to extend.
7. **Configuration space, not locked shape.** (Chapter 15, Slippery Point 5.) The topology here is one valid configuration. Production deployments may choose differently; this plan does not claim uniqueness, only validity.
8. **Input shape discipline.** (Chapter 15, Slippery Point 6 and 7.) Sound Workers hear clips, video Workers see clips, not stills. Photo has no time axis, so this applies to the audio and video plans, not this one — but we note it here as reminder for sibling plans.

---

## 3. Out of scope

Explicitly NOT built in this plan:

- **Audio and video processing.** Sibling plans.
- **15-VM cluster.** Multimedia runs on the host, not in VMs.
- **Vector-mesh / anchor-point RAG over reality (Chapter 14).** Requires real physical drones with multiple senses converging on real objects. We have neither drones nor multiple senses. The mesh stays out of scope until such hardware is available.
- **Distributed single-value sensors (Chapter 11).** No gas / temperature / humidity / light sensors on the host. The single-value-sensor chapter is the cleanest case for the whole hive argument, but it is not what we have hardware to test.
- **3D / 4D physical mapping.** No LIDAR, no drones, no position tracking.
- **Stigmergy, place cells, lateral inhibition.** Future biology borrowings.

These are not rejected — they are simply not the work of this plan. The architecture is designed so they can be added later without refactoring.

---

## 4. Topology

Branching factor is 4-way per grid, Grid A and Grid B together = 8 children per non-leaf tier.

```
                              RajaBee (1)
                                   |
                       cut into 8 (Grid A × 4 + Grid B × 4)
                                   |
             ┌─────────────────────┼─────────────────────┐
        GiantQueen-1            GiantQueen-2    ...   GiantQueen-8   (8 total)
             |                       |                      |
         cut × 8                 cut × 8               cut × 8
             |                       |                      |
       DQ × 8 each            DQ × 8 each           DQ × 8 each      (64 total)
             |                       |                      |
         cut × 8                 cut × 8               cut × 8
             |                       |                      |
     Worker × 8 each         Worker × 8 each       Worker × 8 each   (512 total)
```

**Total: 1 + 8 + 64 + 512 = 585 processes on the host.**

Note: this topology does NOT match the 15-VM Phase 3 roster (1 Raja + 2 GQ + 4 DQ + 8 Worker). The roster is the source of the *model choices per tier*, not the *process count per tier*. Process count is derived from Chapter 12's cut rule. This is consistent with Slippery Point 5 (configuration space): the model stack is documented, the topology is a choice for this plan.

---

## 5. Model stack per tier

Vision models from the roster. Text integrators are the Dense family (MoE dropped: it was chosen in Phase 3 for CPU speed in VMs; on host GPU the advantage disappears and Dense produces more coherent integrations).

| Tier | Vision model | Text integrator | Already on host? |
|---|---|---|---|
| RajaBee | `qwen3.5:9b` (omnimodal) | `qwen3:14b` | both missing |
| GiantQueen | `qwen3-vl:8b` | `qwen3:8b` | vision YES, text missing |
| DwarfQueen | `gemma3:4b` | `phi4-mini:3.8b` | vision missing, text YES |
| Worker | `qwen3.5:0.8b` (omnimodal) | — (leaf, vision only, omnimodal produces text directly) | YES |

**Four models to pull from ollama:** `qwen3.5:9b`, `gemma3:4b`, `qwen3:14b`, `qwen3:8b`. Approximate total download ~25 GB. Disk has 1.1 TB free, no concern.

### 5a. Thinking-mode handling

Qwen3-VL and Qwen3.5-omni models have a thinking phase that, with default options, consumes the `num_predict` budget and leaves `response` empty while the description goes into `thinking`. Mitigations (already documented in `claude-memory/reference_empirical_model_limits.md`):

- Prepend `/no_think` to every prompt at every tier that uses these models.
- Alternative: set `num_predict >= 1024` so the budget covers thinking + response.
- Alternative: read `resp.thinking` as fallback when `resp.response` is empty.

This plan uses **`/no_think`** as the primary choice. `gemma3:4b` and `phi4-mini:3.8b` are not affected.

### 5b. Per-tier image resize

Each tier resizes its input image to the size its vision model prefers. Exact dimensions will be looked up from each model's card at the time that tier's code is written — this plan does NOT fabricate numbers. The resize is applied BEFORE the gestalt inference call. Ollama's vision call auto-resizes when needed, but explicit resize gives us control and avoids surprise token budgets.

---

## 6. Transport principle

All tier-to-tier communication goes through the KillerBee HTTP API. Concretely:

- **Beekeeper** uploads the original photo + text question via the KillerBee web form. The form has a file input field and a media_type selector (text / photo; audio and video will appear later).
- **RajaBee** polls for a pending SwarmJob, GETs the `media_url` from KillerBee, downloads the photo bytes via HTTP GET, runs her gestalt, cuts the photo into 8 pieces, POSTs each piece to KillerBee (the POST creates a JobComponent row + stores the piece file), then waits.
- **Each GiantQueen** polls KillerBee for available components at her level, claims one, GETs the piece URL from KillerBee, downloads the bytes, runs her gestalt, cuts into 8 sub-pieces, POSTs each sub-piece back to KillerBee as a child JobComponent, waits.
- **Each DwarfQueen** does the same on her level.
- **Each Worker** polls for an available leaf component, claims it, downloads its tile bytes, runs its vision model, POSTs the text result back to KillerBee.
- **Text reports flow UP the same API.** Each parent polls `GET /api/component/<parent_id>/children/results`, integrates with her own gestalt via her text model, POSTs her paragraph back.

No tier ever reads a file directly from another tier's filesystem — even though, during single-host dev, all processes share `~/uploads/`. This discipline is what lets the same code run distributed tomorrow without rewriting.

---

## 7. Folder structure on KillerBee server

Self-describing: every path tells the complete lineage without touching the DB.

```
KillerBee/uploads/
  photos/
    swarmjob_<swarmjob_id>/
      original.jpg
      cut_by_raja/
        grid_a_q1.jpg              ← Raja's Grid A quadrant 1 (becomes a GQ input)
        grid_a_q2.jpg
        grid_a_q3.jpg
        grid_a_q4.jpg
        grid_b_q1.jpg              ← Raja's Grid B offset quadrant 1
        grid_b_q2.jpg
        grid_b_q3.jpg
        grid_b_q4.jpg
        cut_by_gq_grid_a_q1/       ← the GQ who received grid_a_q1 cut it into 8
          grid_a_q1.jpg
          ...
          grid_b_q4.jpg
          cut_by_dq_grid_a_q1/     ← the DQ who received that cut into 8
            grid_a_q1.jpg          ← Worker tile (leaf — no deeper folder)
            ...
            grid_b_q4.jpg
          cut_by_dq_grid_a_q2/
            ...
          ...
        cut_by_gq_grid_a_q2/
          ...
        ...
        cut_by_gq_grid_b_q4/
          ...
  audio/     (future)
  videos/    (future)
```

Each JobComponent row carries a `piece_path` column whose value is the server-relative path (e.g. `photos/swarmjob_42/cut_by_raja/grid_a_q1.jpg`) so that the server can serve the bytes and any tier can download them by URL without knowing what component_id they map to.

---

## 8. Cut piece lifecycle

On `POST /api/job/<id>/complete`, after the final Royal Honey is delivered to the Beekeeper:

1. Mark SwarmJob `status = 'completed'` and set `completed_at`.
2. Delete the entire `uploads/photos/swarmjob_<id>/` directory recursively.
3. Leave the JobComponent rows in the DB (they retain `piece_path` as historical reference but the files are gone — this is fine for post-mortem; add a `pieces_deleted` boolean to SwarmJob if later needed).

No automatic cleanup of abandoned jobs — that is a separate operational concern out of scope for this plan.

---

## 9. KillerBee server changes

### 9a. Database migration (Alembic)

Two tables grow, no tables break.

`swarm_jobs` table — add:
- `media_type` (String(16), nullable, default=None) — one of `'text'`, `'photo'`, `'audio'`, `'video'`. Nullable because pre-existing rows are all text.
- `media_url` (String(512), nullable, default=None) — server-relative path to the original file, e.g. `photos/swarmjob_42/original.jpg`. Null when `media_type='text'`.

`job_components` table — add:
- `piece_path` (String(512), nullable, default=None) — server-relative path to this component's media piece. Null for text-only components (legacy + text jobs).

Write the migration file, run on KillerBee's SQLite DB, verify via `.schema` and a SELECT.

### 9b. `models.py`

Add the two columns to `SwarmJob` and the one column to `JobComponent`. Nothing else changes.

### 9c. `forms.py`

Extend `SubmitJobForm`:
- Add `media_type` SelectField with choices `[('text', 'Text only'), ('photo', 'Photo')]`. (Audio and video choices are added later when those plans are built.)
- Add `media_file` FileField, optional. Validation: if `media_type != 'text'`, file is required; otherwise ignored.

### 9d. `app.py` — routes to add

- Extend the existing submit-job POST handler to accept the file upload: if `media_type == 'photo'`, save the uploaded file to `uploads/photos/swarmjob_<new_id>/original.jpg` and set SwarmJob.media_url to that path.
- `GET /uploads/<path:filepath>` — serve files from the uploads directory. Use Flask's `send_from_directory` with the uploads root. Restrict traversal (Flask's safe_join).
- `POST /api/component/<component_id>/upload-piece` — accept a multipart upload containing (a) the binary piece bytes, (b) the piece_path string relative to the job's folder (e.g. `cut_by_raja/grid_a_q1.jpg`). Write the bytes to disk at that path, set the component's `piece_path`.
- Reuse existing endpoints `claim_component`, `submit_component_result`, `get_component_children_results` — these already exist from Phase 3. Just confirm they work for multimedia (media-type-agnostic at that layer).

### 9e. Templates

Add a file input + media_type dropdown to the submit form template. Standard one-form design (text box + attachment button, like every chat UI).

### 9f. Static file security

The `uploads/<path>` route must:
- Resolve paths through `werkzeug.security.safe_join` to prevent directory traversal.
- Not list directories (`autoindex = off`).
- Optionally require authentication for download URLs — for v1 on localhost we skip auth, but note this as a hardening item for distributed deployment.

---

## 10. GiantHoneyBee client changes

### 10a. `killerbee_client.py` — new methods

- `get_job_media(job_id) -> dict` — returns `{media_type, media_url}` from SwarmJob.
- `download_piece(url) -> bytes` — HTTP GET on a URL served by `/uploads/`. Returns raw bytes.
- `upload_piece(component_id, piece_path, image_bytes)` — multipart POST to `/api/component/<id>/upload-piece`. Sets server piece_path.
- `get_children_results(parent_component_id) -> list[str]` — returns the text results of the 8 child components, ordered by grid position. Used for integration.

### 10b. `raja_bee.py`, `giant_queen_client.py`, `dwarf_queen_client.py` — shared branch logic

Each non-leaf client adds a photo branch. Pseudocode:

```python
def process_photo_piece(component_id, piece_url):
    piece_bytes = client.download_piece(piece_url)
    piece_image = PIL.Image.open(io.BytesIO(piece_bytes))

    # 1. Gestalt on my downsampled region
    gestalt_text = run_my_vision_model(
        resize_for_my_vision_model(piece_image),
        prompt="/no_think describe what you see in this image"
    )

    # 2. Cut into 8 children (Grid A 4 quadrants + Grid B 4 offset quadrants)
    children = cut_grid_ab(piece_image)
    #    children = [(name, PIL_image), ...] with 8 entries

    # 3. Upload each child and create JobComponent
    for child_name, child_image in children:
        child_bytes = pil_to_jpeg_bytes(child_image)
        child_path = f"{parent_cut_folder}/{child_name}.jpg"
        child_component_id = client.create_child_component(component_id, child_path)
        client.upload_piece(child_component_id, child_path, child_bytes)

    # 4. Wait for 8 children to complete
    children_results = client.wait_for_children_results(component_id, n=8)

    # 5. Integrate gestalt + children's reports using my text model
    paragraph = run_my_text_integrator(
        prompt=build_integration_prompt(gestalt_text, children_results)
    )

    # 6. Submit my paragraph up
    client.submit_component_result(component_id, paragraph)
```

The three non-leaf tiers differ only in:
- Which vision model name they call (qwen3.5:9b / qwen3-vl:8b / gemma3:4b).
- Which text model name they call (qwen3:14b / qwen3:8b / phi4-mini:3.8b).
- Which resize dimensions they use.
- Which `parent_cut_folder` path prefix their children go into (`cut_by_raja/` / `cut_by_gq_.../` / `cut_by_dq_.../`).

Shared code lives in a new helper module `photo_tier.py` (in GiantHoneyBee) with a `process_photo_piece(tier_name, vision_model, text_model, resize_spec, piece_url, component_id)` function. The three tier clients call it with their specific parameters.

### 10c. `worker_client.py` — photo branch

Workers are leaves. Pseudocode:

```python
def process_photo_tile(component_id, piece_url):
    tile_bytes = client.download_piece(piece_url)
    tile_image = PIL.Image.open(io.BytesIO(tile_bytes))

    # Resize + vision pass (Worker's omnimodal qwen3.5:0.8b)
    result_text = run_vision_model(
        model="qwen3.5:0.8b",
        image=resize_for_qwen35_small(tile_image),
        prompt="/no_think describe what you see in detail"
    )

    # Submit up
    client.submit_component_result(component_id, result_text)
```

### 10d. Cut function (Grid A + Grid B)

For an input image of width W, height H:

Grid A — 4 non-overlapping quadrants covering the full image:
- `grid_a_q1`: `(0, 0, W/2, H/2)` — top-left
- `grid_a_q2`: `(W/2, 0, W, H/2)` — top-right
- `grid_a_q3`: `(0, H/2, W/2, H)` — bottom-left
- `grid_a_q4`: `(W/2, H/2, W, H)` — bottom-right

Grid B — 4 offset tiles straddling Grid A boundaries (same size as Grid A quadrants, centered on Grid A corners):
- `grid_b_q1`: `(W/4, H/4, 3W/4, 3H/4)` — center (spans the middle of the image, catching anything sliced by all four Grid A corners)
- `grid_b_q2`: `(W/4, 0, 3W/4, H/2)` — top-center
- `grid_b_q3`: `(W/4, H/2, 3W/4, H)` — bottom-center
- `grid_b_q4`: `(0, H/4, W/2, 3H/4)` — left-center

Note: the exact canonical Grid B definition lives in `HoneycombOfAI/queen_multimedia.py` from yesterday. The implementation should port that function rather than re-derive — the old queen already solved the boundary-handling edge cases.

---

## 11. First end-to-end test

- **Input:** `/home/nir/Pictures/65291268.JPG` (classical painting).
- **Question:** "What is shown in this photo?"
- **Expected output:** A final Royal Honey paragraph from the RajaBee describing the painting, built by integrating 512 Worker tile descriptions up through 64 DwarfQueens, 8 GiantQueens, and Raja herself. Each intermediate tier contributes its own gestalt observation, not just a summary of its children.

**Steps to run the test:**
1. Verify all 6 required models are present: `ollama list` should show `qwen3.5:9b`, `qwen3-vl:8b`, `gemma3:4b`, `qwen3.5:0.8b`, `qwen3:14b`, `qwen3:8b`, `phi4-mini:3.8b`.
2. Start KillerBee server on port 8877.
3. Start the 585 tier processes (1 Raja, 8 GQ, 64 DQ, 512 Worker). Each process gets its tier role + model pointers via env vars or CLI flags.
4. Log in to KillerBee as a Beekeeper, open the submit-job page, select media_type=photo, attach `65291268.JPG`, type the question, submit.
5. Watch the job progress in the KillerBee web UI (status cycles: pending → splitting → processing → combining → completed).
6. Read the final Royal Honey on the job detail page.
7. Verify `uploads/photos/swarmjob_<id>/` is deleted after completion.

---

## 12. Success criteria

This plan is considered complete when all of the following are true:

1. All 4 missing ollama models have been pulled: `qwen3.5:9b`, `gemma3:4b`, `qwen3:14b`, `qwen3:8b`. `ollama list` confirms.
2. KillerBee DB migration has run. `sqlite3 instance/killerbee.db ".schema swarm_jobs"` shows `media_type` and `media_url`. `.schema job_components` shows `piece_path`.
3. KillerBee submit form accepts a photo upload and stores it under `uploads/photos/swarmjob_<id>/original.jpg`.
4. KillerBee serves any file under `/uploads/<path>` to an authenticated tier client.
5. All 585 tier processes launch and register with KillerBee.
6. Every cut piece transfers via HTTP POST to `/api/component/<id>/upload-piece`, not via direct filesystem writes from a non-server process.
7. Every tier runs its own vision gestalt on its piece (log lines confirm the vision call happened at every level).
8. Every non-leaf tier integrates its children's text + its own gestalt using its text model (log lines confirm the text model call happened at every non-leaf level).
9. The final Royal Honey is a coherent description of the test painting, not a truncated or scrambled concat of Worker outputs.
10. `uploads/photos/swarmjob_<id>/` is fully deleted after `complete_job`.

---

## 13. Root-cause discipline

When something fails during implementation or testing:

- Solve from the root, not with ad-hoc band-aids. (Per `feedback_no_preemptive_infrastructure.md`.) Don't stub orphaned components to make a run "finish." Don't paper over a crashed tier process with a retry wrapper. If a gestalt call returns empty, find out whether it's thinking-mode capture, a wrong prompt, a model-not-loaded error, or a network timeout — and fix the actual cause.
- Do not pre-build infrastructure for theoretical failure modes. If a run succeeds with a known-but-survivable quirk, do not spend a night re-plumbing the quirk out.
- When in doubt, ask Nir. Short question is cheap; long wrong implementation is expensive. (Golden Rule 6.)

---

## 14. Files that will change

### KillerBee repo
- `models.py` — add columns to SwarmJob and JobComponent.
- `forms.py` — extend SubmitJobForm.
- `app.py` — file upload handling in submit-job route, new serve route, new upload-piece API, cleanup on complete_job.
- `templates/*.html` — submit form additions.
- New: `migrations/versions/<hash>_add_multimedia_columns.py` (Alembic).
- New: `uploads/` directory (gitignored, created at runtime).
- Updated `.gitignore` to exclude `uploads/`.

### GiantHoneyBee repo
- `killerbee_client.py` — new HTTP methods (download_piece, upload_piece, get_job_media, get_children_results).
- `raja_bee.py` — photo branch.
- `giant_queen_client.py` — photo branch.
- `dwarf_queen_client.py` — photo branch.
- `worker_client.py` — photo branch.
- New: `photo_tier.py` — shared process_photo_piece helper used by the three non-leaf clients.
- New: `photo_cut.py` — Grid A + Grid B cut function (port from HoneycombOfAI/queen_multimedia.py).

### Optional / later
- Launch script to start 585 processes with correct tier role + model pointers. Separate concern; can be a shell script or a Python supervisor. Not blocking for v1.

---

## 15. Known decisions deferred

These are decisions we consciously did NOT make in this planning session. They are listed so that whoever codes the plan does not re-open them without reason, and so Nir can revisit when relevant:

- **Exact per-tier image resize dimensions.** Looked up per-model at coding time.
- **Worker concurrency model.** The 512 Worker processes on one machine share one GPU via Ollama's serving. That's fine. If Worker throughput is a bottleneck later, we will revisit — not pre-optimize.
- **Authentication on `/uploads/` and `/api/component/<id>/upload-piece`.** On a single host behind localhost, auth is a theoretical concern. Reuse KillerBee's existing session auth for the web form; use the existing tier-client token for the API. Production hardening is a separate plan.
- **Sibling plans for audio and video** — referenced but not written here.

---

## 16. Relationship to existing work

- **HoneycombOfAI multimedia (2026-04-18):** the 1-level hive already does photo/audio/video with a single Queen. Our plan ports the concepts upward into a multi-level tree. The cut function, the varispeed trick for audio, the /no_think handling, the qwen3-vl test reference — all carry over. Files to reference: `HoneycombOfAI/queen_multimedia.py`, `HoneycombOfAI/multimedia_handler.py`, `HoneycombOfAI/MULTIMEDIA_GESTALT_PLAN.md`.
- **PHASE3_LAPTOP_ROSTER_LOCKED.md:** source of per-tier vision and text model choices. Even though multimedia dev is not in VMs, the model progression the roster defined (biggest at top, smallest at Worker) is the right shape and we inherit it.
- **PHASE3_VISION_SWAP_GIANTQUEEN.md:** documents the `qwen3-vl:8b` choice at GQ and the RAM measurement behind it. Useful context if GQ vision behavior surprises.
- **The Distributed AI Revolution chapters 12, 13, 14, 15:** the theoretical backbone. Particularly Chapter 15's seven slippery points — they were correct the last ten times we re-read them and will be correct next time. Read them again if any design choice gets blurry during implementation.

---

## 17. Hand-off

Opus 4.7 planned. Sonnet 4.6 is the intended implementer (per `feedback_workflow.md` — Opus plans, Sonnet codes). Sonnet should:

1. Read this plan top to bottom.
2. Read Chapter 15 of `TheDistributedAIRevolution` before writing code. Not a metaphor; literally reread it.
3. Ask Nir before making any decision that this plan defers (Section 15).
4. Run the test in Section 11 as written.
5. If the run fails, diagnose from the root (Section 13), then fix and re-run. Do not stub, do not skip, do not silently simplify.

When the success criteria in Section 12 are all green, the plan is done. Audio and video plans follow.
