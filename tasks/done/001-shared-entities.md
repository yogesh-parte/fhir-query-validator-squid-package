---
id: 001-shared-entities
feature: fhir-validator
status: done
---

# Shared Pydantic I/O Contracts

## Scope

Define strict, versioned Pydantic v2 models in `src/agentic_layer/entities/` that serve as the single source of truth for all agent inputs, outputs, and the top-level workflow response contract.

**Deliverables:**
- `entities/requests.py` — `ValidationRequest` (`query_url`, `server_key`, `user_id`, `mode`, `auth_token`, `force_refresh`, `correlation_id`)
- `entities/responses.py` — `ValidationResponse` matching the master spec output contract (`valid`, `server_used`, `errors`, `warnings`, `executed`, `results`, `audit_trail`, `escalation`)
- `entities/agent_outputs.py` — typed outputs for CacheAgent, CapabilityInterpreter, QueryValidator, QueryExecution, RuleAgent, SearchLearner, HumanInterventionGate
- `entities/audit.py` — `AuditEntry`, `AgentAuditBlock`, `EscalationInfo`, `AuditTrailBundle`
- `entities/errors.py` — structured `ValidationError`, `ExecutionError`, `AuthError` with severity levels
- `entities/__init__.py` — public re-exports for downstream agents and tests
- Unit tests in `tests/unit/agentic_layer/entities/` validating serialization, required fields, and enum constraints

All models must use type hints, field validators where appropriate, and JSON-serializable defaults. Reference `specs/fhir-query-validator-factory.md` §5 and individual agent specs in `docs/spec/`.

## Acceptance criteria

- [ ] `ValidationRequest` and `ValidationResponse` match the master spec I/O tables and output JSON contract exactly (field names, types, optional vs required).
- [ ] Every specialist agent has a dedicated Pydantic output model with an `audit` block; models round-trip through `model_dump()` / `model_validate()` without data loss.
- [ ] `mode` is constrained to `validate_only` | `validate_and_execute`; `escalation.type` accepts `learner` | `human` | `null`.
- [ ] Unit tests cover required-field validation, invalid enum rejection, and JSON schema examples from `docs/spec/*.md` (≥99% coverage on `entities/`).
- [ ] No agent module defines duplicate ad-hoc dict contracts — all imports flow from `entities/`.

## Out of scope

- HTTP client logic, caching, or workflow orchestration (handled in later tasks).
- LLM-specific message schemas or Langfuse span types.
- Database persistence models or Redis cache serialization formats.

## Log
### [PA] 2026-07-03 — Grooming
Initial task from /squid-plan on specs/fhir-query-validator-factory.md.