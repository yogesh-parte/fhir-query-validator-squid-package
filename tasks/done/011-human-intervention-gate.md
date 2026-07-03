---
id: 011-human-intervention-gate
feature: fhir-validator
status: done
---

# HumanInterventionGate

## Scope

Implement `src/agentic_layer/agents/human_intervention_gate.py` per `docs/spec/human-intervention-spec.md`: pause automated workflow on human escalation, surface rich context, collect human decision, and resume or terminate.

**Deliverables:**
- `HumanInterventionGate` class with `request_review(context: HumanReviewContext) -> HumanDecisionOutput`
- Context package: failing query, failure history (top 5 + total count), learner suggestions, escalation reason, correlation ID, CapabilityStatement excerpt
- Pause mechanism: blocking console prompt in interactive mode; auto-approve stub in non-interactive/test mode (configurable)
- Decisions: `approve`, `reject`, `modify_query`, `escalate_further`; optional `override_query` triggers re-validation on resume
- Audit: `reviewed_by`, `reviewed_at`, `human_notes`, `resume_workflow` flag
- `scripts/_demo_utils.py` helper for formatted console review (shared with task 015)
- Unit tests for each decision path, timeout fallback, learner-vs-human conflict (human wins)

Depends on tasks 001, 009, 010.

## Acceptance criteria

- [ ] When Rule Agent sets `human_required=True`, workflow pauses before returning final response; interactive mode prompts reviewer and waits for input.
- [ ] Context package includes query, errors, failure history summary, and learner suggestions (when present) in structured JSON and human-readable console output.
- [ ] `modify_query` decision with `override_query` causes workflow to re-enter QueryValidator with the new URL on resume.
- [ ] All human decisions are recorded in audit trail with timestamp and decision type; human decision overrides conflicting learner suggestions.
- [ ] ≥99% unit test coverage; integration test demonstrates pause → review → resume path (non-interactive mock human provider).

## Out of scope

- Web admin UI, email/Slack notifications, or ticket system integration.
- Role-based access control for different reviewer permission levels.
- Production operator auth (`FHIR_HUMAN_GATE_REQUIRE_AUTH`) — covered in task 018.

## Log
### [PA] 2026-07-03 — Grooming
Initial task from /squid-plan on specs/fhir-query-validator-factory.md.