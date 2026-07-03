---
id: 007-query-validator
feature: fhir-validator
status: done
---

# QueryValidator Agent

## Scope

Implement `src/agentic_layer/agents/query_validator.py` per `docs/spec/query-validation-spec.md`: validate any FHIR search query against the interpreted CapabilityStatement, emit structured errors/warnings, and record failure events for downstream Rule Agent pattern detection.

**Deliverables:**
- `QueryValidator` class with `validate(query_url, capability_index, server_key, user_id=None) -> QueryValidatorOutput`
- Validate: resource type exists, each search parameter is declared, modifiers are supported, comparators are valid for param type, chained/revinclude params (basic support)
- Integrate `query_parser` (task 004) and `url_safety` (task 004) before validation
- Clear, actionable error messages (e.g., suggest correct camelCase parameter names)
- Attach `validation_errors` list with severity (`error` | `warning` | `high_severity`) for Rule Agent consumption
- Support `validate_only` and `validate_and_execute` mode awareness (set `executed=False` at this stage)
- Unit tests: valid queries, unknown params, wrong modifiers, wrong comparators, unknown resource, SSRF-blocked URLs
- Hooks to emit failure events to Rule Agent (interface only; full wiring in task 012)

Depends on tasks 001, 004, 006.

## Acceptance criteria

- [ ] Valid HAPI query `Patient?gender=male` returns `valid=True` with empty `errors`; invalid param `Patient?birthdate=1990` returns `valid=False` with actionable message referencing `birthDate`.
- [ ] High-severity errors (e.g., SSRF attempt, completely malformed URL) are tagged for immediate human escalation per `docs/spec/rule-and-learner-spec.md`.
- [ ] Validation works consistently when switching `server_key` across `hapi`, `firely`, `spark`, `wildfhir` using registry configs (unit tests with per-server fixture indexes).
- [ ] All validation decisions append to audit trail via `AuditLogger`; output matches `QueryValidatorOutput` entity contract.
- [ ] ≥99% unit test coverage on validator logic; at least one integration test validates a live query against HAPI CapabilityStatement end-to-end.

## Out of scope

- Query execution (task 008).
- LLM-based validation or natural-language query input.
- Full FHIR `_filter` grammar validation.

## Log
### [PA] 2026-07-03 — Grooming
Initial task from /squid-plan on specs/fhir-query-validator-factory.md.