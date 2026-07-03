"""
demo_traceability.py
Demonstrates agent traceability and observability.

Features:
- Clean structured trace output
- Optional Langfuse integration
"""

from datetime import datetime

from _demo_utils import add_project_root_to_path

add_project_root_to_path()

from src.agentic_layer.graph.validation_workflow import run_validation_workflow


def format_trace(state: dict) -> str:
    """Return a clean, readable traceability report."""
    final = state.get("final_output", {})

    lines = []
    lines.append("=" * 85)
    lines.append("                    AGENT TRACEABILITY REPORT")
    lines.append("=" * 85)
    lines.append(f" Timestamp   : {datetime.now().isoformat()}")
    lines.append(f" Query       : {state.get('query_url')}")
    lines.append(f" User        : {state.get('user_id', 'N/A')}")
    lines.append(f" Server      : {state.get('server_key', 'default')}")
    lines.append("-" * 85)

    lines.append(f"\n [VALIDATION] Valid                 : {final.get('valid')}")
    lines.append(f" [VALIDATION] Errors                : {final.get('errors', [])}")
    lines.append(f" [PATTERN]    Detected              : {final.get('pattern_detected')}")
    lines.append(f" [ESCALATION] Decision              : {final.get('escalation')}")
    lines.append(f" [EXECUTION]  Performed             : {final.get('executed')}")
    lines.append(f" [EXECUTION]  Server Used           : {final.get('server_used')}")
    lines.append(f" [HUMAN]      Review Required       : {final.get('human_review_required')}")

    if final.get("guidance"):
        lines.append("\n [LEARNER]")
        lines.append(f"   Message    : {final['guidance'].get('message')}")
        lines.append(f"   Suggestion : {final['guidance'].get('suggestion')}")

    if final.get("human_review_required"):
        lines.append("\n [HUMAN INTERVENTION] Case escalated for human review.")

    lines.append("\n" + "=" * 85)
    lines.append(" END OF TRACE")
    lines.append("=" * 85)

    return "\n".join(lines)


def run_trace_demo():
    print("\n=== Agent Traceability Demo ===\n")

    # Scenario 1: Normal flow
    state1 = {
        "query_url": "Patient?gender=male",
        "server_key": "hapi",
        "user_id": "user-alice",
        "mode": "validate_and_execute"
    }
    print("SCENARIO 1: Normal Valid Query")
    result1 = run_validation_workflow(state1)
    print(format_trace(result1))

    # Scenario 2: Repeated invalid queries to trigger meta loop
    print("\nSCENARIO 2: Repeated Invalid Queries (Triggering Pattern Detection)")
    for i in range(1, 4):
        print(f"\n--- Attempt #{i} ---")
        state2 = {
            "query_url": "Patient?invalid_param=true",
            "server_key": "hapi",
            "user_id": "user-bob",
            "mode": "validate_and_execute"
        }
        result2 = run_validation_workflow(state2)
        print(format_trace(result2))


if __name__ == "__main__":
    run_trace_demo()


# =============================================================================
# Optional: Langfuse Integration
# =============================================================================
"""
To enable Langfuse for production-grade tracing:

1. Install:
   pip install langfuse

2. Set environment variables:
   export LANGFUSE_PUBLIC_KEY=pk_...
   export LANGFUSE_SECRET_KEY=sk_...
   export LANGFUSE_HOST=https://cloud.langfuse.com

3. Wrap workflow calls:

from langfuse import Langfuse
langfuse = Langfuse()

with langfuse.trace(name="fhir-validation-workflow", user_id=state.get("user_id")) as trace:
    result = run_validation_workflow(state)
    trace.update(
        input={"query": state["query_url"]},
        output=result.get("final_output"),
        metadata={"server": state.get("server_key")}
    )
"""
