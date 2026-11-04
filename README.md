# Architecture Diagram Reviewer

**Architecture risk reviewer with an illustrative AWS remediation baseline.** It generates a fixed ALB/ASG/RDS target, not a complete diagram-to-cloud conversion. Independent services, queues, object storage and application integration remain outside its generated scope.

Local human-reviewed diagram → evidence-based risk review → approved two-AZ AWS target → traceable Terraform → offline validation → ZIP.

**Terraform validation does not prove security, provisioning success, application readiness, or production suitability. No AWS plan or apply is run.**

## Release 0.5 — final demo preparation

A finding-to-target summary distinguishes changes in the new baseline from unresolved or unsupported observed roles. Database-role selection is recorded in the approved target; changing it revokes approval, artifacts and validation requests. Selecting a role does not migrate data or modify existing resources. Other database roles stay unsupported.

[Validated complex sample and provenance notes](docs/evidence/README.md) · [Recording checklist](docs/RECORDING.md). Downloads now include `remediation-summary.json`.

## Release 0.4 — compact review and approved-target validation

Open questions are grouped into topics without dropping source entries or changing approval data. Detailed evidence, editing tables, scope rows and resource mappings are expandable, keeping the default page shorter.

After generation, download the validation request and open the **Validate approved target** workflow. It regenerates the same approved trusted templates, verifies revision/template hashes, runs actual restricted offline Terraform validation and publishes a separate report ZIP. See [TARGET_VALIDATION.md](docs/TARGET_VALIDATION.md). This is an owner-triggered external workflow; Terraform still does not run in Render Free, and the app does not automatically submit architecture data to GitHub.

## Release 0.3 — explicit scope and unresolved questions

Release 0.3.1 also replaces the static "live access unverified" label with separate text/image request results for the current session. Successful calls show verified, failures show the last request failed, and new sessions or host restarts reset to not tested. Key presence alone never counts as verification.

