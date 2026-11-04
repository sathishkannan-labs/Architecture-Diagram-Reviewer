# CodeRabbit review resolution

Review: https://github.com/sathishkannan-labs/Architecture-Diagram-Reviewer/pull/1

The review-only snapshot exposed the full current codebase to CodeRabbit. It reported 14 actionable issues (three major, eleven minor) plus two small cleanup suggestions. This document records the verified fixes; it does not claim that CodeRabbit independently approved the fixes.

| Review area | Resolution |
| --- | --- |
| Release revision mismatch | Releases require HEAD to match main; archive and restored/published main use the same revision. A changed main ref during bundling aborts the build. |
| Unpublished branch history | Bundle only refs/heads/main. A real Git regression verifies a private draft commit is absent from the restored release. |
| Windows launcher | Scope execution-policy handling to the child PowerShell process; retain argument forwarding. Native Windows execution still requires verification on Windows and organization Group Policy remains authoritative. |
| Workflow action integrity (two issues) | Pin the reviewed checkout/setup-python/upload-artifact commits and disable checkout credential persistence. |
| Local settings read failures | Ignore unreadable/non-UTF-8 local files; preserve existing environment values. |
| Failed demo-code guesses | Count invalid attempts against the shared process-wide budget. The UI code-entry callback uses the same gate, including after budget exhaustion. Document high-entropy codes. |
| Image error messages | Preserve explicit ExtractionError messages before the broad image-error handler. |
| Meta transport/response failures | Map remaining RequestError subclasses and malformed choice objects to sanitized ExtractionError messages. |
| AWS target name constraints | Reject consecutive/trailing hyphens, preserving lowercase-start and 3–20 character constraints. |
| Unicode DOT labels | Retain UTF-8 while escaping DOT quotes, backslashes and line breaks. |
| Build-time provider installation | Add a finite 1,800-second timeout to each networked Terraform build command. Runtime validation keeps its separate 180-second budget. |
| Session reset | Clear the password widget, authorization result and status along with the workflow, using a pre-rerun callback. |
| Test environment leakage | Use monkeypatch.setenv so the test-loaded key is restored/removed on teardown. |
| Shared evidence rules (cleanup) | Reuse coverage.grounded and grounded_edge in the rule reviewer. |
| Mirror traversal assertion (cleanup) | Assert the actual provider-relative escape target remains absent. |

New regression checks cover throttling, UI reset/exhaustion, transport failures, image messages, target names, Unicode, local-file read failures and bundle/publisher consistency. Existing graph, approval, resource mapping and validation checks remain in the suite.

CodeRabbit's generic docstring-coverage warning is a maintainability metric, not a failed application test. A project-wide docstring rewrite is deferred; this patch targets the actionable defects and the two small cleanup suggestions.

No CodeRabbit autofix controls were activated. Fixes were verified and implemented in the main codebase; the snapshot PR is for review evidence and is closed rather than merged into main.
