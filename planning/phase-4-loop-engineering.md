# Phase 4: Loop Engineering & Advanced Agents

**Phase Duration (Estimated):** 2–3 hours  
**Focus:** Completing feedback loops and advanced specialist agents  
**Status:** Complete

## 1. Objectives

- Implement the QueryExecution Agent to complete the operational loop
- Add pattern detection capabilities to the QueryValidator
- Implement Rule Agent for intelligent escalation
- Implement Search Learner Agent for user guidance
- Add Human Intervention Gate with proper controls
- Wire all feedback loops into the ADK graph workflow
- Ensure observability across the full system

## 2. Scope of This Phase

**In Scope:**
- `QueryExecution Agent` (execute validated queries, handle authentication)
- Pattern detection logic in QueryValidator
- `Rule Agent` – decides between learner vs human escalation
- `Search Learner Agent` – provides helpful explanations and suggestions
- Human Intervention Gate (pause, notify, resume)
- Full graph workflow with conditional routing for all loops
- Enhanced logging and tracing for feedback loops

**Out of Scope:**
- Advanced OAuth2 token refresh mechanisms (basic support only)
- Persistent storage for pattern history (in-memory is acceptable for demo)
- Production-grade security hardening

## 3. Planned Activities

### 3.1 QueryExecution Agent
- Implement execution of validated FHIR search queries
- Support public servers and authenticated servers (Bearer token)
- Handle successful responses and different error types
- Return structured results or error information
- Add execution timing and logging

### 3.2 Pattern Detection (in QueryValidator)
- Track invalid queries per user/session over a time window
- Detect repeated patterns (same error type, same parameter issues, etc.)
- Signal pattern detection to Rule Agent

### 3.3 Rule Agent
- Evaluate pattern detection signals
- Decide escalation path:
  - Activate Search Learner Agent
  - Trigger Human Intervention Gate
- Log decision rationale for auditability

### 3.4 Search Learner Agent
- Generate user-friendly explanations for repeated errors
- Suggest corrected query examples based on CapabilityStatement
- Log recurring issues for potential future improvement

### 3.5 Human Intervention Gate
- Pause automated processing for affected user/session
- Create structured context for human review
- Support human decision options (continue, restrict, update rules, etc.)
- Log all human interventions with rationale

### 3.6 Full Workflow Integration
- Update ADK graph workflow with all conditional edges
- Ensure proper state management across agents
- Add comprehensive logging for the entire loop

### 3.7 Testing & Demo Scenarios
- Test repeated invalid query scenarios
- Test successful validation + execution flow
- Test human escalation path (simulated)
- Create demo notebook or script showcasing the full loops

## 4. Key Deliverables

| Deliverable                              | Location                                           | Priority |
|------------------------------------------|----------------------------------------------------|----------|
| `QueryExecution Agent`                   | `src/agentic_layer/agents/query_execution.py`      | High     |
| Pattern detection logic                  | Inside `QueryValidator Agent`                      | High     |
| `Rule Agent`                             | `src/agentic_layer/agents/rule_agent.py`           | High     |
| `Search Learner Agent`                   | `src/agentic_layer/agents/search_learner_agent.py` | High     |
| Human Intervention Gate logic            | `src/agentic_layer/agents/human_gate.py`           | High     |
| Updated full graph workflow              | `src/agentic_layer/graph/validation_workflow.py`   | High     |
| Demo showcasing feedback loops           | `examples/notebooks/` or `scripts/`                | Medium   |
| Updated Phase 4 planning notes           | This file                                          | Low      |

## 5. Dependencies

- Phase 3 deliverables (core agents + basic workflow)
- `docs/spec/query-execution-spec.md`
- `docs/spec/rule-and-learner-spec.md`
- `docs/spec/human-intervention-spec.md`
- Completed architecture from Phase 2

## 6. Risks & Mitigations

| Risk                                           | Mitigation |
|------------------------------------------------|----------|
| Pattern detection logic becoming too complex   | Start simple (count-based + time window) |
| Human Intervention Gate implementation         | Keep it simple (logging + pause flag) for demo purposes |
| State management across multiple agents        | Leverage ADK state management capabilities |
| Over-engineering the learner responses         | Keep suggestions practical and grounded in CapabilityStatement |

## 7. Success Criteria

- [x] QueryExecution Agent successfully executes validated queries on public servers
- [x] Pattern detection correctly identifies repeated invalid queries from the same user
- [x] Rule Agent makes appropriate escalation decisions
- [x] Search Learner Agent provides helpful, relevant suggestions
- [x] Human Intervention Gate can be triggered and logged
- [x] Full end-to-end flow with feedback loops works in a demo

## 8. Alignment with Software Factory

This phase is critical for demonstrating **loop engineering** — one of the core ideas of the Software Factory approach. It shows how the system can self-correct and escalate intelligently while maintaining human oversight.

## 9. Outcomes & Next Steps

**Expected Outcomes:**
- Complete operational loop (Validate → Execute)
- Intelligent feedback and learning loops
- Responsible AI patterns (human gate when needed)
- Strong demonstration of the Software Factory methodology

**Next Steps after Phase 4:**
- ~~Move to **Phase 5**~~ → **Completed** — see [`phase-5-demo-hardening-and-governance.md`](phase-5-demo-hardening-and-governance.md)

## 10. Post-phase outcomes (2026-06-30)

Delivered beyond original Phase 4 scope (see Phase 5):

- Google ADK CLI/Web demos (`demo_adk_cli.py`, `demo_adk_web.py`, `fhir_validator_agent/`)
- Agent traceability and mock.health loop demos
- OWASP security review + opt-in hardening (URL safety, operator auth, workflow isolation)
- 148 tests; ~99% unit coverage on `src/agentic_layer`
- CI security workflow (Bandit + pip-audit)

Original Phase 4 out-of-scope item *“Production-grade security hardening”* was addressed in Phase 5 as **opt-in** controls preserving demo defaults.

---

**Phase 4 Complete**