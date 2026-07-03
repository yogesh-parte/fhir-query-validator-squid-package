---
id: 014-adk-root-agent
feature: fhir-validator
status: done
---

# ADK Root Agent (Thin Wrapper)

## Scope

Implement `fhir_validator_agent/` as a thin Google ADK 2.0 entrypoint that delegates all business logic to `run_validation_workflow` (ADR-002). No duplicated validation, caching, or escalation logic in the ADK layer.

**Deliverables:**
- `fhir_validator_agent/agent.py` — ADK root agent / graph node mapping inputs to `ValidationRequest` and returning `ValidationResponse` JSON
- `fhir_validator_agent/__init__.py` — package exports for `adk run` / Agent Engine deployment
- Input mapping: ADK session state or tool args → `query_url`, `server_key`, `mode`, optional `user_id`, `auth_token`
- Output mapping: `ValidationResponse.model_dump()` as ADK tool response
- Minimal ADK graph in `src/agentic_layer/graph/adk_graph.py` (optional) or inline in agent.py — single node calling workflow engine
- Unit test verifying ADK agent calls workflow engine (mocked) and does not import httpx directly
- README snippet for `adk run fhir_validator_agent` usage

Depends on task 012.

## Acceptance criteria

- [ ] `fhir_validator_agent/agent.py` contains no query validation, caching, or HTTP logic — only ADK boilerplate and `run_validation_workflow` delegation.
- [ ] ADK agent accepts the same inputs as `ValidationRequest` and returns JSON matching `ValidationResponse` schema.
- [ ] Running ADK agent with a valid HAPI query produces `valid=True` response equivalent to direct `run_validation_workflow` call (equivalence test).
- [ ] ADK wrapper is importable without side effects (no network calls at import time).
- [ ] Unit tests achieve ≥99% coverage on `fhir_validator_agent/` module.

## Out of scope

- ADK Web server deployment, Cloud Run packaging, or Agent Engine CI/CD.
- Multi-node ADK graphs with separate nodes per specialist agent (single delegation node for v1).
- OAuth or ADK-specific authentication beyond passing through `auth_token`.

## Log
### [PA] 2026-07-03 — Grooming
Initial task from /squid-plan on specs/fhir-query-validator-factory.md.