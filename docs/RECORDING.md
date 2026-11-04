# Final demo recording checklist

1. Open https://adr.sathishkannan.com and explain: diagram risk review plus a fixed illustrative AWS remediation baseline.
2. Select Live Meta extraction, enter the private demo code without displaying it, and upload the complex diagram. Keep credentials out of the recording.
3. Show extracted counts and saved graph. Compare with the diagram; record a meaningful, truthful human clarification with evidence. Do not invent a change merely to exercise the UI.
4. Run review. Show the critical public-database finding and high findings. Explain that unverified control coverage is not proof of absence.
5. Select legacy_postgresql as the database role, save target settings, and show the finding-to-target summary. Public DB exposure and failover are addressed in the new baseline only; independent application services remain unsupported. No existing database is changed or migrated.
6. Inspect scope and unresolved questions. Acknowledge all three approval boxes and record approval. Generate approved Terraform.
7. Download validation-request.json, open GitHub's workflow, choose main, paste the JSON, and run. A blank request validates only the fixture. Label any edit/time skip while it runs.
8. Open the completed run and its artifact. Show validation-report.json with actual status and validation-context.json matching revisions. The Render ZIP remains not_run; the external result is separate.
9. Close with limitations: AWS only; illustrative infrastructure; no application bootstrap, IAM/secret integration, TLS, migration or plan/apply. Queue/storage and independent services are not generated. No resources were provisioned.

The historical validated sample is available through the app and docs/evidence/README.md. Identify it as historical evidence if used; do not substitute it for the new request's result.
