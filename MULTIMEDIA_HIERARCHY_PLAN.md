# Multimedia Hierarchy Plan — KillerBee + GiantHoneyBee

**Status:** Planning complete. Implementation not started.
**Author:** Nir + Opus 4.7 (planning session 2026-04-19).
**Scope:** All three modalities — photo, audio, video — in one plan, one implementation effort.
**Implementation sequence:** Photo first, audio second, video third. Fixes discovered in one modality carry forward to the next. NOT three separate plans across days.
**Venue:** Laptop host (10.0.0.8), Debian 13, RTX 5090 (24 GB VRAM). NOT the 15-VM Phase 3 cluster.

---

## 1. Purpose

Yesterday (2026-04-18) the 1-level hive (BeehiveOfAI + HoneycombOfAI) gained multimedia capabilities in one day: a single QueenBee processes photo, audio, and video end-to-end, and integrates Worker results into a Royal Honey. See `HoneycombOfAI/MULTIMEDIA_GESTALT_PLAN.md`.

Today extends the same capability — all three modalities — into the multi-level hive (KillerBee + GiantHoneyBee): RajaBee → GiantQueens → DwarfQueens → Workers. Each non-leaf tier applies the book's recursive sub-sampling principle: low-fidelity gestalt on its own region, high-fidelity cut pieces dispatched to children, text reports integrated on return.

**This plan covers all three media types.** The implementation runs in sequence (photo, audio, video), but it is one effort, and any bug or design fix discovered while building photo is carried forward to audio and to video without re-planning.

---

## 2. Implementation sequence

1. **Photo** — built first. Lowest surface area: no time axis, no temporal cut decisions, smallest binaries. Validates the tier-to-tier HTTP transport, the folder structure, the /no_think handling, the per-tier gestalt-plus-integrate shape. When photo's first Royal Honey is clean, move to audio.
2. **Audio** — adds the time axis. Introduces varispeed-based gestalt at the parent (Chapter 15 Slippery Point 6: time compression, not sample-rate reduction). Re-uses the transport, folder, and integration code from photo; only the cut function and the gestalt operation are new.
3. **Video** — combines both. Visual frames handled like photos but over time (low-FPS sampling for parent gestalt, per Chapter 15 Slippery Point 7; clips-not-frames for Workers so motion is actually perceived). Audio track handled by the audio pipeline, fused at integration. Re-uses everything from photo and audio.

If photo gets stuck, we fix from the root (not a stub, not a workaround), then the audio and video implementations inherit the fix automatically. Same for fixes discovered during audio.

---

## 3. Architectural principles (from The Distributed AI Revolution, Chapters 12-15)

Non-negotiable. Honor in every piece of the implementation.

