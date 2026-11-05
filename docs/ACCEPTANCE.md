# Acceptance and submission readiness

Current patch: 0.6.0. [Final CI evidence](evidence/release-0.6-ci.json): 169 tests passed, one skipped; actual offline Terraform validation passed for all four public fixtures. The graph preview uses escaped SVG after a browser rendering error was found and fixed. Evidence is separated by run; historical results do not automatically validate new targets.

| Gate | Evidence and limit |
|---|---|
| Live Meta | November 4 hosted run: actual image request on a synthetic complex CCM diagram; 14 components and 12 connections. |
| Human review | Same run recorded one source-backed clarification, evidence review, explicit database selection and scope/question acknowledgments. |
| Approval safety | Automated checks cover revision binding and tampering. Live UI walkthrough checked pending target edits disable generation and reset clears access. |
| Scope honesty | All 14 components accounted for. The approved target is an illustrative AWS baseline, not complete diagram conversion. |
| Terraform | Historical live validated ZIP passes actual offline checks. Current CI separately validates four public fixtures. The latest captured live target remains unvalidated; its request stays private. Consult the linked run/report for current status. |
| Hosting | Render Free supports review, approval and download; its own report remains not_run. External validation does not overwrite it. |
| Recording | 28 screenshots and a 115-second captioned slideshow prepared privately. Continuous narrated final video/public video URL still pending. |
| Submission | Copy prepared in SUBMISSION.md. Portal fields, final links and actual submission require completion in the contest account. |

See [live evidence](evidence/live-complex/README.md), [historical validated sample](evidence/README.md), [validation workflow](TARGET_VALIDATION.md), [recording guide](DEMO.md) and [submission copy](SUBMISSION.md).

## Historical verification

Release 0.3 CI recorded 96 passing tests and one root-specific skip, plus actual offline Docker validation of four fixtures: [run](https://github.com/sathishkannan-labs/Architecture-Diagram-Reviewer/actions/runs/41830185530). Those counts describe that release only. Older fixture videos and reports retain their original status.

No plan/apply or AWS provisioning is performed. Validation checks configuration validity only. Application deployment, IAM integration, production TLS and operational controls remain out of scope.
