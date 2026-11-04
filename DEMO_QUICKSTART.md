# Start the demo and publish the source

## Windows — recommended full demonstration

1. Install/start Docker Desktop using **Linux containers** on an x86_64 PC. Extract the entire ZIP into a folder.
2. Copy `.env.example` to `.env`. For live extraction, set `MODEL_API_KEY` to your Meta Model API key. Leave it empty to try synthetic fixtures. Never put AWS credentials in the application.
3. Run `start-demo.cmd`, or open PowerShell in the folder and run:

```powershell
.\start-demo.ps1
```

The launcher builds the image, runs its mandatory offline validation gate, starts the app, checks UI health and opens http://localhost:8501. The first build downloads the pinned toolchain and provider. Build/validation failure stops startup with an error; it is never replaced with a mock pass.

Stop with `docker compose down`. After changing `.env`, run the launcher again to recreate the service with the new setting.

### Try the UI before Docker is available

```powershell
.\start-demo.ps1 -PythonOnly
```

Python 3.11+ is required. This creates a virtual environment and installs the project. Fixtures, correction, risk review, approval, Terraform generation and ZIP download work. Restricted validation on Windows reports `not_run`; use Docker for the complete validation stage. If your system blocks PowerShell scripts, use the Python commands in README.md under “Tests and optional Python-only UI”.

## Linux/macOS

```bash
chmod +x start-demo.sh
./start-demo.sh
# Or the Python-only UI:
./start-demo.sh --python-only
```

The full image targets Linux/amd64. Apple Silicon/ARM users need an x86_64 Docker environment for this release.

## Five-minute walkthrough

1. Fixture practice: load **public-database** to see a confirmed public exposure finding. For final acceptance, select **Live Meta extraction**, test text connectivity and upload a real diagram.
2. Inspect the original extraction; edit a label or other graph fact and save. Show the `user_corrected` provenance. Unsaved graph edits disable review/generation/download.
3. Run architecture review. Open a confirmed finding, an unverified coverage question and the service-level coverage table. A missing or inferred relationship does not prove a real control is absent.
4. Review the separate AWS target, decision IDs, component scope and open questions. Save target settings. Check the target consent, scope acknowledgment and unresolved-question acknowledgment, then record approval of that revision.
5. Generate and inspect every validation stage. Download the ZIP; check `traceability.json`, `ADR.md`, original/corrected graphs and `validation-report.json`.

The bundled `docs/evidence/fixture-walkthrough.mp4` shows the real fixture UI with validation unavailable. It is a rehearsal recording, not live Meta acceptance. Record the final live demo only after both Meta requests and Docker validation succeed.

## Publish to GitHub

Create an empty repository on GitHub, then run with your normal Git credentials:

```powershell
python scripts/publish.py --repo https://github.com/YOUR_ACCOUNT/YOUR_REPOSITORY.git --push
```

This restores the included Git history if needed and pushes `main` without overwriting existing history. Check the resulting GitHub Actions runs before submission. Actual remote publication has not been performed in this environment.

## What remains externally unverified

- Meta account/model access and successful live text/image extraction: key not provided here.
- Clean Docker build and actual restricted Terraform validation: Docker unavailable here; this host maps only UID 0.
- Windows launcher execution: prepared for Windows, but this development host is Linux. Windows validation fallback is unit-tested.
- GitHub publication/CI and final live recording: require the destination repository and successful live/Docker gates.

**Terraform validation does not prove security, provisioning success, application readiness or production suitability. No plan or apply is run.**