1. **Every tier perceives with its own model on a downsampled view of its region.** (Chapter 15, Slippery Point 2.) Upper tiers are NOT blind waiters.
2. **Each tier runs the biggest model its role can support.** (Chapter 15, Slippery Point 3.) Tier-to-model progression is from `PHASE3_LAPTOP_ROSTER_LOCKED.md`: biggest at Raja, smallest at Worker.
3. **Every tier-to-tier hop goes through the KillerBee HTTP API.** No shared-filesystem shortcuts even on a single host. (HoneycombOfAI + KillerBee `CLAUDE.md` Rule #1, plus our design discussion.)
4. **Workers are leaves.** They do NOT cut further. They process their unit (tile / slice / clip), produce text, return it up.
5. **Grid A + Grid B offset cuts at every non-leaf tier.** (Chapter 12.) 8 children per cut. Spatial for photo; temporal for audio; temporal for video visual; temporal for video audio track.
6. **Input-shape discipline at the Worker tier.** (Chapter 15, Slippery Points 6+7.) Image Workers see tiles. Audio Workers hear slices. Video Workers see clips (not frames). Motion is perceived by the model, not reasoned by the integrator from stills.
7. **The "mesh" from Chapter 14 is out of scope** for this plan — it requires physically-present multi-sensor convergence at real-world anchor points, which we do not have. Text reports flow up the tree directly.
8. **Configuration space, not locked shape.** (Slippery Point 5.) The topology and models here are one valid configuration. Do not claim uniqueness.

---

## 4. Out of scope

Explicitly NOT built here:

- **Vector-mesh / anchor-point RAG over reality (Chapter 14).** Needs real physical drones converging on real objects with multiple senses. We have none.
- **Distributed single-value sensors (Chapter 11).** No gas / temperature / humidity / light sensors on the host.
- **3D / 4D physical mapping.** No LIDAR, no drones, no position tracking.
- **Stigmergy, place cells, lateral inhibition.** Future biology borrowings.
- **15-VM cluster.** Multimedia dev is on the host, period.

Not rejected — just not this plan's work. The architecture is designed so these can be added later without refactoring.

---

## 5. Shared topology

4-way branching per grid, Grid A and Grid B together = 8 children per non-leaf tier, three levels of cut.

```
                              RajaBee (1)
                                   |
                       cut into 8 pieces
                                   |
             ┌─────────────────────┼─────────────────────┐
        GQ-1                     GQ-2             ...   GQ-8        (8 total)
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

**What varies per modality:** what "cut into 8 pieces" actually does. For photo it is spatial (Grid A + Grid B quadrants). For audio it is temporal (time sections). For video it is temporal (time clips) for visual plus separate temporal cuts on the audio track.

**Input-length adaptation.** 585 is the *maximum* topology. For a short input (e.g., a 30-second video) some tiers will pass their piece through intact because no further cut is useful — a DwarfQueen receiving a 0.9-second audio sub-piece does not try to cut it into eight 0.1-second sub-sub-pieces. Tier pass-through is a normal case, not a failure. Long inputs (e.g., a 30-minute meeting recording) fill the tree.

**Note on roster:** this topology does NOT match the 15-VM Phase 3 roster process count (1+2+4+8). The roster is the source of the *model choices per tier*, not the *process count per tier*. Process count here is derived from Chapter 12's Grid A + Grid B cut rule.

---

## 6. Model stacks per media type

Per-tier model progression is the same across modalities for the *text integrator* (each non-leaf tier combines its gestalt with its children's text). Perception models differ because the input differs: vision for photo, STT (speech-to-text) for audio, vision + STT for video.

### 6a. Photo

| Tier | Vision (gestalt) | Text integrator | On host? |
|---|---|---|---|
| RajaBee | `qwen3.5:9b` (omnimodal) | `qwen3:14b` | both missing |
| GiantQueen | `qwen3-vl:8b` | `qwen3:8b` | vision yes, text missing |
| DwarfQueen | `gemma3:4b` | `phi4-mini:3.8b` | vision missing, text yes |
| Worker | `qwen3.5:0.8b` (omnimodal) | — (leaf, vision only) | yes |

### 6b. Audio

| Tier | STT (gestalt) | Text integrator | On host? |
|---|---|---|---|
| RajaBee | `whisper large-v3-turbo` | `qwen3:14b` (shared with photo) | whisper yes via `~/.local/bin/whisper`; text missing |
| GiantQueen | `whisper small` | `qwen3:8b` | whisper downloads on first use; text missing |
| DwarfQueen | `whisper tiny` | `phi4-mini:3.8b` | same |
| Worker | `whisper tiny` | — (leaf, STT output IS the text) | same |

Whisper at the parent tiers operates on a **time-compressed** version of the whole audio region (2× varispeed via ffmpeg `asetrate`). The empirical 2× ceiling from `reference_empirical_model_limits.md` is respected — above 2× whisper produces garbage. Per-tier whisper-model size (large → tiny) matches the roster.

### 6c. Video

Video has both a visual track and an audio track. Both flow up the tree; each tier produces a combined paragraph.

| Tier | Visual gestalt (on low-FPS sampled frames) | Audio gestalt (on time-compressed audio track) | Text integrator | Worker unit |
|---|---|---|---|---|
| RajaBee | `qwen3-vl:8b` with up to 60 frames @ /no_think | `whisper large-v3-turbo` on 2× varispeed | `qwen3:14b` | — (not a leaf) |
| GiantQueen | `qwen3-vl:8b` @ /no_think | `whisper small` on 2× varispeed | `qwen3:8b` | — |
| DwarfQueen | `qwen3-vl:8b` @ /no_think | `whisper tiny` on 2× varispeed | `phi4-mini:3.8b` | — |
| Worker | `qwen3-vl:8b` on a **video clip** of ~3 s sampled at 2 FPS (≈6 frames) @ /no_think | `whisper tiny` on the clip's audio slice | — (leaf) | video clip + video-audio slice |

**Why `qwen3-vl:8b` at all tiers for video** rather than the roster's per-tier vision progression: the roster's Worker vision model `qwen3.5:0.8b` is untested for multi-frame input. Slippery Point 7 demands Workers see clips, not single frames. `qwen3-vl:8b` is the only vision model on the host that is *documented to handle multi-frame input* (60 frames tested, `reference_empirical_model_limits.md`). Using a single vision model for video across all tiers is a conscious deviation from the roster, justified by Slippery Point 7's motion-perception requirement.

---

## 7. Models to install on host

Combined across all three modalities. Use `ollama pull` for each.

- `qwen3.5:9b` — Raja vision (photo).
- `gemma3:4b` — DwarfQueen vision (photo).
- `qwen3:14b` — Raja text integrator (all modalities).
- `qwen3:8b` — GiantQueen text integrator (all modalities).

Approximate total download ≈ 25 GB. Disk has 1.1 TB free.

Already on host (verified 2026-04-19): `qwen3-vl:8b`, `qwen3.5:0.8b`, `phi4-mini:3.8b`, `qwen3:1.7b`, `llama3.2:3b`.

Whisper is installed at `~/.local/bin/whisper`. Model weights auto-download on first use per size.

ffmpeg is needed for audio varispeed, video frame sampling, and audio-track extraction from video. Verify with `ffmpeg -version` before coding — if missing, `sudo apt install ffmpeg` (not an NVIDIA/CUDA package; safe to install).

---

## 8. Thinking-mode handling

`qwen3-vl` and `qwen3.5` omnimodal families route vision output to `thinking` field by default; ref in `reference_empirical_model_limits.md`. Mitigation at every inference site:

1. Prepend **`/no_think`** to every prompt at every tier that uses these models (photo: Raja, GQ, Worker; video: every tier).
2. Belt-and-suspenders: read `resp.thinking` as fallback when `resp.response` is empty.
3. Keep `num_predict` generous (≥1024) so a thinking budget cannot starve the visible response.

`gemma3:4b` and `phi4-mini:3.8b` are not affected.

---

## 9. Per-tier image/audio/video resize and compression

Each tier feeds its perception model the shape that model expects. Concrete numbers are looked up per-model at coding time — do NOT fabricate. The principle per modality:

- **Photo** — resize to the tier's vision-model preferred pixel dimensions. Ollama auto-resizes but explicit resize gives predictable token budgets.
- **Audio** — time-compress via ffmpeg `asetrate=<rate*2>,aresample=<rate>` (2× varispeed). Each parent tier's gestalt is computed on the 2×-compressed version of its whole region. Slippery Point 6: the axis to compress is time, not sample rate.
- **Video visual** — frame-sample at ≈1 FPS for parent gestalts (so a 3-minute clip becomes ≈180 frames; if that exceeds the tested 60-frame ceiling, sample sparser or process in segments — decision at coding). Slippery Point 7.
- **Video audio** — same as audio: 2× varispeed for parent gestalts.
- **Video Workers** — 3-second clip, 2 FPS (≈6 frames) passed to qwen3-vl. Plus a matched 3-second audio slice passed to whisper. Clips, not frames.

---

## 10. Transport principle

All tier-to-tier communication goes through the KillerBee HTTP API. Identical for all three media types:

- **Beekeeper** uploads the original file + text question via the KillerBee web form (one form, file-attach button + media_type selector).
- **RajaBee** polls, GETs the media_url from KillerBee, downloads the original, runs her gestalt on her tier's compressed/resized view, cuts into 8 children, POSTs each child piece to KillerBee, waits.
- **Each non-leaf tier** polls for available components at its level, claims one, downloads its piece, runs its gestalt, cuts into 8 sub-pieces, POSTs each, waits.
- **Each Worker** claims a leaf component, downloads its unit (tile/slice/clip), runs its perception model, POSTs the text result back.
- **Text reports flow up the same API.** Each parent polls for its children's results, integrates with its gestalt via its text model, POSTs its paragraph up.

No shared filesystem shortcuts. Even on a single host, every piece crosses HTTP.

---

## 11. Folder structure on KillerBee server

Self-describing at every level. Path tells the complete lineage; no DB lookup needed.

```
KillerBee/uploads/
  photo/
    swarmjob_<id>/
      original.jpg
      cut_by_raja/
        grid_a_q1.jpg ... grid_b_q4.jpg
        cut_by_gq_grid_a_q1/
          grid_a_q1.jpg ... grid_b_q4.jpg
          cut_by_dq_grid_a_q1/
            grid_a_q1.jpg ... grid_b_q4.jpg     (Worker tiles, leaves)
  audio/
    swarmjob_<id>/
      original.mp3
      cut_by_raja/
        grid_a_sec_1.mp3                        (1st temporal Grid A section)
        grid_a_sec_2.mp3 ... grid_b_sec_4.mp3
        cut_by_gq_grid_a_sec_1/
          grid_a_sec_1.mp3 ...
          cut_by_dq_grid_a_sec_1/
            grid_a_sec_1.mp3 ...                (Worker slices, leaves)
  video/
    swarmjob_<id>/
      original.mp4
      original_audio.mp3                        (ffmpeg-extracted audio track)
      cut_by_raja/
        grid_a_sec_1.mp4                        (visual 1st temporal Grid A)
        grid_a_sec_1_audio.mp3                  (matching audio slice)
        ... grid_b_sec_4.mp4 + .mp3
        cut_by_gq_grid_a_sec_1/
          grid_a_sec_1.mp4 + .mp3
          cut_by_dq_grid_a_sec_1/
            grid_a_clip_1.mp4                   (Worker video clip)
            grid_a_clip_1_audio.mp3             (matching audio slice)
```

`JobComponent.piece_path` stores the server-relative path of the component's primary piece. For video, a sibling column `audio_piece_path` stores the matching audio slice. See Section 13a.

---

## 12. Cut piece lifecycle

On `POST /api/job/<id>/complete`:
1. Mark SwarmJob `status='completed'`, set `completed_at`.
2. Delete `uploads/<media_type>/swarmjob_<id>/` recursively.
3. Keep JobComponent rows (retain `piece_path` as historical; files are gone).

No automatic cleanup of abandoned jobs — separate operational concern, out of scope.

---

## 13. KillerBee server changes

### 13a. Database migration

KillerBee has no Alembic / Flask-Migrate setup (verified 2026-04-19). Use a one-off Python migration script in `KillerBee/scripts/migrate_multimedia.py` that connects to `instance/killerbee.db` via SQLite and runs raw `ALTER TABLE ... ADD COLUMN` statements. SQLite supports adding nullable columns cleanly. The script should be idempotent — check `PRAGMA table_info(...)` before adding, so re-running is safe.

`swarm_jobs` — add:
- `media_type` (String(16), nullable) — `'text'` | `'photo'` | `'audio'` | `'video'`.
- `media_url` (String(512), nullable) — server-relative path to the original file.

`job_components` — add:
- `piece_path` (String(512), nullable) — server-relative path to this component's piece (video: visual file).
- `audio_piece_path` (String(512), nullable) — for video components: server-relative path to this component's extracted audio slice. Null for photo/audio/text.

### 13b. `models.py`

Add the three columns.

### 13c. `forms.py`

Extend `SubmitJobForm`:
- `media_type` SelectField: `[('text', 'Text only'), ('photo', 'Photo'), ('audio', 'Audio'), ('video', 'Video')]`.
- `media_file` FileField, optional. Required when `media_type != 'text'`.

### 13d. `app.py` — routes

- Extend submit-job POST to save uploaded file to `uploads/<media_type>/swarmjob_<new_id>/original.<ext>`, set `media_url`. For video, also `ffmpeg -i original.mp4 original_audio.mp3` to extract audio track.
- `GET /uploads/<path:filepath>` — serve files (use `safe_join`, no autoindex).
- `POST /api/component/<id>/upload-piece` — multipart upload of piece bytes + server-relative path. Writes to disk, updates component. For video, accepts both a video piece and an audio piece in the same request (or two calls — decide at coding).
- `POST /api/job/<id>/complete` hook — add cleanup of `uploads/<media_type>/swarmjob_<id>/`.

### 13e. Templates

Submit form template: add media_type dropdown + file attachment button. One-form design.

### 13f. Security

`safe_join` on all `uploads/<path>` serves. No autoindex. Localhost v1 skips auth; noted as hardening item.

---

## 14. GiantHoneyBee client changes

### 14a. `killerbee_client.py` — new HTTP methods

- `get_job_media(job_id) -> {media_type, media_url, audio_url?}`.
- `download_piece(url) -> bytes`.
- `upload_piece(component_id, piece_path, bytes, audio_bytes=None, audio_path=None)`.
- `get_children_results(parent_component_id) -> list[str]`.

### 14b. Tier clients — branching by media_type

Every non-leaf tier client (`raja_bee.py`, `giant_queen_client.py`, `dwarf_queen_client.py`) detects `media_type` on its input component or job and dispatches to:
- `process_photo_piece(...)` — branch in new helper `photo_tier.py`.
- `process_audio_piece(...)` — branch in new helper `audio_tier.py`.
- `process_video_piece(...)` — branch in new helper `video_tier.py` (internally calls both audio and visual helpers).
- `process_text_piece(...)` — existing Phase 3 code, unchanged.

Worker client (`worker_client.py`) has matching leaf branches: `process_photo_tile`, `process_audio_slice`, `process_video_clip`.

### 14c. `photo_tier.py`

```python
def process_photo_piece(tier, component_id, piece_url, vision_model, text_model, resize_spec, cut_folder_prefix):
    piece_image = PIL.Image.open(io.BytesIO(client.download_piece(piece_url)))

    gestalt = run_ollama_vision(vision_model,
        resize_to_spec(piece_image, resize_spec),
        prompt="/no_think describe what you see")

    if tier == "worker":
        client.submit_component_result(component_id, gestalt)
        return

    children = cut_grid_ab_spatial(piece_image)         # [(name, PIL.Image) × 8]
    for child_name, child_image in children:
        child_bytes = pil_to_jpeg_bytes(child_image)
        child_component_id = client.create_child_component(component_id,
            piece_path=f"{cut_folder_prefix}/{child_name}.jpg")
        client.upload_piece(child_component_id,
            piece_path=f"{cut_folder_prefix}/{child_name}.jpg",
            bytes=child_bytes)

    children_results = client.wait_for_children_results(component_id, n=8)
    paragraph = run_ollama_text(text_model,
        prompt=build_photo_integration_prompt(gestalt, children_results))
    client.submit_component_result(component_id, paragraph)
```

### 14d. `audio_tier.py`

Same shape as photo tier. Differences:
- Perception model is whisper (per tier's whisper size).
- Gestalt operates on a 2× varispeed version of the audio piece (use ffmpeg subprocess).
- Cut function is `cut_grid_ab_temporal(audio_bytes, duration)` — Grid A: 4 non-overlapping time sections; Grid B: 4 offset sections. Exact section length depends on parent's piece duration.
- If a piece is shorter than the whisper receptive-field floor (~5s), the tier passes through intact (no cut). See Section 5 input-length adaptation.

### 14e. `video_tier.py`

Combines audio and visual work per tier:

```python
def process_video_piece(tier, component_id, piece_url, audio_url, vision_model, whisper_size, text_model, ...):
    video_bytes = client.download_piece(piece_url)
    audio_bytes = client.download_piece(audio_url)

    visual_gestalt = run_video_visual_gestalt(video_bytes, vision_model, ...)
    audio_gestalt = run_audio_gestalt(audio_bytes, whisper_size, ...)

    if tier == "worker":
        worker_text = integrate_worker_video(visual_gestalt, audio_gestalt)
        client.submit_component_result(component_id, worker_text)
        return

    visual_children, audio_children = cut_video_grid_ab_temporal(video_bytes, audio_bytes)
    for (vis_name, vis_bytes), (aud_name, aud_bytes) in zip(visual_children, audio_children):
        child_component_id = client.create_child_component(...)
        client.upload_piece(child_component_id,
            piece_path=f"{cut_folder_prefix}/{vis_name}.mp4", bytes=vis_bytes,
            audio_path=f"{cut_folder_prefix}/{vis_name}_audio.mp3", audio_bytes=aud_bytes)

    children_results = client.wait_for_children_results(component_id, n=8)
    paragraph = run_ollama_text(text_model,
        prompt=build_video_integration_prompt(visual_gestalt, audio_gestalt, children_results))
    client.submit_component_result(component_id, paragraph)
```

### 14f. Shared cut helpers (new files in GiantHoneyBee)

- `photo_cut.py` — Grid A + Grid B spatial. Port from `HoneycombOfAI/queen_multimedia.py`.
- `audio_cut.py` — Grid A + Grid B temporal. Port.
- `video_cut.py` — Grid A + Grid B temporal for video + matching audio slice. Port.
- `varispeed.py` — ffmpeg wrapper for 2× time compression. Port.
- `frame_sample.py` — ffmpeg wrapper for low-FPS frame sampling. Port.

---

## 15. End-to-end tests

One test per modality. Run in implementation order.

### 15a. Photo

- Input: `/home/nir/Pictures/65291268.JPG` (classical painting).
- Question: "What is shown in this photo?"
- Expected: final Royal Honey describing the painting, built by integrating 512 Worker tile descriptions up through 64 DwarfQueens, 8 GiantQueens, and Raja, with each tier contributing its own gestalt observation.

### 15b. Audio

- Input: the same 3-minute Prince-of-Persia audio clip from yesterday's 1-level-hive validation (confirm location in `~/HoneycombOfAI/` at coding time).
- Question: "Describe what happens in this recording."
- Expected: Royal Honey covering start / middle / end of the clip. Acceptance: coverage parity with yesterday's 1-level Royal Honey (2183 chars, three-act coverage).

### 15c. Video

- Input: yesterday's 30-second Big Buck Bunny clip (confirm location at coding time).
- Question: "Describe what happens in this video."
- Expected: Royal Honey describing motion, character actions, and dialogue/soundtrack. Reference: yesterday's 1-level Royal Honey reached 9892 chars with motion-perceiving language ("walks steadily toward us", "picks up apple"). Multi-tier should match or exceed.

---

## 16. Success criteria

Plan is complete when all of the following are green:

### 16a. Infrastructure
1. `ollama list` shows `qwen3.5:9b`, `gemma3:4b`, `qwen3:14b`, `qwen3:8b`, `qwen3-vl:8b`, `qwen3.5:0.8b`, `phi4-mini:3.8b`.
2. `which whisper` shows `~/.local/bin/whisper`; `ffmpeg -version` succeeds.
3. KillerBee DB migration ran (new columns present in both tables).
4. KillerBee submit form accepts all 4 media_type values and stores uploaded files under `uploads/<type>/swarmjob_<id>/original.<ext>`.
5. `GET /uploads/<path>` serves files; directory traversal blocked.

### 16b. Photo
6. Photo Royal Honey produced end-to-end for `65291268.JPG`.
7. Every level of the tree logged a vision-model call on its downsampled region.
8. Every non-leaf level logged a text-integrator call.
9. `uploads/photo/swarmjob_<id>/` deleted after `complete_job`.

### 16c. Audio
10. Audio Royal Honey produced end-to-end for the 3-min Prince-of-Persia clip.
11. Every non-leaf level logged a whisper gestalt call on a 2×-varispeed version of its time region.
12. Coverage at least equal to yesterday's 1-level Royal Honey (start / middle / end all present).

### 16d. Video
13. Video Royal Honey produced end-to-end for the 30-sec Big Buck Bunny clip.
14. Every non-leaf level logged BOTH a visual gestalt (qwen3-vl on frames) AND an audio gestalt (whisper on time-compressed track).
15. Workers received video CLIPS (≥2 frames), not single frames — verified by a log line that records frame count per clip processed.
16. Motion-perceiving language present in the final Royal Honey.

---

## 17. Root-cause discipline

When something fails during implementation or testing:
- Solve from the root. No stubs, no orphan-marking as a way to finish, no retry wrappers over a real bug.
- Do not pre-build infrastructure for theoretical failure modes.
- Ask Nir when a design question opens that this plan did not answer. Short question cheap; long wrong implementation expensive.
- A fix discovered in photo applies to audio and video. Don't re-discover it three times.

---

## 18. Files that will change

### KillerBee
- `models.py`, `forms.py`, `app.py`, submit-form template.
- New Alembic migration file.
- New `uploads/` directory (gitignored).
- `.gitignore` update.

### GiantHoneyBee
- `killerbee_client.py` — new HTTP methods.
- `raja_bee.py`, `giant_queen_client.py`, `dwarf_queen_client.py`, `worker_client.py` — modality branches.
- New: `photo_tier.py`, `audio_tier.py`, `video_tier.py` — per-modality shared helpers.
- New: `photo_cut.py`, `audio_cut.py`, `video_cut.py`, `varispeed.py`, `frame_sample.py` — utilities ported from `HoneycombOfAI`.

### Launch
- A process supervisor (shell script or Python) to start all 585 processes with correct tier role + model pointers. Separate concern; can be minimal for v1.

---

## 19. Known decisions deferred

Not made in this planning session; listed so the implementer does not re-open them without reason:

- **Exact per-tier image resize dimensions** — per model, at coding time.
- **Exact min-duration threshold for tier pass-through** on short audio/video pieces — pick at coding time based on whisper's receptive-field floor.
- **Worker concurrency** on one GPU — Ollama serves. Revisit if bottleneck.
- **Authentication on `/uploads/` and upload-piece API** — reuse existing Flask session auth for web form, existing tier-client token for API. Production hardening is a separate plan.
- **Audio + video audio-track coupling detail** — whether one POST carries both video + audio or two POSTs; decide at coding.
- **Video visual gestalt when frame count exceeds the 60-frame tested ceiling** — segment and integrate or sample sparser; decide at coding.

---

## 20. Relationship to existing work

- **HoneycombOfAI multimedia (yesterday, 2026-04-18):** the 1-level hive already does photo / audio / video end-to-end. This plan ports all the pieces upward into the multi-level tree. Key files to reference:
  - `HoneycombOfAI/queen_multimedia.py` — canonical cut functions, varispeed helper, frame-sample helper.
  - `HoneycombOfAI/multimedia_handler.py` — Worker-side dispatch.
  - `HoneycombOfAI/MULTIMEDIA_GESTALT_PLAN.md` — yesterday's plan doc.
- **`PHASE3_LAPTOP_ROSTER_LOCKED.md`** — source of per-tier vision and whisper model choices.
- **`PHASE3_VISION_SWAP_GIANTQUEEN.md`** — documents `qwen3-vl:8b` at GQ and RAM measurement.
- **`reference_empirical_model_limits.md` (claude-memory)** — whisper 2× varispeed ceiling, qwen3-vl 60-frame multi-frame support, /no_think handling.
- **The Distributed AI Revolution Chapters 12, 13, 14, 15** — theoretical backbone. Especially Chapter 15's seven slippery points — reread before coding.

---

## 21. Hand-off

Opus 4.7 planned. Sonnet 4.6 is the intended implementer (`feedback_workflow.md`: Opus plans, Sonnet codes).

Sonnet should:
1. Read this plan top to bottom.
2. Reread Chapter 15 of `TheDistributedAIRevolution` before touching code.
3. For each of the three modalities, in order (photo → audio → video):
   - Implement the modality branch following Sections 13–14.
   - Run the end-to-end test from Section 15.
   - When all the modality's success criteria (Section 16) are green, move to the next.
4. If a run fails, diagnose from the root (Section 17), fix, re-run. Do not stub. Do not skip. Do not silently simplify.
5. Ask Nir whenever hitting a decision the plan deferred (Section 19).

All 16 success criteria green → plan is done.
