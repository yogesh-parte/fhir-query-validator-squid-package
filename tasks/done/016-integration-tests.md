---
id: 016-integration-tests
feature: fhir-validator
status: done
---

# Integration Tests (Live Public Servers)

## Scope

Add `tests/integration/` suite exercising real FHIR public test servers and optional mock.health, validating end-to-end behavior beyond unit mocks.

**Deliverables:**
- `tests/integration/conftest.py` — markers, server availability checks, skip when offline
- `tests/integration/test_cache_live.py` — CacheAgent against HAPI, Firely, Spark metadata endpoints
- `tests/integration/test_validation_live.py` — valid/invalid queries across ≥3 public servers
- `tests/integration/test_execution_live.py` — `validate_and_execute` against HAPI and Firely
- `tests/integration/test_escalation_live.py` — repeated invalid queries triggering learner threshold (may use accelerated window settings in test env)
- `tests/integration/test_mockhealth_live.py` — skipped unless `MOCK_HEALTH_API_KEY` set; validates auth metadata + simple query
- `pyproject.toml` marker registration: `integration`, `mockhealth`
- CI: integration job runs on schedule or manual workflow_dispatch; PR job runs unit tests only (or integration with `continue-on-error` documented)

Depends on tasks 005–012.

## Acceptance criteria

- [ ] Integration tests pass locally against HAPI, Firely, and Spark when network is available; skipped gracefully when servers unreachable.
- [ ] `test_validation_live` confirms a known-valid query returns `valid=True` and known-invalid param returns `valid=False` on each public server.
- [ ] `test_execution_live` returns Bundle with `resource_count>=0` for `Patient?_count=1` against HAPI.
- [ ] `test_mockhealth_live` is skipped without API key; passes with `MOCK_HEALTH_API_KEY` in env fetching `/metadata`.
- [ ] Integration suite documented in `tests/integration/README.md` with run commands: `uv run pytest tests/integration -m integration`.

## Out of scope

- Load testing or performance benchmarks against public servers.
- Contract testing against every possible search parameter permutation.
- CI mandatory gate on every PR (network flakiness) — document opt-in CI job instead.

## Log
### [PA] 2026-07-03 — Grooming
Initial task from /squid-plan on specs/fhir-query-validator-factory.md.