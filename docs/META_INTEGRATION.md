# Meta integration verification — 2026-11-03

Documentation checked against primary Meta sources:
- https://dev.meta.ai/docs/api-reference — official base URL `https://api.meta.ai/v1`, bearer `MODEL_API_KEY`, Chat Completions endpoint.
- https://dev.meta.ai/docs/cookbook/vision-input — `muse-spark-1.3`, user-message `image_url` parts with inline data URLs.
- https://dev.meta.ai/docs/api-reference/chat-completions/schemas — message and response shapes.

This is a **Meta Model API** integration, not an assumption that the older Llama API wire format is compatible. Model entitlement remains account-dependent. The host is fixed in code; no credential-forwarding custom URL setting is accepted.

Live text and image calls: **NOT RUN — no MODEL_API_KEY provided in the development environment**. Do not describe M1 as passed. Run `python scripts/live_acceptance.py examples/single-server.png` after setting your key and chosen model. The script first probes text, then performs actual image extraction and records only graph output and pass/fail metadata. Graph evidence may contain diagram labels: keep the generated acceptance folder private if your diagram is confidential.

The client uses at most three attempts (network errors, 429, selected 5xx only), fixed 60-second request timeouts, capped responses, strict schema validation, no request/response debug logging, and no file uploads to the provider Files API. Images exist in memory for the request; Python cannot promise cryptographic memory erasure. Provider-side retention is governed by Meta's terms.
