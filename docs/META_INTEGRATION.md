# Meta integration and evidence

The application uses the **Meta Model API** for image-to-graph extraction. The fixed host is `https://api.meta.ai/v1`, with bearer `MODEL_API_KEY`, Chat Completions and default model `muse-spark-1.3`. Model entitlement is account-dependent.

Primary references: [API reference](https://dev.meta.ai/docs/api-reference), [vision input](https://dev.meta.ai/docs/cookbook/vision-input), [message schemas](https://dev.meta.ai/docs/api-reference/chat-completions/schemas).

## What was actually tested

The November 3 development-host entry saying live calls were not run was historical, not the current project status. A real hosted walkthrough on November 4 successfully extracted the synthetic complex CCM image using live Meta: 14 components, 12 connections and two boundaries. It included one source-backed manual clarification before review, approval and download. See [the live run summary](evidence/live-complex/README.md). A synthetic input image with a real model request is distinct from loading fixture JSON.

The private demo pack contains 28 screenshots and a 115-second silent, captioned slideshow. That slideshow is assembled from screenshots, not continuous screen recording. Historical validated output is separately identified in [evidence](evidence/README.md).

## Bounded recovery

The adapter accepts bare JSON or a complete fenced JSON block, then validates the strict graph schema and rejects `user_corrected` provenance from the model. A schema failure permits exactly one new extraction attempt using the same image and only sanitized error type names. Invalid model output, labels and raw validation errors are not echoed into the retry feedback. It does not repair facts or guarantee success.

Each completion operation has at most three HTTP attempts for selected transient failures. Extraction therefore has at most two completion operations and six HTTP attempts; a text probe has one operation and at most three attempts. Each operation consumes the hosted budget. Transport errors, refusals and incomplete responses do not trigger schema recovery.

Images are checked, resized and sent in memory; response sizes and timeouts are bounded. No provider Files API or debug payload logging is used. Python does not guarantee memory erasure, and provider retention follows Meta's terms.

## Why the downstream stages are deterministic

Meta interprets visual labels and relationships into an editable graph. Human correction and provenance are retained. Rules classify diagram evidence; target selection, approvals and Terraform use constrained schemas and trusted templates. This boundary makes recommendations auditable and keeps model-generated executable code out of the validator. No second model-written review feature is claimed.
