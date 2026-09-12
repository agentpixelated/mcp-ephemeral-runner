# Wisdom — Large Media Relay and Agentic Video QA

Date distilled: 2026-09-12

## 1. Solve the correct layer
Authentication, transport, compute, and storage are different problems. OAuth success only proves authentication. A credential on one machine does not give another sandbox network egress, disk, or provider reachability.

## 2. Name the bottleneck precisely
A file rejected by a connector is not evidence that the backing storage provider cannot hold that file. Measure the failing boundary first. In the C:U workflow, the practical ceiling belonged to the connected-file/materialization path, while Google Drive itself held the multi-gigabyte source normally.

## 3. Control plane and data plane should be separable
A persistent host may be useful for authentication or metadata without being a sensible place to carry large media. Keep slow or user-owned machines out of the byte path when a disposable cloud runner can do the transfer faster and more safely.

## 4. Prove one bounded path before scaling
Before creating dozens of chunks or changing infrastructure, send one small/ranged sample end-to-end and compare exact byte count and checksum. A successful proof converts an architectural guess into evidence.

## 5. Move compute to where the data already lands
Once an ephemeral GitHub runner can fetch the full source quickly, editing on that runner is better than forwarding every source byte again into a constrained sandbox. Bring back compact review evidence, project state, and the final deliverable instead of the whole raw source when possible.

## 6. Use transient storage as a conveyor belt, not a warehouse
Provider quotas are easier to respect when only the current artifact exists. Delete the previous relay artifact before producing the next. Peak storage matters more than cumulative bytes transferred.

## 7. Temporary public exposure must be scoped and reversible
When authenticated server-to-server transfer is unavailable, expose a server-side temporary copy only after explicit approval. Keep the original private. Revoke access and delete the temporary copy after the verified final is durable.

## 8. Integrity belongs at every trust boundary
Record source size and origin checksum before processing. For ranged transfers record offsets and per-part hashes. Before editing, the compute-side source must match the origin. Transport success without integrity evidence is just optimism wearing a progress bar.

## 9. Technical success is not editorial success
A render that encodes and decodes correctly can still be repetitive, poorly paced, or have jarring audio. The GT7 re-audit showed that a coarse contact sheet missed real editorial defects. For multi-clip gameplay, inspect every candidate, every selected output clip, every adjacent boundary, then the complete final sequence after the latest revision.

## 10. Navigation evidence is not approval evidence
Sparse global samples are useful for finding candidate regions. They cannot justify a final handoff. Candidate windows need denser normal-speed or frame-by-frame review around setup, action, payoff, and exit.

## 11. Cloud boundaries should not weaken the workflow
Changing execution from a local sandbox to GitHub Actions changes only the compute location. It does not remove the candidate ledger, source-integrity checks, clip-by-clip QA, boundary QA, black/freeze checks, audio continuity checks, or final full decode.

## 12. Cleanup is a completion criterion
Temporary public permissions, source copies, relay artifacts, public workflow links, and disposable review data are liabilities after the task. A workflow is not finished until the durable deliverable is verified and temporary access paths are retired.

## Provenance
Distilled from two verified 2026-09-12 workflows:
- C:U large-media ingestion: multi-gigabyte private source, connector limit discovery, ranged proof, temporary-copy bridge, GitHub Actions relay, and exact checksum validation.
- GT7 gameplay re-audit: demonstrated why sparse/global visual QA is insufficient for final editorial approval.

This file intentionally contains no OAuth tokens, credentials, cookies, private URLs, or reusable secrets.
