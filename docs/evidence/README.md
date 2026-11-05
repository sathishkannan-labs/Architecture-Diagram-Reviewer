# Current and historical evidence

See [the November 4 live complex run](live-complex/README.md) for the captured run summary. Its exact request stays in the private demo pack and its hosted report is not_run. Current fixture CI is separate.

# Validated complex sample evidence

[Download the validated live-Meta sample](release-0.4-live-validated-artifacts.zip).
This is historical release 0.4 evidence from the user-supplied complex diagram run,
not a fresh run or an approval of release 0.5 output. It contains 14 observed
components and 12 connections, original/corrected graphs, approved target,
findings, scope, questions, Terraform and the actual validation report.

Terraform 1.9.8 / AWS provider 5.100.0: version, fmt, fmt-check, offline init and
validate passed; zero validation errors and warnings. No plan or apply ran.
The request and both revisions and file hash sets matched the supplied app ZIP.
No human correction was recorded in this historical sample.

The sample retains eight unsupported and four omitted components. It is an
illustrative baseline, not a full conversion or migration. New database-role
selection and finding summaries require a fresh approval and validation request.

`validation-context.json` records expected pre-format file hashes and validated
post-format hashes. Terraform fmt changed whitespace in three files; this is
expected and recorded, not a hash mismatch. Release 0.5 templates have been aligned with Terraform fmt; all four fixture outputs now pass fmt-check before any formatting. The workflow still checks fmt again.

The offline init message `Installed ... (unauthenticated)` comes from installation
using the bundled filesystem mirror, not a newly authenticated registry download.
At image build time Terraform init obtains the pinned provider from its registry,
verifies the registry checksums/signature and writes the genuine dependency lock;
providers mirror prepares the bundled package. Runtime init uses that mirror and
lock with network disabled. This is not a claim that offline init independently
verified a publisher signature. The Terraform binary archive is checked against
HashiCorp's HTTPS checksum list; detached checksum-signature verification is not
implemented. The image and build pipeline remain part of the trust boundary.

Other files in this directory include older fixture evidence and videos. Their
filenames and release records identify them; do not present those as a current
live demonstration.
