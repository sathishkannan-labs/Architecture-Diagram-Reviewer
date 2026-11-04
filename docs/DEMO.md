# Demo recording

The included `evidence/fixture-walkthrough.mp4` records the actual local Streamlit UI: fixture load, human correction, six-rule evidence review, target approval, traceability and ZIP download. Captions explicitly identify it as a fixture demonstration, and show validation as `not_run`. It is a development walkthrough, **not the required final live acceptance video**. It contains no live API key or uploaded private diagram.

## Final live recording — 3–5 minutes

1. Show the local Docker container and resource limits. Keep your API key off screen. State the validation limitations displayed in the app.
2. Select Live Meta extraction. Demonstrate successful live text connectivity and upload a real diagram. Show the extracted graph and compare its evidence to the diagram. Do not start from fixture JSON.
3. Make a visible human correction in a table or Quick label correction, save it, and show `user_corrected` provenance and the preserved original graph. If appropriate, correct a genuinely missed/ambiguous detail rather than changing a cosmetic label.
4. Run risk review. Show a confirmed issue with component evidence and an unverified missing-control question. Explain that diagram omission does not establish real-world absence.
5. Show the proposed target, decision IDs and the component-scope table. Explain unsupported or omitted roles and the difference between the new baseline and the uploaded topology. Show open questions and control coverage. Check all three acknowledgments, then approve the displayed revision.
6. Generate. Show actual `fmt`, `fmt-check`, `init` and `validate` stages with **passed** results. Expand output and show that runtime initialization used the bundled provider mirror.
7. Show at least one `traceability.json` resource address → approved decision → finding/observation/baseline assumption. Open the ADR from the same ZIP.
8. Download and inspect the ZIP and validation report. State that no plan or apply ran and validation does not prove security or provisioning readiness.

If any stage is unavailable, failed or timed out, disclose that and resolve it before marking M1/M3/M4 complete. Never replace a real validation screen with a mock or fixture success screen.

## Re-record the fixture UI walkthrough

This is an optional developer utility, independent of the application's dependencies:

```bash
python -m pip install playwright==1.51.0
python -m playwright install chromium
# Install ffmpeg using your OS package manager, then:
python scripts/record_fixture_demo.py
```

The recording helper starts its own temporary Streamlit process, operates the real UI, adds truthful fixture captions, downloads the ZIP, and converts the browser recording to MP4. It intentionally expects `not_run` on an environment without the complete validation toolchain. On a fully configured host, change the recording expectation and caption to the actual report before re-recording; never force the result to fit a script.
