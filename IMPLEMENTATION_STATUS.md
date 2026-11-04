# Release 0.3 implementation status — November 4, 2026

The public preview is hosted on Render Free. Source: https://github.com/sathishkannan-labs/Architecture-Diagram-Reviewer. Demo: https://adr.sathishkannan.com.

## Completed changes

- Every observed component has an included/replaced/omitted/unsupported target disposition. Independent services and multiple databases are explicitly unsupported by the fixed baseline; the app does not claim to consolidate or migrate them.
- Approval requires separate component-scope and unresolved-question acknowledgments. They are enforced by the service, local API and generator. Scope and questions are part of the target revision, so graph/target edits revoke approval and artifacts. Derived target metadata is recomputed before generation to reject tampering.
- All graph unknowns and unverified review questions remain visible through approval and appear in open-questions.json, ADR.md and the schema-v2 manifest.
- Control coverage is assessed per service using sufficiently grounded direct relationships or applicable authentication boundaries. A control box alone does not establish coverage. Relationships shown in diagrams do not prove effectiveness.
- Added backup coverage, queue resilience and object-storage policy questions. These report insufficient evidence as unverified, not as confirmed absent controls. Queue/storage identification currently uses supported `other` labels; full typed product configurations are not implemented.
- Added a saved-graph preview, component/connection/boundary/unknown counts, and corrected-graph.dot in the artifact ZIP. Public/private/unknown exposure is color coded; inferred arrows are dashed. Preview labels are escaped, not executable DOT input.
- Added the supplied complex live extraction as a synthetic replay fixture: 14 components, 12 connections, two boundaries and five diagram unknowns. The new review retains five confirmed findings and adds six unverified questions. Fixture mode does not make a fresh live API call.
- Downloads additionally contain component-scope.json and control-coverage.json. All 26 Terraform resources retain approved decision references.

## Verification

- Local: 93 tests passed; four native non-root subprocess tests skipped in this host. Release CI: 96 passed, one root-specific check skipped on the non-root runner. All native non-root/network/timeout/output checks passed there. New tests cover complex topology, scoped relationships, uncertain controls, explicit acknowledgments, metadata tampering, question retention, UI approval gates and correction invalidation.
- All four fixture workflows pass correction, review, acknowledgment, approval, generation, ZIP inspection and invalidation. The release Docker CI passed the image build plus actual fmt/fmt-check/offline init/validate for all four fixtures with network=none and resource restrictions. Runtime validation in this development host remains not_run. Reports: docs/evidence/release-0.3-offline-smoke.json and docs/evidence/release-0.3-fixture-verification.json. CI: https://github.com/sathishkannan-labs/Architecture-Diagram-Reviewer/actions/runs/41830185530
- Previous historical results and fixture video under docs/evidence belong to earlier releases. They are not a recording of the current UI or a completed live acceptance run.
- The user supplied successful live text/image runs; the complex exported graph matched the test reference exactly. These requests were not independently rerun from this development host.

## Remaining submission gates

- The clean Docker gate passed in release CI. A final user-facing live workflow/video with actual validation still needs recording in a Docker-capable environment. Docker is unavailable in this development host. Public Render execution remains deliberately disabled and reports not_run.
- Final live demo with a meaningful human clarification, scope/question acknowledgments, target approval and download. The supplied complex export had no recorded corrections.
- Native Windows launcher execution and final submission materials/video remain to be verified. Release CI passed at the linked run; this does not establish final video/submission completion.

No AWS plan/apply, arbitrary Terraform/model code execution, multi-service Terraform generation or data migration is implemented. Validation does not prove security, provisioning success, application readiness or production suitability.
