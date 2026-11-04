# Render Free public preview

This preview supports fixture or owner-authorized live extraction, correction,
review, approval, trusted Terraform generation, traceability and ZIP downloads.
Terraform execution is always disabled on Render. Reports honestly say `not_run`.
Use the approved-target GitHub workflow in [TARGET_VALIDATION.md](TARGET_VALIDATION.md),
or the existing local Docker workflow, for actual offline validation. The app
provides a request download and workflow link after approval/generation. External
results remain separate from the Render report.

## Service settings

- Type: Web Service; runtime: Python; plan: **Free**.
- Repository: https://github.com/sathishkannan-labs/Architecture-Diagram-Reviewer
- Branch: `main`; region: Singapore for the India demo audience.
- Build: `pip install .`
- Start: `python scripts/start_hosted.py`
- Environment: `PYTHON_VERSION=3.12.8`, `ARCHREVIEW_HOSTED=1`.
- Optional HTTP health check: `/_stcore/health`.
- No database, provider mirror, Terraform binary or persistent disk is needed.

Service settings and secrets are managed directly in Render, not by a Blueprint.
The local Dockerfile and Compose restrictions remain for local validation only.
Native Python avoids building or carrying the large AWS provider mirror.

Fixtures work immediately without credentials. To enable live Meta calls, set
`MODEL_API_KEY` and a strong private `DEMO_CODE` in the service's Environment page,
then save and deploy. Optionally set `META_MODEL` for your entitled Meta model.
Do not put these secrets in GitHub. Enter the demo code in the app sidebar and
share it only with the intended reviewers.

Live requests have one shared concurrency slot, at most 20 operations per rolling
hour and 100 operations per process lifetime. Each operation can retry up to three
HTTP attempts. These in-memory counters reset on service restart or redeploy;
they are demo controls, not durable billing limits. They are enforced in the Meta
client, including text probes, and missing codes fail closed. No API key or demo
code is supplied in the initial deployment, so live calls start disabled.

## Verification

Check deployment reaches `live`, `/_stcore/health` returns 200, and the UI opens.
Load a fixture, correct a label, review, approve, generate and download. Confirm
the component-scope and unresolved-question acknowledgments are required, and
that the download contains component-scope.json, open-questions.json and control-coverage.json. Confirm
the download contains a hosting-stage `not_run` validation report. Confirm live
buttons are disabled without both the configured key and correct demo code.

Render Free sleeps after 15 minutes of inactivity, with roughly a minute to wake.
Session state and generated downloads are temporary and can disappear on restart.
This public preview does not satisfy live Meta acceptance or actual Terraform
validation acceptance. Its deploy and memory usage must be verified on Render.
