# Validate the approved target

Render Free hosts the interactive review and generation UI. Actual Terraform
execution stays outside that public service. The project now has a separate
**Validate approved target** GitHub Actions workflow that runs the same restricted
Docker validator against your approved graph and target.

## From the app

1. Review, acknowledge scope/questions, approve and generate artifacts.
2. Download `validation-request.json` using **Download validation request**. It is
   also included in the artifact ZIP when it fits the 50,000-byte demo limit.
3. Open **Open Terraform validation workflow**, select **Run workflow**, keep
   branch **main**, and paste the request file's JSON into `request_json`.
4. Run the workflow. Repository write access is required. A blank field runs
   only the synthetic complex fixture; it does not validate your current target.
5. Open the completed run and download its **approved-target-validation** artifact.
   Unzip it, then inspect `validated-artifacts.zip`.
6. Check `validation-report.json` for actual results and `validation-context.json`
   for matching graph/target revisions, request hash and Terraform file hashes.

The request contains architecture labels, evidence, original/corrected graphs
and correction history. Review it before sharing it with GitHub. The application
does not send it automatically and stores no GitHub token. Do not submit secret
data or private architecture information to a workflow unless you intend to
share it with that repository and its workflow infrastructure. Workflow artifacts
are retained for seven days; normal GitHub workflow permissions and quotas apply.

The Render download still reports `not_run` because Terraform did not run in
Render. The workflow creates a separate ZIP with `passed`, `failed`, `timed_out`
or `not_run` based on actual execution. The app does not import user-provided
pass claims or replace its own report with an unverified external report.

## What is enforced

- Requests accept graph/approval metadata only, never arbitrary Terraform or
  executable model output. Only version-controlled templates are rendered.
- Graph, target, scope, questions, acknowledgments and correction audit revisions
  must match. Template and provider-lock hashes must match the submitted request.
  If templates changed, generate a fresh request from the current app.
- Terraform runs as the image's non-root user, with no container network,
  capabilities dropped, a read-only root filesystem, 2 CPU/2 GB/128 process
  limits, bounded temporary storage and the existing subprocess restrictions.
- Provider installation uses the bundled mirror. Validation has a 180-second
  wall-clock limit and bounded output. No cloud credentials, plan or apply.
- JSON input is read as data from the GitHub event file. It is never interpolated
  into shell commands. The original audit is retained in the generated ZIP.

## Optional GitHub CLI

```bash
gh workflow run validate-target.yml --repo sathishkannan-labs/Architecture-Diagram-Reviewer --ref main -F request_json=@validation-request.json
```

The CLI uses your own existing GitHub authentication, not a token stored in Render.
You can also run `scripts/validate_request.py --request PATH --output PATH` inside
the locally built Docker image with the same restrictions. Requests over the
workflow demo limit should use the existing local full-workflow path instead.

Validation establishes configuration validity only. It does not prove security,
successful provisioning, application readiness or production suitability.
