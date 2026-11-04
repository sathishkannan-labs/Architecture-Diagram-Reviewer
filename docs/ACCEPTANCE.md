# Acceptance gates and evidence

Deadline from the project baseline: November 5, 2026, 02:00 UTC / 07:30 IST.

| Gate | Evidence / current state |
|---|---|
| Live Meta text and image | User supplied successful text connectivity and image runs. Complex extraction matched 14 components and 12 edges. Not independently rerun from this host. |
| Correction/review/approval | Local automated and fixture integration checks pass. Final live video must demonstrate a meaningful correction and explicit scope/question acknowledgments. |
| Target scope | Every observed component is accounted for; unsupported roles and omissions are acknowledged. Fixed baseline is not a faithful multi-service conversion. |
| Actual offline validation | Release Docker CI passed build and actual fmt/check/offline init/validate for all four fixtures. Docker remains unavailable in this development host. Public Render execution is disabled; reports not_run. |
| Repository and hosting | GitHub source and Render Free preview exist. Release CI passed; the deployed code and browser workflow are verified separately. |
| Final submission | Live video with actual local validation and final submission materials remain outstanding. |

## Release 0.3 verification

Local: 93 tests pass, four native non-root checks skip in this host. Release CI: 96 pass, one root-specific check skips on the non-root runner. Docker smoke and all four fixtures pass actual offline validation. Four fixture integration workflows pass including correction, scope/question acknowledgments, approval, 26 resource references, status-bearing ZIP and invalidation. New regression tests preserve the exact complex topology, separate five confirmed issues from six unverified questions, and retain all five original diagram unknowns.

Component scope and open questions are part of the approved revision. Tampering with scope, questions or acknowledgment flags prevents generation. API approval requests must send `acknowledge_scope: true` and, when questions exist, `acknowledge_unknowns: true`; omitted flags fail closed.

## Finish the complete local acceptance

1. Build the Docker image and run scripts/offline_smoke.py plus scripts/verify_workflow.py --require-validation with the documented network/resource restrictions.
2. Run live image extraction locally, make a meaningful clarification, compare the saved graph, and rerun review.
3. Inspect component scope and all unresolved questions. Explicitly acknowledge both and approve the current revision.
4. Generate and inspect actual fmt, fmt-check, init and validate results. Verify report status is passed; not_run is not a validation pass.
5. Inspect component-scope.json, open-questions.json, control-coverage.json, traceability.json, ADR.md and correction audit in the ZIP. Edit the graph again to verify approval and downloads disappear.
6. Record the complete live workflow and finalize the repository/video/submission links. Historical fixture recordings do not satisfy live acceptance.

No plan/apply is run. The fixed target omits application deployment, IAM integration, production TLS and several operational controls. A shown control relationship does not prove effectiveness.

## Release CI evidence

https://github.com/sathishkannan-labs/Architecture-Diagram-Reviewer/actions/runs/41830185530

Structured reports are retained in docs/evidence/release-0.3-offline-smoke.json and release-0.3-fixture-verification.json. They record fixture mode and do not claim a new live Meta request.
