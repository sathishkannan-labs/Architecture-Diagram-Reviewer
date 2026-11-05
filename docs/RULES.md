# Current review rules

Nine rule IDs are implemented. AR-002 is not emitted or used by target decisions.

| Rule | Subject | Result |
|---|---|---|
| AR-001 | Application redundancy | One grounded instance can confirm a high finding; unknown redundancy is unverified. |
| AR-003 | Database exposure | Grounded public placement or a grounded Internet edge can confirm critical exposure. |
| AR-004 | Authentication | Missing grounded coverage becomes an unverified question. |
| AR-005 | Secrets | Missing grounded coverage becomes an unverified question. |
| AR-006 | Database failover | Grounded explicit absence can confirm a high finding. |
| AR-007 | Backup/recovery | Missing grounded coverage becomes an unverified question. |
| AR-008 | Monitoring | Missing grounded coverage becomes an unverified question. |
| AR-009 | Queue resilience | Queue-labelled services raise unverified delivery/retry/resilience questions. |
| AR-010 | Object-storage policy | Storage-labelled services raise unverified policy/encryption questions. |

Grounding requires evidence, non-inferred provenance and confidence at least 0.8 **when a confidence value is supplied**. A null confidence does not independently disqualify an otherwise grounded observation. Confirmed findings receive 0.95; unverified findings receive 0.6. These are rule-assigned values, not calibrated probabilities.

Control coverage needs grounded service relationships or an applicable authentication boundary. A standalone control box does not establish coverage or real-world effectiveness.

For components of type `other`, case-insensitive whole-word aliases recognize queue, SQS, Kafka and RabbitMQ; storage aliases recognize object storage, object-storage, S3 and bucket. These labels identify topics for questions, not proof of a missing control. Such roles remain unsupported by the fixed Terraform baseline.
