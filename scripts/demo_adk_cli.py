#!/usr/bin/env python3
"""
demo_adk_cli.py
Showcase the FHIR Query Validator via Google ADK CLI (`adk run`).

Runs scripted scenarios through the ADK graph workflow agent and prints
node-level events plus spec-aligned final_output. Also prints instructions
for interactive CLI mode.

Usage:
    python3 scripts/demo_adk_cli.py
    python3 scripts/demo_adk_cli.py --scenario valid
    python3 scripts/demo_adk_cli.py --interactive-hint-only

Requirements:
    pip install google-adk
    Run from repository root.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from typing import Any

from _demo_utils import (
    HAPI_DEMO_SCENARIOS,
    adk_available,
    agent_dir,
    parse_adk_events,
    project_root,
    require_adk,
    reset_workflow_singletons,
    summarize_final_output,
)

AGENT_FOLDER = "fhir_validator_agent"


def run_adk_subprocess(name: str, config: dict[str, Any]) -> None:
    state = {**config["state"], "user_id": config["state"].get("user_id", f"adk-cli-{name}")}
    title = config["title"]

    print("\n" + "=" * 78)
    print(f"ADK CLI SCENARIO: {name} — {title}")
    print("=" * 78)
    print(f"Agent      : {AGENT_FOLDER}")
    print(f"State      : {json.dumps(state)}")
    print("-" * 78)

    cmd = [
        "adk",
        "run",
        AGENT_FOLDER,
        "--state",
        json.dumps(state),
        "--jsonl",
        "run",
    ]

    result = subprocess.run(
        cmd,
        cwd=project_root(),
        capture_output=True,
        text=True,
    )

    if result.returncode != 0 and not result.stdout.strip():
        print(result.stderr or "adk run failed")
        sys.exit(result.returncode)

    summary = parse_adk_events(result.stdout)
    _print_run_summary(summary, result.stderr)


def run_learner_in_process(name: str, config: dict[str, Any]) -> None:
    """
    Learner escalation needs in-process pattern history.
    Each `adk run` subprocess starts with a fresh validator singleton.
    """
    from src.agentic_layer.graph.validation_workflow import run_validation_workflow

    repeat = config.get("repeat", 3)
    base_state = {
        **config["state"],
        "user_id": config["state"].get("user_id", "adk-cli-learner"),
    }

    print("\n" + "=" * 78)
    print(f"IN-PROCESS SCENARIO: {name} — {config['title']}")
    print("=" * 78)
    print("Note: learner escalation accumulates pattern history in-process.")
    print("      `adk run` subprocesses do not share validator state.")
    print(f"Entry point: run_validation_workflow() × {repeat}")
    print("-" * 78)

    reset_workflow_singletons()
    last: dict[str, Any] | None = None
    for attempt in range(1, repeat + 1):
        print(f"\n--- Attempt {attempt}/{repeat} ---")
        last = run_validation_workflow(base_state)
        summarize_final_output(last["final_output"])

    if last and last["final_output"].get("escalation") == "learner":
        guidance = last.get("learner_guidance") or {}
        if guidance:
            print(f"\nLearner suggestion: {guidance.get('suggestion', guidance.get('message', ''))}")

    print("=" * 78)


def _print_run_summary(summary: dict[str, Any], stderr: str) -> None:
    if summary["node_paths"]:
        print("\n--- ADK GRAPH NODES ---")
        for path in summary["node_paths"]:
            print(f"  • {path}")

    if summary["errors"]:
        print("\n--- ADK ERRORS ---")
        for err in summary["errors"]:
            print(f"  • {err}")

    if summary["final_output"]:
        summarize_final_output(summary["final_output"])
    else:
        print("\nNo final_output found in ADK events (check stderr logs).")
        if stderr:
            print(stderr[-500:])

    print("=" * 78)


def print_interactive_instructions() -> None:
    print("\n" + "=" * 78)
    print("INTERACTIVE ADK CLI")
    print("=" * 78)
    print("Launch the agent in interactive mode:")
    print(f"  cd {project_root()}")
    print(f"  adk run {AGENT_FOLDER}")
    print()
    print("One-shot run with workflow state (JSON):")
    print(
        "  adk run fhir_validator_agent "
        '--state \'{"query_url":"Patient?gender=male","server_key":"hapi",'
        '"mode":"validate_and_execute","user_id":"you"}\' "run"'
    )
    print()
    print("Structured JSONL output (for tooling):")
    print("  adk run fhir_validator_agent --jsonl --state '{...}' run")
    print("=" * 78)


def main() -> None:
    parser = argparse.ArgumentParser(description="Google ADK CLI demo for FHIR Query Validator")
    parser.add_argument(
        "--scenario",
        choices=[*HAPI_DEMO_SCENARIOS.keys(), "all"],
        default="all",
        help="Which scripted scenario to run (default: all)",
    )
    parser.add_argument(
        "--interactive-hint-only",
        action="store_true",
        help="Skip scripted runs; only print interactive adk run instructions",
    )
    args = parser.parse_args()

    require_adk()
    if not agent_dir().exists():
        print(f"Agent folder not found: {agent_dir()}")
        sys.exit(1)

    print("FHIR Query Validator Factory — Google ADK CLI Demo")
    print(f"ADK CLI     : {'found' if adk_available() else 'missing'}")
    print(f"Agent entry : {agent_dir() / 'agent.py'}")

    if args.interactive_hint_only:
        print_interactive_instructions()
        return

    names = list(HAPI_DEMO_SCENARIOS) if args.scenario == "all" else [args.scenario]
    for name in names:
        config = HAPI_DEMO_SCENARIOS[name]
        if config.get("in_process"):
            run_learner_in_process(name, config)
        else:
            run_adk_subprocess(name, config)

    print_interactive_instructions()
    print("\nDemo complete.")


if __name__ == "__main__":
    main()