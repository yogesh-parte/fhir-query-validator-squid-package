# Agent Traceability & Observability

This document explains how traceability is implemented in the `fhir-query-validator-factory` demonstration.

## Why Traceability Matters

In agentic systems, especially those demonstrating **Software Factory** principles, it is important to understand:
- Which agent made which decision
- Which feedback loops were triggered
- When and why escalation to a human occurred

Good traceability improves debugging, auditing, and demonstration value.

## Current Implementation

### 1. Structured Logging (Default)

The system uses clear `print` statements throughout the workflow and agents to show:

- When each agent is invoked
- Cache hits/misses/expirations
- Validation results
- Pattern detection
- Escalation decisions (Learner vs Human)

Run the traceability demos to see this in action:

```bash
python3 scripts/demo_traceability.py
python3 scripts/demo_agent_traceability.py
python3 scripts/demo_agent_traceability.py --server mockhealth --export traces.json
python3 scripts/demo_adk_cli.py --scenario valid   # ADK graph node paths via JSONL
python3 scripts/demo_adk_web.py --api-only --port 8080   # against a running adk web server
```

### 2. Trace Report

The `demo_traceability.py` script generates a clean, human-readable report after each workflow execution, showing:

- Final validation result
- Whether a pattern was detected
- Escalation decision
- Learner guidance (if triggered)
- Human review requirement

`demo_agent_traceability.py` extends this with a **per-agent pipeline trace** (CacheAgent through HumanInterventionGate), **audit trail** entries from `RuleAgent` and `HumanInterventionGate`, and a **human pause → review → resume** scenario. Use `--export` to write a JSON trace bundle for presentations.

### 3. Optional: Langfuse Integration

For production-grade observability, **Langfuse** can be used.

**Benefits of Langfuse:**
- Automatic span/trace collection
- Visualization of agent calls and loops
- Cost tracking (if using LLM calls)
- User-level analytics
- Scoring and evaluation

**How to Enable:**

```bash
pip install langfuse
```

Set environment variables:

```bash
export LANGFUSE_PUBLIC_KEY=pk_...
export LANGFUSE_SECRET_KEY=sk_...
export LANGFUSE_HOST=https://cloud.langfuse.com
```

Then wrap workflow calls as shown in `scripts/demo_traceability.py`.

## Recommended Observability Levels

| Level              | Tool          | Use Case                              | Recommended For |
|--------------------|---------------|---------------------------------------|-----------------|
| Basic              | Print logs    | Local development & demos             | Default         |
| Structured         | `demo_traceability.py` | Clear demo reports                 | Presentations   |
| Production         | Langfuse      | Full tracing, analytics, evaluation   | Real deployments|

## Future Improvements

- Add Langfuse as a first-class optional dependency
- Instrument all agents with Langfuse spans
- Add custom scores (e.g., "escalation quality", "loop efficiency")

---

This traceability layer supports the **Software Factory** goal of building observable, governable agentic systems.
