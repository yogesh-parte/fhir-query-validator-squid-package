# Spec: Rule Agent + Search Learner Agent

**Status:** Ready for Implementation  
**Version:** 0.3  
**Last Updated:** 2026-07-02  
**Owner:** Yogesh  
**Related ADRs:** ADR-001  
**Related Specs:** `query-validation-spec.md`, `human-intervention-spec.md`

## 1. Overview

The **Rule Agent** and **Search Learner Agent** work together to detect repeated invalid query patterns and decide on intelligent escalation.

- **Rule Agent**: Monitors validation failures, identifies patterns from the same `user_id`, and decides whether to activate the learner or escalate to a human.
- **Search Learner Agent**: Analyzes the failure pattern, explains the likely mistake to the user, and suggests corrected queries or better search approaches.

Together they close the feedback loop that turns repeated errors into learning and controlled human oversight.

## 2. Goals

- Prevent silent repeated failures by detecting patterns early.
- Provide helpful, context-aware guidance instead of generic error messages.
- Escalate to humans only when necessary (configurable thresholds).
- Maintain full auditability of escalation decisions and learner suggestions.
- Improve overall query success rate over time through pattern learning.

## 3. Inputs (to Rule Agent)

| Input              | Type   | Description                                      | Required |
|--------------------|--------|--------------------------------------------------|----------|
| user_id            | string | Identifier for pattern tracking                  | Yes      |
| query_url          | string | The failing query                                | Yes      |
| validation_errors  | list   | Structured errors from QueryValidator            | Yes      |
| timestamp          | string | ISO timestamp of the failure                     | Yes      |
| server_key         | string | Server on which failure occurred                 | Yes      |

## 4. Outputs

**Rule Agent Output**:
```json
{
  "pattern_detected": true,
  "failure_count_window": 4,
  "escalation_decision": "learner" | "human" | "none",
  "learner_activated": true,
  "human_required": false,
  "audit": { ... }
}
```

**Search Learner Agent Output** (when activated):
```json
{
  "explanation": "The parameter 'birthdate' is not supported on Patient for this server. Try 'birthDate' (camelCase) instead.",
  "suggested_queries": [
    "https://hapi.fhir.org/baseR4/Patient?birthDate=ge1990-01-01"
  ],
  "learning_notes": "Common mistake: incorrect parameter casing for this FHIR server.",
  "confidence": 0.85
}
```

## 5. Core Behavior

**Rule Agent**:
1. Receive failure event from QueryValidator or QueryExecution.
2. Record failure in short-term window store (per `user_id` + `server_key`).
3. Evaluate against thresholds:
   - ≥ 3 failures in last 10 minutes → activate learner.
   - ≥ 5 failures in last 15 minutes **or** high-severity error → escalate to human.
4. Emit structured decision + trigger appropriate downstream agent.

**Search Learner Agent** (triggered by Rule Agent):
1. Analyze recent failures for the user/server combination.
2. Compare against known common mistakes and CapabilityStatement.
3. Generate human-readable explanation + 1–3 corrected query suggestions.
4. Log the learning event for future improvement.

## 6. Feedback Loops & Escalation Policy

- Failures flow: QueryValidator → Rule Agent → (Learner or HumanInterventionGate)
- Learner suggestions flow back to QueryValidator for improved future validation.
- Human escalation triggers `human-intervention-spec.md` flow (pause/resume, review context).
- All decisions are recorded in the per-request audit trail (`docs/traceability.md`).

**Configurable Thresholds** (via `.env` or settings):
- `LEARNER_THRESHOLD_FAILURES=3`
- `LEARNER_WINDOW_MINUTES=10`
- `HUMAN_THRESHOLD_FAILURES=5`
- `HUMAN_WINDOW_MINUTES=15`

## 7. Edge Cases & Error Handling

- First failure for a user → no escalation.
- Very high volume of failures from one user → rate-limit learner calls.
- Learner unable to generate useful suggestion → fall back to generic guidance + human flag.
- Pattern detection across different `server_key` values.

## 8. Acceptance Criteria

- Correctly detects patterns and triggers learner at defined thresholds.
- Triggers human escalation at higher thresholds or on high-severity errors.
- Learner produces clear, actionable explanations and at least one improved query suggestion in ≥80% of test cases.
- All escalation decisions are fully traceable (who, when, why, what was suggested).
- Thresholds are configurable without code changes.
- Works consistently across public servers and mock.health.
- Unit + integration tests cover normal flow, edge cases, and threshold boundaries.
- No sensitive user data is logged in learner explanations.

## 9. Open Questions

- Should learner suggestions be stored and reused across sessions (long-term memory)?
- Preferred mechanism for human notification (stdout only for v1, or Slack/email later)?
- How should we handle conflicting suggestions from the learner vs. strict CapabilityStatement validation?

---
