# Acceptance gates and evidence

All dates below are 2026. Deadline: **November 5, 02:00 UTC / 07:30 IST**.

| Gate | Required evidence | Current result |
|---|---|---|
| M1: real text + image | Successful Meta responses and a graph manually checked against a real diagram | BLOCKED: no MODEL_API_KEY; docs checked, adapter mocked-tested |
| M2: correction/review/approval | Correction history, six rules, valid references, approval revision | Automated tests and actual fixture UI walkthrough pass; live-input path pending M1 |
| M3: clean offline Docker | Actual fmt/check/init/validate using mirror, no credentials, non-root, IP egress denied | NOT VERIFIED: Docker unavailable; host maps only UID 0, so validator fails closed |
| M4: repository + complete live video | Reachable GitHub repository, live extraction through actual validation | NOT COMPLETE: no destination repository, live acceptance and Docker gates pending |

## What was actually exercised

- Installed the exact direct dependencies from pyproject.toml and built the editable Python package.
- Tests cover three synthetic diagram graphs, six mandatory rule IDs, inferred/unknown facts, invalid IDs/edges/boundaries, extraction errors and bounded retries, correction provenance/history, stale approval rejection, target changes, resource mapping, expiry, ZIP status and the optional API flow.
- Process supervision tests launch real children to exercise nonzero exit, timeout and output overflow. In this UID-0-only host they use an explicitly test-only Popen adapter so supervision can be tested independently of identity restrictions. These are **not** evidence that production security preflight passed.
- Root preflight rejection is tested. Four native subprocess checks are skipped here because changing to a non-root UID is unsupported by the host mapping. They run without that skip on a normal non-root Linux executor.
- Terraform 1.9.8 downloaded and verified against its HTTPS SHA256SUMS. AWS 5.100.0 installed using Terraform's signed-provider verification; a genuine provider lock file and filesystem mirror were produced during dependency preparation. This preparation does **not** establish runtime validation success.
- Streamlit AppTest exercised loading, review, approval, generation and `not_run` download. Browser automation exercises a human label correction and downloads the generated ZIP from the real Streamlit UI.
- `docs/evidence/host-validation-report.json` records `not_run` when the complete toolchain is present but the host cannot execute non-root processes. `fixture-artifacts.zip` contains a fixture-mode result with its own honest validation status. Missing binaries in a Python-only UI also produce `not_run`.

## Finish on the user's Linux/Docker machine

1. Set MODEL_API_KEY, verify account access to the configured model, and run `scripts/live_acceptance.py` on each of the three example PNGs. Manually compare nodes, arrows, evidence and unresolved facts. Also test a real architecture image of your own.
2. Build the image. The build must pass `scripts/offline_smoke.py` as UID 10001 using the same restricted runtime validator. Repeat with `docker run --network=none` and the CPU/memory/process limits documented in README.
3. Run the full UI path with a real extraction, make a meaningful correction, inspect the risk evidence, approve the displayed target revision, generate and verify the validation status is `passed`. Inspect stage output: success must include both initialization and `validate`, not just formatting.
4. Inspect `traceability.json`, `ADR.md`, `corrections.json`, approved target and lock file from the downloaded ZIP. Verify every resource reference is present, and change the graph to confirm approval/artifacts disappear.
5. Run Python tests on normal non-root Linux. Native network/identity checks should run, not skip because of this host's UID mapping.
6. Publish the local history to a user-selected empty GitHub repository, let CI complete, and record the full live workflow using docs/DEMO.md. Do not use the fixture video as final acceptance.

## Deadline gates

| Gate | UTC | IST |
|---|---|---|
| First full local workflow | Nov 4, 12:00 | Nov 4, 17:30 |
| Freeze features; drop incomplete P1 | Nov 4, 18:00 | Nov 4, 23:30 |
| Repository, video, submission materials complete | Nov 5, 00:00 | Nov 5, 05:30 |
| Submission deadline | Nov 5, 02:00 | Nov 5, 07:30 |

No Kubernetes, AWS provisioning, arbitrary target patterns, persistent accounts or durable queue are implemented. Render, missing-load-balancer/backup review rules and advanced accounting are deferred. The generated DB has seven-day retention as part of the fixed baseline; this does not imply a backup review rule or restore testing has been completed.

## Release 0.2 additions

The release fixes Docker cleanup, oversized runtime provider extraction and Windows import failures; adds launchers/readiness/publishing/integrity utilities; and adds integration tests for pending UI edits and inferred/low-confidence controls. The current pytest result is 65 passed / 4 skipped. Windows fallback is tested here, but native Windows PowerShell execution is unverified. The provider mirror unpacker is tested with isolated archives; clean Docker runtime validation remains an external gate. See DEMO_QUICKSTART.md for the direct local handoff.
