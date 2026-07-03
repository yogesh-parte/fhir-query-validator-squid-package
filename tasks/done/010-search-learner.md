---
id: 010-search-learner
feature: fhir-validator
status: done
---

# Search Learner Agent

## Scope

Implement `src/agentic_layer/agents/search_learner.py` per `docs/spec/rule-and-learner-spec.md` and ADR-002: rule-based heuristic suggestions (no LLM required) when Rule Agent activates learner escalation.

**Deliverables:**
- `SearchLearnerAgent` class with `suggest(user_id, query_url, validation_errors, capability_index, failure_history) -> SearchLearnerOutput`
- Heuristics: parameter casing fixes (`birthdate` → `birthDate`), common FHIR param synonyms, unsupported modifier removal, comparator corrections for date/number types
- Compare errors against `CapabilityIndex` to propose 1–3 corrected `suggested_queries` URLs
- Fields: `explanation`, `suggested_queries`, `learning_notes`, `confidence` (0.0–1.0 heuristic score)
- Fallback generic guidance when no high-confidence suggestion possible; flag for human review in audit
- Unit tests with ≥80% of fixture cases producing at least one improved suggestion (per spec acceptance criteria)
- No sensitive user data or tokens in explanations

Depends on tasks 001, 006, 009.

## Acceptance criteria

- [ ] For `Patient?birthdate=ge1990-01-01` against HAPI index, learner returns explanation mentioning camelCase and at least one corrected URL with `birthDate`.
- [ ] `confidence` reflects heuristic match strength; low-confidence cases still return `explanation` but may have empty `suggested_queries` and audit flag `fallback=True`.
- [ ] Learner produces actionable explanations with ≥1 improved query suggestion in ≥80% of curated unit-test failure scenarios.
- [ ] Output matches `SearchLearnerOutput` entity; no PHI, tokens, or API keys appear in `explanation` or `learning_notes`.
- [ ] ≥99% unit test coverage on learner heuristics; integration test triggered via Rule Agent threshold in workflow context (task 012).

## Out of scope

- LLM/Gemini-powered suggestions or RAG over documentation.
- Storing and reusing suggestions across sessions (long-term memory).
- Auto-retry of suggested queries without explicit workflow re-entry.

## Log
### [PA] 2026-07-03 — Grooming
Initial task from /squid-plan on specs/fhir-query-validator-factory.md.