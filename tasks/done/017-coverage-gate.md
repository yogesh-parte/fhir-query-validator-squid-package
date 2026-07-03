---
id: 017-coverage-gate
feature: fhir-validator
status: done
---

# Coverage Gate (≥99% CI)

## Scope

Enforce ≥99% unit test coverage on `src/agentic_layer` via pytest-cov and fail CI when the threshold is not met, per `AGENTS.md` and master spec quality gates.

**Deliverables:**
- `pyproject.toml` — `[tool.coverage.run]` source=`src/agentic_layer`, omit patterns for `__init__.py` only if justified
- `pyproject.toml` — `[tool.coverage.report]` `fail_under = 99`, `show_missing = true`
- `pytest` invocation in Makefile: `uv run pytest tests/ --cov=src/agentic_layer --cov-report=term-missing --cov-fail-under=99`
- `.github/workflows/ci.yml` — add coverage step to `lint-and-test` job after unit tests
- `htmlcov/` gitignored; optional `make coverage-html` target for local reports
- Coverage exclusions documented in `tests/README.md` if any lines are pragma-ignored (must be minimal and justified)

Depends on all implementation tasks 001–014 having tests.

## Acceptance criteria

- [ ] `make test` (or dedicated `make test-coverage`) fails with non-zero exit when `src/agentic_layer` coverage drops below 99%.
- [ ] CI workflow runs coverage gate on every push/PR to `main` and reports missing lines in log output.
- [ ] Coverage measures `src/agentic_layer` only (not scripts or `fhir_validator_agent` unless explicitly included); current coverage ≥99% after full implementation.
- [ ] No broad `# pragma: no cover` blocks on business logic; any exclusions listed in `tests/README.md` with rationale.
- [ ] Coverage configuration works with `uv run pytest` without additional manual setup.

## Out of scope

- 100% coverage mandate or branch coverage gates.
- Coverage tracking for `scripts/` or `fhir_validator_agent/` (may add later).
- Codecov or Coveralls external service integration.

## Log
### [PA] 2026-07-03 — Grooming
Initial task from /squid-plan on specs/fhir-query-validator-factory.md.