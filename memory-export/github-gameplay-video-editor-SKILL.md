---
name: github-gameplay-video-editor
version: 1.0.0
purpose: Edit oversized gameplay recordings on disposable GitHub Actions compute using integrity-gated source access, full-session visual navigation, candidate-level vision review, Auto-Editor/PySceneDetect/FFmpeg execution, individual clip export, and strict visual/technical QA.
risk: medium
compute_model: github-actions-ephemeral
---

# GitHub Gameplay Video Editor

## Trigger
Use for long gameplay recordings that are already available to a GitHub Actions runner or are routed there by the large-media relay skill, especially when local/connector materialization is slow or size-limited.

Route source transport through `large-media-github-relay` first when needed. Route editorial judgment through the canonical gameplay editing rules as well.

## Tooling hierarchy
1. **Auto-Editor** (`WyattBlue/auto-editor`) for explicit manual keep/cut ranges, preview, rendered highlight, clip-sequence export, timeline export, and optional targeted actions.
2. **PySceneDetect** (`Breakthrough/PySceneDetect`) for scene/cut boundary evidence and candidate boundary refinement.
3. **FFmpeg/ffprobe** for deterministic frame extraction, audio analysis, decode QA, contact sheets, black/freeze detection, and final metadata verification.
4. **Open-source vision on actual extracted frames** (e.g. BLIP + OCR) when direct model vision cannot consume the review images. This is a fallback evidence layer, not permission to skip visual review when direct pixels are available.

Do not use a design application as the editing engine or primary visual-review path when the task is repo-based video editing.

## Workflow

### 1. Ground and verify source
- Record exact source file identity, byte size, duration, streams, resolution, frame rate, and checksum.
- Require source bytes at GitHub compute to match the origin checksum before editing.
- Keep the original source private and unchanged. If a temporary public server-side copy is required, it must be separately approved and later revoked/deleted.

### 2. Full-session navigation
- Inspect the entire recording at regular intervals (typically 10–20 s for a long gameplay source).
- Create timestamped navigation sheets covering the complete duration.
- Navigation frames are only a map. They cannot approve a clip.

### 3. Candidate discovery
Use several signals instead of a single threshold:
- audio RMS / spikes;
- silence gaps;
- motion / visual delta;
- scene-change density;
- optional game-specific UI/OCR events.

Keep candidates separated enough to avoid many copies of one incident. Candidate discovery proposes locations; it never decides the edit by itself.

### 4. Candidate visual review
For every candidate:
- extract a strip across a context window, normally 20–30 s;
- inspect setup, escalation/action, payoff/reaction, and recovery;
- inspect source audio importance separately;
- reject menus, loading, repeated camera states, dead traversal, unreadable action, accidental UI, or duplicate incidents unless they carry necessary context.

If direct vision access fails, run an open-source image-caption/OCR pass on the actual frames and combine it with motion/audio evidence. Record clearly that this is a fallback. Do not pretend metadata alone is visual review.

### 5. Dense refinement of kept candidates
For each kept event:
- sample more densely around the event;
- use PySceneDetect or scene-delta evidence near proposed boundaries;
- choose exact source in/out so the viewer understands the trigger and sees the payoff;
- preserve reaction/recovery only as long as it adds information.

Default event shape:
`setup -> readable action/escalation -> payoff -> minimal recovery`

### 6. Build the edit with Auto-Editor
Prefer explicit manual ranges after editorial selection:
- use `--edit 0` plus `--keep START,STOP` ranges for a judgment-led edit;
- run `--preview` before a long render when syntax or pacing is uncertain;
- use small margins only when they prevent clipped context;
- use `--export clip-sequence` for individual kept clips;
- optionally export a v3/Resolve/Kdenlive timeline for future manual editing.

Use hard cuts by default. Effects must have an editorial reason. Avoid blanket zooms, transitions, speed ramps, filters, or generated music merely to make the edit look 'edited'.

### 7. Render outputs
Produce, at minimum when requested:
- one cohesive highlight edit;
- individual clips for the strongest incidents;
- a machine-readable edit ledger containing clip ID, source in/out, output duration, event summary, and QA status.

Preserve original aspect ratio unless the user requests another platform format. Prefer a broadly compatible H.264/AAC delivery encode; keep a higher-quality project/timeline representation when practical.

### 8. Clip-by-clip QA
For every output clip inspect:
- first frames: does setup make sense immediately?
- middle: is action readable and free of dead time?
- last frames: is payoff/reaction complete?
- black/freeze/corrupt frames;
- accidental menus/loading/UI;
- audio presence, clipping, pops, or abrupt truncation;
- uniqueness versus other clips.

Verdict must be `PASS` or `REVISE`, never implied.

### 9. Boundary QA
For every adjacent pair in the highlight:
- no repeated frame/shot;
- no incomprehensible chronology jump unless intentionally montage-like;
- no accidental audio pop/drop;
- cut lands on intended action or recovery point;
- transition, if any, has a specific reason.

### 10. Full-sequence QA
After the last revision:
- inspect the complete sequence again, not an earlier draft;
- verify the opening earns attention quickly;
- ensure later clips still add new information rather than repeating the same combat state;
- run `ffmpeg -v error -i FINAL -f null -` or equivalent decode check;
- run black/freeze checks;
- verify duration, resolution, fps, codec, audio streams, and output file size;
- generate final review strips/contact sheets for independent visual evidence.

Only after all gates pass is the file eligible for durable upload/handoff.

## GitHub Actions rules
- Runner disk and artifacts are disposable.
- Keep large source bytes on runner only for the active job.
- Return review evidence and finished deliverables, not redundant copies of the source.
- If artifact quota is tight, use bounded rolling artifacts or GitHub Releases for verified final outputs.
- Never persist OAuth refresh tokens, rclone configs, cookies, or API keys in commits/artifacts/logs.

## Completion criteria
A task is complete only when:
- source checksum matches origin;
- full-session navigation exists;
- every final candidate has actual visual evidence;
- exact keep ranges are recorded;
- highlight and requested individual clips render successfully;
- clip, boundary, full-sequence, and technical QA pass;
- final deliverables are persisted to the requested durable destination;
- temporary public access/copies are revoked and deleted after the final is verified.

## Failure boundaries
- Audio peaks alone are not highlights.
- A contact sheet alone is not clip-by-clip review.
- A successful render is not editorial QA.
- Do not use a design app as a substitute for the requested editing repository/toolchain.
- Do not upload a rough draft as final.
- Do not leave temporary public source copies active after completion.
