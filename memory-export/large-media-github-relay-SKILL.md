---
name: large-media-github-relay
version: 1.0.0
purpose: Move oversized authorized media through GitHub Actions disposable compute when normal connected-file or materialization limits block access, with scoped temporary exposure, integrity checks, bounded artifacts, and cleanup.
risk: medium
compute_model: github-actions-ephemeral
---

# Large Media GitHub Relay Skill

## Trigger
Use when an authorized media source is too large for the normal ChatGPT connector/materialization path, but the task requires the actual bytes for analysis, editing, rendering, or other deterministic processing.

Do not use this skill merely because a file is large. First verify that the ordinary connected-file path actually fails or is materially impractical.

## Core model
Treat **authentication, transport, compute, and durable storage as separate layers**.

A successful OAuth login proves only authentication. It does not prove that the target compute has network egress, sufficient disk, or a usable byte path. Select the data plane only after measuring the actual blocker.

GitHub Actions is disposable transport/compute, not canonical storage.

## Procedure
1. **Ground the exact source.** Verify source identity, byte size, and an origin checksum when available. Keep the original non-destructive and private by default.
2. **Prove the real bottleneck.** Record the failing connector/tool limit or network condition. Do not mislabel a connector limit as a storage-provider file-size limit.
3. **Prefer a reversible access bridge.** If GitHub cannot authenticate directly and a public URL is required, create a server-side temporary copy rather than exposing the original. Get explicit user approval before public sharing. Expose only the temporary copy and only for the required transfer window.
4. **Run a small end-to-end proof first.** Fetch a bounded byte range, pass it through the proposed relay, and verify exact size plus SHA-256 (or another strong checksum) at both ends before scaling up.
5. **Choose where compute should happen.** If the GitHub runner can fetch the full source quickly and has enough disk/CPU for the task, process the source on the runner instead of relaying every source byte back into a weaker sandbox. Return only review evidence and final deliverables when possible.
6. **If chunk relay is required, bound storage.** Use HTTP Range reads or equivalent deterministic byte ranges. Keep each artifact below current provider/tool limits. Delete the previous artifact before producing the next when quota is tight. Treat the artifact store as a conveyor belt, not a warehouse.
7. **Preserve an integrity ledger.** For every part record byte start/end, expected byte count, actual byte count, and SHA-256. If reconstructing a full file, concatenate in exact byte order and require the reconstructed size and origin checksum to match before processing.
8. **Keep secrets out of the data plane.** Prefer GitHub's scoped token, temporary public-copy access, presigned URLs, or provider secret stores. Never commit OAuth refresh tokens, API keys, cookies, rclone configs, or service credentials to the repository, artifacts, logs, AgentMemory, AgentKnowledge, or skills.
9. **Verify processing outputs independently.** Relay success only proves byte transport. The downstream task must run its own domain-specific QA, such as media decode, visual review, or data validation.
10. **Persist the intended deliverable.** Move only the verified final/project state to the user's durable destination. Do not treat GitHub artifacts or runner disk as durable user storage.
11. **Cleanup is part of completion.** After the durable final is verified, revoke temporary public access, delete the temporary source copy, delete relay artifacts/workflows when no longer useful, and ensure the original source remains unchanged/private.

## Media-editing handoff
When this skill is invoked for video editing:
- after source integrity is proven, route to `/AgentSkills/agentic-video-editing/SKILL.md`;
- gameplay footage additionally routes to `/AgentSkills/gameplay-clip-editing/SKILL.md`;
- if compute remains on GitHub, preserve the same candidate-ledger, clip-by-clip, boundary, full-sequence, and technical QA gates. Moving compute does not weaken editorial verification.

## Completion criteria
The relay workflow is complete only when:
- the source identity/size is grounded;
- the real transport blocker is identified;
- the chosen GitHub path has been verified end-to-end;
- source integrity is verified at the compute boundary;
- any temporary exposure is revoked after downstream completion;
- relay artifacts are cleaned up or have a deliberately bounded retention;
- no secret was persisted in repository/artifact/skill state.

## Failure boundaries
- Never expose the original private source publicly when a temporary copy can serve the purpose.
- Never create public sharing without explicit user approval.
- Never infer that OAuth success means a sandbox can reach the provider.
- Never call a partial or size-only transfer valid without checksum verification when an origin checksum is available.
- Never accumulate multi-gigabyte artifacts when a bounded rolling relay can satisfy the task.
- Never use an excluded user-owned machine as the data plane merely because it is reachable.
- Never leave temporary public copies or relay links active after verified completion.

## Verified origin evidence
Promoted at the user's explicit request after the 2026-09-12 C:U large-media workflow:
- a 4,594,320,879-byte private Drive video exceeded the observed normal connector/materialization ceiling;
- a bounded ranged-transfer proof arrived byte-identically;
- GitHub Actions successfully fetched the source through a scoped temporary public copy while the original remained private;
- combined GitHub artifacts larger than the failing connector ceiling successfully reached ChatGPT;
- direct full-source download on GitHub matched the origin MD5 exactly and achieved materially higher throughput than the previously tested user-host relay;
- this demonstrated that the efficient solution was to move the compute to the cloud runner after integrity verification rather than continue shuttling the entire source through the constrained path.
