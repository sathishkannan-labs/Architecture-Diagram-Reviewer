# Submission handoff

## Links

- Live demo: https://adr.sathishkannan.com/
- Source: https://github.com/sathishkannan-labs/Architecture-Diagram-Reviewer
- Evidence: [live run summary](evidence/live-complex/README.md) and [validated historical bundle](evidence/README.md)
- Checks: https://github.com/sathishkannan-labs/Architecture-Diagram-Reviewer/actions
- **Final public video URL: pending upload**

## Project name

Architecture Diagram Reviewer

## Tagline

Turn architecture diagrams into evidence-based risk reviews and human-approved AWS remediation baselines.

## Short description

Architecture Diagram Reviewer uses Meta's multimodal API to extract components and connections from a diagram, preserving evidence and uncertainty. Users correct the graph, inspect grounded findings, acknowledge scope and open questions, and approve a revision before trusted templates generate an illustrative AWS Terraform baseline. A separate restricted Docker workflow validates the exact approved output with hash-bound provenance.

## Problem and approach

Architecture diagrams communicate intent, but reviews often lose the connection between a visual observation, a risk finding and a proposed change. This project keeps that chain visible. Explicit public-database exposure can become a confirmed critical finding; an authentication control missing from a picture remains a question.

Meta handles the visual interpretation. Deterministic rules, constrained targets and trusted templates keep downstream decisions auditable. Human correction, retained originals, revision-bound approval and per-resource traceability support review rather than automatic trust.

The complex CCM demonstration extracted 14 components and 12 connections through a real Meta request. A source-backed manual clarification was recorded before review. The approved baseline accounts for every component while explicitly identifying omitted and unsupported services.

## What makes it different

- Evidence and uncertainty stay attached to observations and findings.
- Changes invalidate downstream approval and downloads.
- Every generated resource traces to an approved decision and finding or explicit baseline assumption.
- Validation is separated from the public host and bound to the request, target and file hashes.
- Scope limitations are visible before approval.

## Scope and limitations

The generated Terraform is AWS-specific: a fixed two-AZ ALB/ASG/RDS PostgreSQL baseline. It does not faithfully recreate every diagram, migrate databases, deploy application code or implement all operational controls. Terraform validation checks configuration validity; no AWS plan/apply is run. The Render download reports not_run because execution happens separately. Live access requires the private demo code; fixture mode works without API credentials.

## Final checklist

- [ ] Confirm the authenticated portal's actual fields, eligibility, track and video requirements.
- [ ] Upload the final narrated video and replace the pending URL above; verify public playback.
- [ ] Provide judge access through an appropriate private submission field, never the README or video.
- [ ] Check demo, source and evidence links from a signed-out browser.
- [ ] Paste/adapt this copy, review declarations and submit using the contest account.
- [ ] Save the submission confirmation.

Suggested positioning: indie project, Build for Your World, subject to the portal's actual options. The public event page announced November 4 at 9 PM ET (November 5 at 7:30 AM IST); confirm any updates in the portal: https://dev.meta.ai/events/global-hackathon and https://cerebralvalley.ai/e/meta-ai-developer-hackathon/hackathon/submit.

This document prepares the entry. It is not confirmation that the contest submission has been sent.
