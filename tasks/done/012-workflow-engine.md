---
id: 012-workflow-engine
feature: fhir-validator
status: done
---

# Workflow Engine

## Scope

Implement `src/agentic_layer/graph/workflow_engine.py` as the Python-native orchestration source of truth (ADR-002), wiring all specialist agents with explicit feedback loops and assembling the final `ValidationResponse`.

**Deliverables:**
- `run_validation_workflow(request: ValidationRequest) -> ValidationResponse` public API
- Pipeline: CacheAgent → CapabilityInterpreter → QueryValidator → (conditional) QueryExecution
- Feedback loops: invalid query → RuleAgent → SearchLearner OR HumanInterventionGate → resume/retry QueryValidator
- Mode routing: `validate_only` skips QueryExecution; `validate_and_execute` runs execution only when `valid=True`
- Correlation ID propagation through all agents via `AuditLogger`
- Optional `WorkflowAgents` dependency injection for per-request isolation (settings flag, default singleton for demos)
- Unit tests with mocked agents verifying routing for valid/invalid/escalation paths
- Integration test: full happy path against HAPI in `validate_and_execute` mode

Depends on tasks 001–011.

## Acceptance criteria

- [ ] End-to-end `run_validation_workflow` with valid HAPI query returns master spec JSON contract with `valid=True`, populated `audit_trail`, and `escalation.required=False`.
- [ ] Invalid query triggers RuleAgent; at threshold 3 failures learner output is attached to response; at threshold 5 or high-severity, HumanInterventionGate pauses flow.
- [ ] `validate_only` mode never sets `executed=True` or calls QueryExecution; `validate_and_execute` calls execution only after `valid=True`.
- [ ] Execution errors feed back to audit trail and optionally RuleAgent for pattern tracking per `docs/loop-engineering.md`.
- [ ] ≥99% unit test coverage on workflow routing logic; integration test passes for HAPI valid query and learner escalation scenario with mocked failures.

## Out of scope

- Google ADK graph definition (task 014).
- Distributed workflow persistence or async job queues.
- Langfuse automatic instrumentation (optional future enhancement).

## Log
### [PA] 2026-07-03 — Grooming
Initial task from /squid-plan on specs/fhir-query-validator-factory.md.