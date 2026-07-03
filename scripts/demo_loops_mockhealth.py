#!/usr/bin/env python3
"""
demo_loops_mockhealth.py
Loop-engineering demo against the mock.health authenticated FHIR sandbox.

Exercises the same feedback loops as demo_loops.py, but targets:
  server_key: mockhealth
  base URL:   https://api.mock.health/fhir

Requires MOCK_HEALTH_API_KEY in .env.local (loaded automatically via python-dotenv).

Usage:
    python3 scripts/demo_loops_mockhealth.py
    python3 scripts/demo_loops_mockhealth.py --mode validate_only
"""

from __future__ import annotations

import argparse
import os

from _demo_utils import (
    add_project_root_to_path,
    mockhealth_api_key,
    print_scenario_header,
    require_mockhealth_key,
    reset_workflow_singletons,
    summarize_final_output,
)

add_project_root_to_path()

from src.agentic_layer.graph.validation_workflow import run_validation_workflow

SERVER_KEY = "mockhealth"
DEFAULT_QUERY = "Patient?_count=1"


def run_scenario(
    name: str,
    query_url: str,
    user_id: str,
    mode: str = "validate_and_execute",
) -> dict:
    print_scenario_header(
        name,
        query_url=query_url,
        server_key=SERVER_KEY,
        user_id=user_id,
        mode=mode,
    )

    result = run_validation_workflow({
        "query_url": query_url,
        "server_key": SERVER_KEY,
        "user_id": user_id,
        "mode": mode,
    })

    summarize_final_output(result["final_output"])

    if result.get("learner_guidance"):
        print(f"\nLearner Guidance: {result['learner_guidance']['message']}")
        print(f"Suggestion       : {result['learner_guidance']['suggestion']}")
        print(f"Example          : {result['learner_guidance']['example']}")

    if result["final_output"].get("human_review_required"):
        review = result["final_output"].get("human_review") or {}
        print(f"\nHuman Review     : severity={review.get('severity')} id={review.get('review_id')}")

    print("=" * 78 + "\n")
    return result


def run_demo(default_mode: str) -> None:
    require_mockhealth_key()
    print("FHIR Query Validator Factory — mock.health Loop Demo\n")
    print(f"Server     : {SERVER_KEY} → https://api.mock.health/fhir")
    print("API Key    : (set) (from MOCK_HEALTH_API_KEY)")
    print(f"Auth scope : Bearer token forwarded to cache + execution agents")
    print(f"Env file   : .env.local loaded={os.path.exists('.env.local')}\n")

    reset_workflow_singletons()
    run_scenario(
        name="Valid Query (Cache → Validate → Execute)",
        query_url=DEFAULT_QUERY,
        user_id="mockhealth-user-valid",
        mode=default_mode,
    )

    reset_workflow_singletons()
    run_scenario(
        name="Validate Only (Execution Loop Skipped)",
        query_url=DEFAULT_QUERY,
        user_id="mockhealth-user-validate-only",
        mode="validate_only",
    )

    reset_workflow_singletons()
    invalid_query = "Patient?invalid_param=true"
    last = None
    for attempt in range(1, 4):
        last = run_scenario(
            name=f"Repeated Invalid Queries — Attempt {attempt}/3 (Learner Threshold)",
            query_url=invalid_query,
            user_id="mockhealth-user-learner",
            mode="validate_only",
        )

    if last and last["final_output"].get("escalation") == "learner":
        print("✓ Learner escalation loop triggered on mock.health\n")

    reset_workflow_singletons()
    print("Optional: run with a fresh user to observe cache HIT on second valid query.")
    run_scenario(
        name="Cache Warm-up",
        query_url=DEFAULT_QUERY,
        user_id="mockhealth-user-cache-a",
        mode="validate_only",
    )
    run_scenario(
        name="Cache Reuse (conditional refresh)",
        query_url=DEFAULT_QUERY,
        user_id="mockhealth-user-cache-b",
        mode="validate_only",
    )

    print("Demo completed. mock.health loops exercised:")
    print("  • Cache invalidation (auth-scoped key)")
    print("  • Validation → execution gating")
    print("  • Pattern detection → learner escalation")


def main() -> None:
    parser = argparse.ArgumentParser(description="Loop demo for mock.health FHIR sandbox.")
    parser.add_argument(
        "--mode",
        default="validate_and_execute",
        choices=["validate_only", "validate_and_execute"],
        help="Default workflow mode for the valid-query scenario",
    )
    args = parser.parse_args()
    run_demo(args.mode)


if __name__ == "__main__":
    main()