[Public demo](https://adr.sathishkannan.com) · [Deployment configuration](docs/RENDER_DEMO.md)

The saved graph preview shows component counts and directed connections. Review now checks service-level control relationships and retains all unresolved observations. Before approval, every observed component is classified as included, replaced, omitted or unsupported by the fixed baseline. Separate acknowledgments cover scope/simplifications and open questions. These are enforced in the service and optional API, not only in the UI.

Downloads include `component-scope.json`, `open-questions.json`, `control-coverage.json` and `corrected-graph.dot`, alongside the ADR and schema-v2 traceability manifest. The complex CCM fixture reproduces a supplied live extraction: 14 components, 12 connections, two boundaries and five unknowns. Its five confirmed findings are retained; six unverified coverage/resilience/policy questions are now surfaced. Fixture replay does not make a new live Meta call.

## Local demo package

Start with [DEMO_QUICKSTART.md](DEMO_QUICKSTART.md). Windows launchers, Linux/macOS launcher, offline readiness inventory, four-diagram workflow verification, and a GitHub publishing utility are included. Graph/target edits awaiting save block downstream actions; validator runtime errors still produce a downloadable failure report.

## Current acceptance status

For the lightweight public preview on Render Free, see [docs/RENDER_DEMO.md](docs/RENDER_DEMO.md). It keeps Terraform execution disabled, reports `not_run`, and requires an owner-configured API key and private demo code for live requests. Local Docker remains the complete validation environment.

This is an implemented P0 candidate, **not a completed submission**. Supplied live runs demonstrate text/image access and a complex graph matching its reference. Clean Docker validation passed in release CI, and the supplied live complex target passed the external GitHub validator. The final live walkthrough with a meaningful human correction and demo recording remains outstanding. See [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) for exact results. The supplied historical fixture walkthrough must not be presented as a current live Meta demonstration.

## Start locally (recommended: Docker Desktop, Linux containers, x86_64)

```bash
cp .env.example .env
# Set MODEL_API_KEY in .env to your Meta Model API key.
docker compose up --build
```

Open http://localhost:8501. Fixture mode needs no Meta key; the build needs internet to install pinned dependencies and prepare the provider mirror. The image build deliberately fails if clean, non-root, IP-blocked Terraform initialization and validation cannot pass. The AWS provider is unpacked at build time so runtime initialization links it from the read-only mirror without extracting its approximately 674 MiB binary into the temporary filesystem. Run Docker Desktop with Linux/amd64 containers. ARM images are intentionally unsupported in v1.

Compose limits the container to 2 CPUs, 2 GiB memory and 128 processes, drops capabilities, disables privilege escalation, uses a read-only root filesystem, and binds the UI to localhost. The application requires network access for Meta; the **validator subprocess and its descendants** have IP socket creation blocked by libseccomp. Unix sockets remain available for provider RPC. This is a restriction around trusted templates, not a general hostile-code sandbox.

### Complete the workflow

1. Select **Live Meta extraction**, optionally test text connectivity, and upload one PNG/JPEG (≤5 MB, ≤20 megapixels). Images are verified, resized to ≤1600 px, stripped of metadata, passed inline, and never written to disk by the service. The file widget is reset on successful extraction.
2. Inspect the original extraction. Correct the editable component/connection tables, or use Quick label correction. Save corrections; changed records become `user_corrected`. Duplicate IDs, invalid enums and dangling references are rejected atomically. Boundaries and unresolved questions can be edited as JSON.
3. Run architecture review. Six mandatory checks plus backup coverage, queue resilience and object-storage policy questions distinguish confirmed evidence from unverified coverage. Control links are assessed per service; even a shown link does not prove effective enforcement. Inspect all open questions.
4. Review the separate target, settings, decisions and component scope. Acknowledge simplifications, unsupported roles and unresolved questions, then explicitly approve that exact revision. Target changes and graph corrections invalidate approval and generated artifacts.
5. Generate. Read the structured per-stage results, inspect the resource-to-decision manifest and download the ZIP even if validation is failed or unavailable. Sessions and artifacts expire after one hour; background expiry clears in-memory observations/artifacts. No persistent accounts or queues exist.

The target is deliberately narrow: ALB, private ASG instances, isolated encrypted Multi-AZ PostgreSQL, managed database password, seven-day backups. It leaves TLS, authentication/authorization, monitoring, an application AMI, IAM credential access and application deployment unresolved. Private app subnets have no NAT or VPC endpoints. Read the ADR before interpreting the target as a runnable application.

### Tests and optional Python-only UI

```bash
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e '.[test]'
python -m pytest -q
python -m streamlit run streamlit_app.py
```

Python-only mode supports fixtures, live extraction, editing, review and downloads. Full validator support requires Linux, libseccomp, non-root subprocess execution, Terraform 1.9.8 and a prepared mirror. On Windows, use Docker Desktop for validation. Missing dependencies are reported as `not_run`, never `passed`.

For a manually prepared Linux toolchain, `scripts/build_mirror.py` is a **build-time-only** networked dependency installer; `TOOLCHAIN_ROOT` selects its output parent. Set `TERRAFORM_BIN`, `TERRAFORM_MIRROR` and `TERRAFORM_LOCK_FILE` to those trusted build outputs. The repository includes a genuine AWS 5.100.0 lock file obtained from HashiCorp's signed package installation; the Docker build independently creates its own lock and mirror.

### Live acceptance

```bash
# Set MODEL_API_KEY in the project .env, or export it in this terminal.
python scripts/live_acceptance.py examples/single-server.png
```

The UI and this script read only MODEL_API_KEY and META_MODEL from the project .env; existing nonempty terminal values take precedence. The script makes actual text and image requests; it exits nonzero on failure. It saves only sanitized status metadata and the validated graph under `acceptance/`. Repeat for `public-database.png` and `redundant-private.png`. Fixtures with matching JSON are for rule tests and recovery; they do not prove extraction quality. Check the real extracted graphs manually against every diagram.

Meta's documented API and the checked model are recorded in [docs/META_INTEGRATION.md](docs/META_INTEGRATION.md). Entitlement and live compatibility remain account-dependent. No third-party inference host is silently substituted.

### Offline runtime verification

```bash
docker build -t architecture-reviewer:local .
docker run --rm --network=none --cpus=2 --memory=2g --pids-limit=128 \
  --cap-drop=ALL --security-opt=no-new-privileges \
  architecture-reviewer:local python scripts/offline_smoke.py
```

This repeats the actual runtime validator against a new private workspace, with no cloud credentials and no container network. Runtime stages are version check, format, format check, backend-free read-only-lock init and `validate -json`. A filesystem mirror is the only provider installation method; no `direct` stanza exists. One file lock limits concurrent executions across local processes. All stages share a 180-second wall-clock budget and 64 KiB output budget. Timeouts/output overflow terminate the whole process group. Validation processes refuse root and fail closed if the network filter is unavailable.

### Three-diagram fixture verification

```bash
python scripts/doctor.py
python scripts/verify_workflow.py --output .local-checks
# Full Docker gate, including actual initialization and validation:
docker run --rm --network=none --cpus=2 --memory=2g --pids-limit=128 \
  --cap-drop=ALL --security-opt=no-new-privileges \
  architecture-reviewer:local python scripts/verify_workflow.py --require-validation
```

The fixture verifier checks all four diagrams, records a simulated correction, acknowledges component scope/open questions, checks 26 resource decision references, ZIP contents and approval invalidation. Its JSON always declares fixture mode and live acceptance as not run. `--require-validation` exits nonzero if actual validation is unavailable.

### Optional local FastAPI adapter

```bash
python -m uvicorn archreview.api:app --host 127.0.0.1 --port 8000
```

Use `/docs`: create a fixture session or extract an image; use its opaque token as `Authorization: Bearer ...`. Edit, review, approve with the displayed target revision, generate and download. FastAPI calls the same service as Streamlit. It is not required for the default image. Keep it bound to localhost. There is no public production authentication/rate-limit boundary in v1.

## Artifact contents

- `main.tf`, `versions.tf`, `variables.tf`, `outputs.tf`, genuine `.terraform.lock.hcl`
- `traceability.json` mapping every resource address to an approved decision
- `ADR.md`, `approved-target.json`, `original-extraction.json`, `corrected-graph.json`
- `corrections.json`, `findings.json`, `validation-report.json`, generated `README.md`

Templates are packaged, version-controlled Jinja2 files. Neither image text nor model responses can supply resource definitions, Terraform text, commands, template names or executable content. Resource identifiers and values come from a constrained target schema.

## GitHub and submission

A local Git repository and history are included in the delivery as `repository.bundle`. No remote repository has been created or pushed. Create an empty GitHub repository in your account/organization, then run from the extracted project folder:

```bash
# Inspect/prepare the destination without pushing:
python scripts/publish.py --repo https://github.com/YOUR_ACCOUNT/YOUR_REPOSITORY.git
# Publish with your normal Git credentials:
python scripts/publish.py --repo https://github.com/YOUR_ACCOUNT/YOUR_REPOSITORY.git --push
```

The utility restores the packaged history if needed, checks for uncommitted edits, uses a separate `publish` remote, and never force-pushes. Normal non-fast-forward protection applies if the destination already has commits. CI uploads Python results and offline validation reports. No Meta key is used in CI.

To create another release from a clean Git working tree, run `python scripts/make_release.py`. Verify a downloaded release with `python scripts/verify_release.py /path/to/architecture-diagram-reviewer-final.zip`.

See [docs/DEMO.md](docs/DEMO.md) for the required live recording and [docs/ACCEPTANCE.md](docs/ACCEPTANCE.md) for remaining gates. CI checks Python tests and builds/runs the complete offline Docker toolchain. Render hosting is deliberately deferred until local M3 passes; no hosted validation is offered.
