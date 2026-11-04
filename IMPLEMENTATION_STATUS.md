# Release 0.2 implementation status — November 3, 2026

**Demo/publish source package prepared. Full live acceptance remains incomplete.** Start with DEMO_QUICKSTART.md.

The project implements Meta Model API extraction, verified/resized image handling, editable Streamlit UI, direct Python workflow service, six mandatory rules, correction audit, revision-bound target approval, trusted Terraform templates, 26 resource decision references, ADR/ZIP generation, restricted Linux validator, provider-mirror Docker build, optional FastAPI adapter and GitHub CI.

## Changes completed in this release

- Fixed Docker's Terraform extraction/cleanup command, which previously tried to remove a license from the wrong directory.
- Changed the build-time mirror to unpack the approximately 674 MiB AWS provider into the image. Runtime initialization can link the provider from the mirror instead of exhausting the 512 MiB job tmpfs. Archive paths are allowlisted; unexpected contents fail the build.
- Fixed Windows Python-only support: Linux's fcntl is optional, and unsupported validation reports `not_run` while the UI and downloads remain usable.
- Added Windows CMD/PowerShell and Bash launchers, local .env loading limited to the two Meta settings, readiness inspection and three-diagram integration verification.
- Prevented unsaved graph/target edits from reaching downstream actions. Kept table edits authoritative; details JSON cannot replace component/connection tables.
- Hardened uncertain-fact rules: inferred/low-confidence redundancy, private placement and failover remain questions; uncertain Internet edges cannot establish confirmed exposure.
- Made validator exceptions produce downloadable failure reports atomically; checked structured `validate -json` validity before reporting a pass.
- Improved risk evidence, target decisions, traceability and ADR inspection in the UI. Re-recorded the real fixture walkthrough.
- Added Git history restoration/publication utility, hash-verified release packaging and CI report artifacts. Publication never force-pushes or commits working files automatically.

## Verified here

- **65 tests passed; four native non-root subprocess tests skipped.** Exact output: docs/evidence/pytest.txt. Tests cover extraction, edits, six rules, uncertainty, approval, traceability, API, UI, Windows fallback, provider unpacking, process supervision, Git bundle restoration and release tamper detection.
- All three synthetic diagram workflows pass the integration checks, including 26 traced resources each and stale-approval rejection. Actual validation is `not_run`: docs/evidence/fixture-workflow-summary.json.
- A real browser recorded human correction, evidence review, target approval and ZIP download from the current UI. The video and download accurately identify fixture mode and unavailable validation.
- Exact direct project dependencies installed successfully. Packaging includes trusted templates and genuine AWS 5.100.0 lock data.

## External gates not claimed as passed

- **Live Meta text/image:** no MODEL_API_KEY is configured here. Official docs were checked in the first implementation; the client is mocked-tested. Set your key/model and run live acceptance before recording a final submission.
- **Actual clean Docker validation:** Docker is unavailable, and this managed host maps only UID 0. Non-root validation fails closed. Mirror unpacking and orchestration are tested; a full Docker build/offline run is still required.
- **Windows launcher execution:** PowerShell is unavailable on this Linux host. Windows fallback behavior is tested; native Windows launcher execution remains to be checked on the user's PC.
- **GitHub remote/CI:** no destination repository was provided. Local history, a tested restoration/push utility and CI are included. No remote push or successful remote CI run is claimed.
- **Final live demo:** the included video is a fixture rehearsal, not the requested end-to-end live acceptance recording. Render/public hosting remains deferred.

Terraform validation does not prove security, provisioning success, application readiness or production suitability. No plan or apply is run.
