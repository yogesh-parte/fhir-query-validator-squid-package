---
id: 015-demo-scripts
feature: fhir-validator
status: done
---

# Demo Scripts

## Scope

Implement operator-facing demo scripts in `scripts/` and wire Makefile targets per `specs/fhir-query-validator-factory.md` §9 and `scripts/README.md`.

**Deliverables:**
- `scripts/demo_loops.py` — feedback loops demo against public HAPI: cache miss/hit, invalid query → learner escalation
- `scripts/demo_agent_traceability.py` — per-agent pipeline trace, human pause → review → resume, `--export traces.json`, `--server` flag
- `scripts/demo_loops_mockhealth.py` — authenticated mock.health demo (requires `MOCK_HEALTH_API_KEY`)
- `scripts/demo_query_generator.py` — generate sample queries from CapabilityStatement search params
- `scripts/_demo_utils.py` — shared formatters, server selection, human review console helpers
- Makefile targets: `demo-loops`, `demo-agent-trace`, `demo-mockhealth` invoke real scripts (remove placeholder echoes)
- Each script supports `--help` and exits non-zero on workflow failure

Depends on tasks 012, 013, 011.

## Acceptance criteria

- [ ] `make demo-loops` runs successfully against HAPI showing cache status, validation result, and learner escalation on repeated invalid queries.
- [ ] `make demo-agent-trace` demonstrates per-agent trace output and human pause → resume; `--export` writes valid JSON trace bundle.
- [ ] `make demo-mockhealth` skips gracefully with clear message when `MOCK_HEALTH_API_KEY` is unset; succeeds when key is present in `.env.local`.
- [ ] `demo_query_generator.py` produces at least one valid and one intentionally invalid query for demo purposes from live CapabilityStatement.
- [ ] All demo scripts use `run_validation_workflow` (not duplicated agent calls); scripts have unit/smoke tests where feasible.

## Out of scope

- `demo_adk_cli.py`, `demo_adk_web.py`, Jupyter notebooks (Phase 5 parity items, optional follow-up).
- Langfuse-enabled demo path.
- Production deployment or Docker compose for demos.

## Log
### [PA] 2026-07-03 — Grooming
Initial task from /squid-plan on specs/fhir-query-validator-factory.md.