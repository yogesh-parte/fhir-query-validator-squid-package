---
id: 004-shared-utils
feature: fhir-validator
status: done
---

# Shared Utilities (audit_log, query_parser, url_safety)

## Scope

Implement cross-cutting utilities in `src/agentic_layer/utils/` used by multiple specialist agents and the workflow engine.

**Deliverables:**
- `utils/audit_log.py` — `AuditLogger` with correlation-ID support; append per-agent entries (`agent_name`, `timestamp`, `duration_ms`, `decision`, `metadata`); in-memory trail assembly for export
- `utils/query_parser.py` — parse FHIR search URLs into resource type, parameters, modifiers (`:exact`, `:contains`), comparators (`eq`, `gt`, `ge`, etc.), and chained parameters; handle relative and absolute URLs
- `utils/url_safety.py` — SSRF mitigation: block private/loopback hosts, enforce allowed schemes (`https` only in production flag), validate `query_url` host matches resolved server base; no redirect following helpers
- `utils/__init__.py` — public exports
- Unit tests with edge cases: malformed URLs, casing variants, chained search params, audit trail ordering, redacted sensitive fields

Align with Phase 5 security controls in `planning/phase-5-demo-hardening-and-governance.md` and `docs/traceability.md`.

## Acceptance criteria

- [ ] `query_parser.parse("Patient?birthDate=ge1990-01-01&gender=male")` returns structured components including comparator `ge` and resource `Patient`; invalid URLs raise `QueryParseError` with line-level detail.
- [ ] `url_safety.validate_query_url(query_url, server_base)` rejects SSRF targets (e.g., `http://127.0.0.1`, `http://169.254.169.254`) and mismatched hosts; passes for valid FHIR search URLs against registered server bases.
- [ ] `AuditLogger` records entries in invocation order, attaches `correlation_id`, and produces a JSON-serializable list consumable by task 013 export; no secrets in `metadata`.
- [ ] All three utility modules have ≥99% unit test coverage with parametrized edge-case tests.
- [ ] Utilities are pure/stateless where possible; `AuditLogger` is injectable into agents for test isolation.

## Out of scope

- Production log redaction via `logging_safe.py` (optional hardening in task 018).
- FHIRPath or complex `_filter` expression parsing beyond standard search parameters.
- Langfuse span creation wrappers.

## Log
### [PA] 2026-07-03 — Grooming
Initial task from /squid-plan on specs/fhir-query-validator-factory.md.