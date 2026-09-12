# Wisdom — Repo-Based Gameplay Editing on Ephemeral Cloud Compute

Date: 2026-09-12

## Durable lessons

1. **Move compute to the data after transport is proven.** Once a multi-gigabyte source can be fetched quickly and checksum-verified on GitHub Actions, repeatedly relaying the raw recording elsewhere only adds failure modes.

2. **Transport success and editorial success are different proofs.** A matching checksum proves the source is intact; it says nothing about whether the edit is good.

3. **Full-session navigation and candidate review are separate passes.** Sparse frames every 10–20 seconds are excellent for mapping a long recording but cannot approve a clip. Kept candidates need denser context around the actual incident.

4. **Use multimodal evidence to discover candidates.** Audio spikes are useful locators but produce false positives. Combine audio, motion, scene changes, OCR/UI signals, and visual interpretation.

5. **When direct image viewing fails, analyze the actual pixels rather than falling back to metadata.** A local/open-source captioning or vision model over extracted frames is a legitimate fallback evidence layer. State the limitation and do not pretend filenames or RMS values are visual review.

6. **Repo-native editing tools are preferable when the task explicitly requests a repo workflow.** Auto-Editor provides manual keep/cut ranges, preview, clip-sequence export, timelines, and targeted effects. PySceneDetect gives shot-boundary evidence. FFmpeg remains the deterministic execution/QA substrate. A design application is not a substitute for this stack.

7. **Judgment should lead automation.** For narrative gameplay highlights, first select events, then encode explicit ranges. Do not let silence/motion thresholds decide the story simply because they are easy to automate.

8. **An event is more than its loudest second.** Strong clips usually need trigger/setup, readable escalation, payoff, and only enough recovery to make the outcome clear. Over-tight cuts are as bad as dead air.

9. **Hard cuts are a safe default.** Transitions, zooms, speed changes, captions, replays, and SFX should each solve a concrete readability or emphasis problem. Decorative editing applied uniformly tends to lower information density.

10. **Export both sequence and atomic clips when reuse matters.** The highlight serves the viewing experience; individual clip files make later social edits, sharing, and reordering cheap.

11. **QA must be performed on the last render.** Inspect every output clip, each adjacent boundary, then the full sequence. Technical checks include full decode, black/freeze detection, audio presence, duration, codec, frame rate, and resolution.

12. **Cleanup is editorial infrastructure, not housekeeping.** Temporary public source copies and review publications exist only to make the job possible. Revoke/delete them after the final durable upload is verified.

## Failure patterns captured

- Misidentifying a connector/materialization ceiling as a Google Drive file-size limit.
- Keeping a slow personal/server relay in the data path after a faster disposable cloud runner was proven.
- Treating a global contact sheet as sufficient visual QA.
- Trying to solve an editing-viewer problem with a design tool when the user explicitly requested repository-based editing.
- Installing heavy ML dependencies in an order that can pull unnecessary GPU packages on a CPU runner; install CPU Torch explicitly before Transformers/Accelerate.
- Running one giant opaque workflow before a small proof; prove source transport, frame extraction, model inference, and render paths in bounded stages.

## Preferred architecture

`private origin -> reversible temporary access -> GitHub Actions source integrity gate -> full-session navigation -> candidate discovery -> actual-frame vision review -> dense candidate refinement -> Auto-Editor/PySceneDetect/FFmpeg edit -> clip QA -> boundary QA -> full-sequence technical QA -> durable final upload -> revoke/delete temporary exposure`

This wisdom complements, rather than replaces, the canonical gameplay editing and large-media relay skills.
