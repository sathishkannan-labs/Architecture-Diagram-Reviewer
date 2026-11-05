# Captured live complex run

Captured November 4, 2026 from the hosted app. The input was the project's synthetic complex CCM architecture image; **a real Meta image request** produced the graph. It was not loaded from fixture JSON.

The run contains 14 components, 12 connections and two boundaries. One manual source-backed clarification added the legacy PostgreSQL public-port/failover annotation before review. Review produced five confirmed findings and six unverified findings. The target explicitly selected `legacy_postgresql` as its database source and accounted for one included, two replaced, four omitted and seven unsupported components. It generated 26 resource references.

The exact captured request and UI test results are retained in the private demo pack. They are not published here because they contain graph labels, evidence and correction history.

## Validation status

The hosted download remains not_run. The current code CI validates all four public fixtures. The exact captured live target has not been validated by this final patch's CI; historical validated output is a different run, linked in the parent evidence directory.

A real hosted image request is distinct from fixture loading. Replaying an approved request makes no fresh Meta call. Validation does not provision AWS or prove application readiness.

The privately prepared demo pack contains 28 screenshots and a 115-second silent captioned slideshow; it is not continuous recording. A final narrated public video URL remains pending.
