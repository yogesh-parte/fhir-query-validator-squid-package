---
id: 009-rule-agent
feature: fhir-validator
status: done
---

# Rule Agent

## Scope

Implement `src/agentic_layer/agents/rule_agent.py` per `docs/spec/rule-and-learner-spec.md`: monitor validation failures per `user_id` + `server_key`, detect sliding-window patterns, and decide escalation to Search Learner or HumanInterventionGate.

**Deliverables:**
- `RuleAgent` class with `record_failure(user_id, query_url, validation_errors, server_key, timestamp) -> RuleAgentOutput`
- In-memory sliding-window store keyed by `(user_id, server_key)` with configurable thresholds from settings (task 002)
- Escalation policy: ≥3 failures in 10 minutes → `escalation_decision=learner`; ≥5 failures in 15 minutes OR any `high_severity` error → `escalation_decision=human`
- Output fields: `pattern_detected`, `failure_count_window`, `learner_activated`, `human_required`, full `audit` block
- Rate-limit learner activation to prevent spam on burst failures
- Unit tests at threshold boundaries (2 vs 3 vs 5 failures), window expiry, high-severity fast-path, cross-server isolation
- State store interface allowing future Redis swap without API change

Depends on tasks 001, 002.

## Acceptance criteria

- [ ] Exactly 3 failures within 10 minutes for the same `user_id`/`server_key` sets `escalation_decision=learner` and `learner_activated=True`; 2 failures yields `escalation_decision=none`.
- [ ] 5 failures within 15 minutes OR a single `high_severity` validation error sets `escalation_decision=human` and `human_required=True`.
- [ ] Failures from different `server_key` values for the same `user_id` are tracked independently; window entries expire after configured minutes.
- [ ] Thresholds `LEARNER_THRESHOLD_FAILURES`, `LEARNER_WINDOW_MINUTES`, `HUMAN_THRESHOLD_FAILURES`, `HUMAN_WINDOW_MINUTES` are read from settings without code changes.
- [ ] ≥99% unit test coverage including boundary and edge cases; all decisions produce auditable `audit` records per `docs/traceability.md`.

## Out of scope

- Search Learner suggestion generation (task 010).
- Human gate UI and pause/resume mechanics (task 011).
- Long-term cross-session learner memory or persistent failure databases.

## Log
### [PA] 2026-07-03 — Grooming
Initial task from /squid-plan on specs/fhir-query-validator-factory.md.