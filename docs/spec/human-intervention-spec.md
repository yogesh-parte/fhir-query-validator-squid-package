# Spec: HumanInterventionGate

**Status:** Ready for Implementation  
**Version:** 0.3  
**Last Updated:** 2026-07-02  
**Owner:** Yogesh  
**Related ADRs:** ADR-001  
**Related Specs:** `rule-and-learner-spec.md`, `query-validation-spec.md`

## 1. Overview

The **HumanInterventionGate** provides the final safety net in the agentic workflow. When the `Rule Agent` determines that human review is required (based on escalation thresholds or high-severity issues), this component pauses the automated flow, surfaces context to a human, and allows resume or override decisions.

It is a critical component for responsible AI in healthcare, ensuring high-stakes or repeated-failure scenarios receive human oversight.

## 2. Goals

- Implement configurable, explicit human escalation gates.
- Provide rich, actionable context to the human reviewer (query, errors, history, learner suggestions).
- Support "pause → review → resume/override" workflow (as demonstrated in original `demo_agent_traceability.py`).
- Maintain complete audit trail of human decisions.
- Keep the gate non-blocking for low-risk paths.
- Be usable in both CLI demos and future web/admin interfaces.

## 3. Inputs (when triggered)

| Input                    | Type    | Description                                      | Required |
|--------------------------|---------|--------------------------------------------------|----------|
| user_id                  | string  | User triggering the pattern                      | Yes      |
| failing_query            | string  | The query that caused escalation                 | Yes      |
| failure_history          | list    | Recent failures with timestamps and errors       | Yes      |
| learner_suggestions      | object  | Output from Search Learner Agent (if any)        | No       |
| escalation_reason        | string  | "threshold_exceeded" \| "high_severity" \| "manual" | Yes   |
| correlation_id           | string  | For tracing the request                          | Yes      |

## 4. Outputs / Decisions

```json
{
  "human_decision": "approve" | "reject" | "modify_query" | "escalate_further",
  "override_query": "new query url (optional)",
  "human_notes": "Free text explanation from reviewer",
  "resume_workflow": true,
  "audit": {
    "reviewed_by": "human@domain.com",
    "reviewed_at": "2026-07-02T18:45:00Z",
    "decision": "..."
  }
}
```

## 5. Core Behavior

1. Receive escalation trigger from `Rule Agent`.
2. Assemble rich context package (query, errors, history, learner suggestions, CapabilityStatement excerpt).
3. **Pause** the automated workflow.
4. Surface context to human (in current implementation: console / structured output + optional JSON export).
5. Wait for human input:
   - Approve & resume
   - Reject / block
   - Modify query and re-validate
   - Escalate further (e.g., create ticket)
6. Record decision with identity, timestamp, and reasoning.
7. Resume or terminate the workflow accordingly.
8. Feed decision back into `Rule Agent` / learner for future improvement.

## 6. Feedback Loops & Learning

- Human decisions are logged and can be used to improve threshold tuning and learner quality over time.
- Approved queries after human review can be treated as high-confidence examples.
- Rejected patterns help refine validation rules.

## 7. Edge Cases & Error Handling

- Human unavailable (timeout) → configurable fallback (auto-approve low-risk, or queue for later review).
- Conflicting learner suggestion vs human decision → human decision always wins; log the conflict.
- Very long failure history → summarize for human (top 5 + count).

## 8. Acceptance Criteria

- Correctly pauses workflow when `Rule Agent` requests human escalation.
- Presents clear, actionable context to the reviewer.
- Supports pause → review → resume workflow in demo scripts.
- All human decisions are fully audited and traceable.
- Human can override with a modified query that then re-enters validation.
- Works in both automated demo mode and interactive mode.
- Thresholds and behavior are configurable via environment/settings.
- No sensitive patient data is exposed in human context views.

## 9. Open Questions

- Preferred notification channel for pending human reviews in production (email, Slack, dashboard)?
- Should we support role-based access (different humans have different override powers)?
- How to handle concurrent escalations from the same user?

---
