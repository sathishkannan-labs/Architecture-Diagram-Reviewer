# Demo recording guide

Lead with the complex diagram's exposed legacy database, then show evidence, human review and the approved remediation baseline. Suggested length: 3–5 minutes; confirm the actual portal's video requirements before uploading.

## Current hosted walkthrough

1. Open https://adr.sathishkannan.com/ and keep secrets off screen. Explain that Render Free may sleep and does not execute Terraform.
2. Select live extraction and demonstrate text connectivity, then upload `examples/complex-ccm.png`. A real image request is required; loading fixture JSON is a separate synthetic path.
3. Compare graph labels and edges with the image. Record a source-backed clarification only where warranted. Show original/corrected observations and provenance.
4. Run review. Contrast confirmed public-database exposure with unverified control questions. Missing diagram detail does not establish real-world absence.
5. Show the one-screen findings/remediation summary, component scope, database-role choice and open questions. Explain unsupported roles and the fixed ALB/ASG/RDS baseline.
6. Check every applicable acknowledgment and approve the displayed revision. Generate and download. Render's report honestly remains `not_run`.
7. Show the separate GitHub validation workflow and matching graph/target revisions. Use the actual saved request or identify a recorded sample explicitly. A blank manual request runs only a fixture.
8. Inspect actual fmt/check/init/validate output, traceability and ADR from that run. State that no plan/apply ran and successful validation does not establish a deployable application.

## Available recording material

The November 4 private demo pack contains 28 screenshots, narration guidance, captions and a 115-second silent slideshow of the real hosted run. It is assembled from stills, **not continuous screen recording**. It includes one manually entered source-backed clarification. Its original hosted download is `not_run`; later CI validation is a separate event. Add narration, upload the final video and check public playback before submission.

The checked-in `evidence/fixture-walkthrough.mp4` is an older development recording. Its old captions/counts reflect that release, not current functionality or live acceptance.

## Optional developer fixture recording

`scripts/record_fixture_demo.py` operates the local UI with Playwright and ffmpeg. Install Playwright 1.51.0, Chromium and ffmpeg separately. It expects an environment where validation is unavailable and explicitly labels fixture mode. It has not been re-recorded as part of the final patch; use the current hosted walkthrough for submission. Never force or relabel a recorded validation outcome.
