#!/usr/bin/env python3
"""
demo_loops.py
Demonstration script showing the feedback loops in action.
"""

from __future__ import annotations

from _demo_utils import (
    add_project_root_to_path,
    print_scenario_header,
    reset_workflow_singletons,
    summarize_final_output,
)

add_project_root_to_path()

from src.agentic_layer.graph.validation_workflow import run_validation_workflow


def run_scenario(
    name: str,
    query_url: str,
    user_id: str,
    mode: str = "validate_and_execute",
) -> dict:
    print_scenario_header(
        name,
        query_url=query_url,
        server_key="hapi",
        user_id=user_id,
        mode=mode,
    )

    result = run_validation_workflow({
        "query_url": query_url,
        "server_key": "hapi",
        "user_id": user_id,
        "mode": mode,
    })

    summarize_final_output(result["final_output"])

    if result.get("learner_guidance"):
        print(f"\nLearner Guidance: {result['learner_guidance']['message']}")
        print(f"Suggestion       : {result['learner_guidance']['suggestion']}")

    print("=" * 78 + "\n")
    return result


if __name__ == "__main__":
    print("FHIR Query Validator Factory - Loop Engineering Demo\n")

    reset_workflow_singletons()
    run_scenario(
        name="Normal Valid Query",
        query_url="Patient?gender=male",
        user_id="user-alice",
    )

    invalid_query = "Patient?invalid_param=true"
    last = None
    for attempt in range(1, 4):
        last = run_scenario(
            name=f"Repeated Invalid Queries — Attempt {attempt}/3",
            query_url=invalid_query,
            user_id="user-bob",
            mode="validate_only",
        )

    if last and last["final_output"].get("escalation") == "learner":
        print("✓ Learner escalation loop triggered\n")

    print("Demo completed. Check the loop messages above to see feedback in action.")