---
id: 008-query-execution
feature: fhir-validator
status: done
---

# QueryExecution Agent

## Scope

Implement `src/agentic_layer/agents/query_execution.py` per `docs/spec/query-execution-spec.md`: safely execute pre-validated FHIR search queries and return structured Bundle or OperationOutcome results.

**Deliverables:**
- `QueryExecutionAgent` class with `execute(query_url, server_key, auth_token=None, user_id=None) -> QueryExecutionOutput`
- Guard: refuse execution unless caller passes `validated=True` flag or `QueryValidatorOutput.valid` from same request context
- HTTP GET via `httpx` with auth headers from `AuthProvider`; redirects disabled by default
- Parse 200 + Bundle (extract `resource_count`), OperationOutcome, 4xx/5xx errors
- Record `duration_ms`, `status_code`, `executed_at` in audit block
- Error taxonomy: `network`, `auth`, `server_error`, `empty_result` (successful with `resource_count=0`)
- Unit tests with MockTransport; integration tests against HAPI and Firely with known valid queries

Depends on tasks 001, 003, 004.

## Acceptance criteria

- [ ] Agent refuses to execute when `validated=False` or validation errors present in same workflow context; no bypass path in public API.
- [ ] Successful execution of `Patient?gender=male` against HAPI returns `executed=True`, `result_type=Bundle`, `resource_count>=0`, and parseable `results` JSON.
- [ ] Auth failure on protected server returns `error_type=auth` with clear message; network timeout returns `error_type=network` without unhandled exceptions.
- [ ] Empty search results (`resource_count=0`) are treated as successful execution, not an error.
- [ ] ≥99% unit test coverage; integration tests execute real queries against ≥2 public test servers.

## Out of scope

- Result set caching or paging/`_count` orchestration beyond passing through URL params.
- Streaming large bundles or truncated result policies.
- Write operations (POST/PUT/DELETE) on FHIR resources.

## Log
### [PA] 2026-07-03 — Grooming
Initial task from /squid-plan on specs/fhir-query-validator-factory.md.