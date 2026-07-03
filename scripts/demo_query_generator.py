#!/usr/bin/env python3
"""
demo_query_generator.py
Demonstrate QueryGeneratorAgent and optional workflow integration.

Generates FHIR search queries from standard build.fhir.org search parameters,
then optionally runs the validation workflow on the generated query.

Usage:
    python3 scripts/demo_query_generator.py
    python3 scripts/demo_query_generator.py --resource Observation --status final --run
"""

from __future__ import annotations

import argparse
import json

from _demo_utils import add_project_root_to_path, summarize_final_output

add_project_root_to_path()

from src.agentic_layer.agents.query_generator_agent import QueryGeneratorAgent
from src.agentic_layer.graph.validation_workflow import run_validation_workflow


def main() -> None:
    parser = argparse.ArgumentParser(description="FHIR query generator demo")
    parser.add_argument("--resource", default="Patient", help="FHIR resource type")
    parser.add_argument("--gender", help="Patient gender criterion (token)")
    parser.add_argument("--status", help="Status criterion (Observation, Encounter, etc.)")
    parser.add_argument("--intent", help="Built-in intent template (e.g. 'male patients')")
    parser.add_argument("--count", type=int, default=10, help="_count paging parameter")
    parser.add_argument("--list-resources", action="store_true", help="List known resource types")
    parser.add_argument("--describe", action="store_true", help="Show standard search params")
    parser.add_argument("--run", action="store_true", help="Run validation workflow on result")
    parser.add_argument("--server", default="hapi", help="server_key for workflow run")
    args = parser.parse_args()

    agent = QueryGeneratorAgent()

    if args.list_resources:
        print(json.dumps(agent.list_resources(), indent=2))
        return

    if args.describe:
        print(json.dumps(agent.describe_resource(args.resource), indent=2))
        return

    if args.intent:
        generated = agent.generate_from_intent(args.resource, args.intent)
    else:
        criteria: dict[str, object] = {}
        if args.gender:
            criteria["gender"] = args.gender
        if args.status:
            criteria["status"] = args.status
        generated = agent.generate(args.resource, criteria, count=args.count)

    print("\n=== QueryGeneratorAgent ===")
    print(json.dumps(generated, indent=2))

    if not generated.get("generated"):
        return

    if not args.run:
        print("\nRe-run with --run to validate/execute the generated query on a FHIR server.")
        return

    print("\n=== Validation Workflow ===")
    result = run_validation_workflow({
        "query_url": generated["query_url"],
        "server_key": args.server,
        "mode": "validate_and_execute",
    })
    summarize_final_output(result["final_output"])


if __name__ == "__main__":
    main()