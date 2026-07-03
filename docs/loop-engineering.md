# Loop Engineering Documentation

This document explains the explicit feedback loops implemented in the `fhir-query-validator-factory` demonstration.

## Overview

One of the core ideas of the **Software Factory** approach is **loop engineering** — deliberately designing feedback loops so the system can self-correct, learn, and escalate when necessary.

## Implemented Loops

### 1. Cache Invalidation Loop

**Agents Involved:** `CacheAgent`

**Description:**
- The `CacheAgent` fetches the `CapabilityStatement` and stores it with a timestamp.
- On subsequent requests, it checks if the cache is still valid (TTL-based, default 7 days).
- Within TTL, it sends conditional requests using `If-None-Match` (ETag); a `304 Not Modified` response reuses the cached statement.
- If TTL expires or the server returns new content, the cache is refreshed.
- Auth-scoped cache keys prevent cross-tenant leakage (e.g. `mockhealth` with `MOCK_HEALTH_API_KEY`).
- Future enhancement: `If-Modified-Since` / `Last-Modified` conditional requests.

**Goal:** Reduce unnecessary network calls while keeping data reasonably fresh.

---

### 2. Validation → Execution Loop

**Agents Involved:** `QueryValidatorAgent` → `QueryExecutionAgent`

**Description:**
- A query is only executed if it passes validation.
- This prevents wasteful or potentially harmful queries from reaching the FHIR server.

**Goal:** Ensure safety and efficiency by gating execution behind validation.

---

### 3. Pattern Detection → Learning / Human Escalation Loop (Meta Loop)

**Agents Involved:** 
- `QueryValidatorAgent` (pattern detection)
- `RuleAgent` (decision making)
- `SearchLearnerAgent` or `HumanInterventionGate`

**Description:**
This is the most important loop for demonstrating intelligent behavior:

1. `QueryValidatorAgent` tracks invalid queries per user (keyed by `user_id` + `server_key`).
2. If repeated invalid patterns are detected, it sets `pattern_detected = True` when the learner threshold is met.
3. `RuleAgent` evaluates the situation and decides:
   - **"learner"** → Activate `SearchLearnerAgent` when **3+ invalid queries within 10 minutes** (see `LEARNER_THRESHOLD` in `query_validator.py`).
   - **"human"** → Trigger `HumanInterventionGate` when **5+ invalid queries within 15 minutes**, on **high-severity** validation concerns, or when abuse heuristics fire (see `HUMAN_THRESHOLD` in `query_validator.py` and `rule_agent.py`).
4. The system either helps the user improve or escalates to a human.

**Goal:** 
- Reduce repeated failures through guidance.
- Maintain responsible AI behavior via human oversight when automation is insufficient.
- Demonstrate self-improving / meta-feedback capabilities.

---

### Summary of Loop Engineering

| Loop Name                        | Type          | Agents Involved                     | Purpose                              | Intelligence Level |
|----------------------------------|---------------|-------------------------------------|--------------------------------------|--------------------|
| Cache Invalidation               | Operational   | CacheAgent                          | Performance & freshness              | Low                |
| Validation → Execution           | Safety        | QueryValidator + QueryExecution     | Prevent invalid execution            | Medium             |
| Pattern → Learner / Human        | Meta / Learning | QueryValidator + Rule + Learner/Human | Self-correction + responsible AI   | High               |

These loops are orchestrated in `src/agentic_layer/graph/workflow_engine.py` and exposed via:

- `run_validation_workflow()` — synchronous entry point for demos and tests
- Google ADK `root_agent` — linear graph (`initialize` → `run_validation_pipeline` → `finalize`) that delegates to the same engine

Run `python3 scripts/demo_loops.py` or `python3 scripts/demo_adk_cli.py` to observe loop output in the terminal.

---

This document serves as evidence of deliberate **loop engineering** in the Software Factory demonstration.
