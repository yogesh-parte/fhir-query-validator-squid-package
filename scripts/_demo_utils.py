"""Shared helpers for demo scripts."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def add_project_root_to_path() -> Path:
    root = Path(__file__).resolve().parent.parent
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    return root


def mockhealth_api_key() -> str | None:
    return os.getenv("MOCK_HEALTH_API_KEY")


def require_mockhealth_key() -> str:
    key = mockhealth_api_key()
    if key:
        return key
    print(
        "mock.health requires MOCK_HEALTH_API_KEY.\n"
        "  1. Copy .env.example to .env.local\n"
        "  2. Add your key from https://mock.health/docs\n"
        "  3. Re-run this script"
    )
    sys.exit(1)


def reset_workflow_singletons() -> None:
    from src.agentic_layer.graph.workflow_engine import reset_singletons

    reset_singletons()


def print_scenario_header(name: str, *, query_url: str, server_key: str, user_id: str, mode: str) -> None:
    print("\n" + "=" * 78)
    print(f"SCENARIO: {name}")
    print("=" * 78)
    print(f"Query      : {query_url}")
    print(f"Server     : {server_key}")
    print(f"User       : {user_id}")
    print(f"Mode       : {mode}")
    print("-" * 78)


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def agent_dir() -> Path:
    return project_root() / "fhir_validator_agent"


def adk_available() -> bool:
    import shutil

    return shutil.which("adk") is not None


def require_adk() -> None:
    if adk_available():
        return
    print(
        "Google ADK CLI not found. Install with:\n"
        "  pip install google-adk\n"
        "  # or: pip install -e '.[adk-cli]'"
    )
    sys.exit(1)


def summarize_final_output(final: dict[str, Any]) -> None:
    print("\n--- FINAL OUTPUT ---")
    print(f"Valid                 : {final.get('valid')}")
    print(f"Server Used           : {final.get('server_used')}")
    print(f"Pattern Detected      : {final.get('pattern_detected')}")
    print(f"Escalation            : {final.get('escalation')}")
    print(f"Execution Performed   : {final.get('executed')}")
    print(f"Human Review Required : {final.get('human_review_required')}")
    if final.get("errors"):
        print(f"Errors                : {final.get('errors')}")
    if final.get("results"):
        print(f"Results               : {final.get('results')}")


# Shared HAPI demo scenarios used by ADK CLI/Web demos and loop scripts.
HAPI_DEMO_SCENARIOS: dict[str, dict[str, Any]] = {
    "valid": {
        "title": "Valid query — cache → validate → execute",
        "state": {
            "query_url": "Patient?gender=male",
            "server_key": "hapi",
            "mode": "validate_and_execute",
        },
    },
    "invalid": {
        "title": "Invalid query — validation errors surfaced",
        "state": {
            "query_url": "Patient?not_a_real_param=true",
            "server_key": "hapi",
            "mode": "validate_only",
        },
    },
    "learner": {
        "title": "Repeated invalid queries — learner escalation",
        "state": {
            "query_url": "Patient?not_a_real_param=true",
            "server_key": "hapi",
            "mode": "validate_only",
        },
        "repeat": 3,
        "in_process": True,
    },
}


def parse_jsonl_events(stdout: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def parse_adk_events(events_or_stdout: str | list[dict[str, Any]]) -> dict[str, Any]:
    """Extract node paths, final_output, and ADK errors from JSONL or event lists."""
    if isinstance(events_or_stdout, str):
        events = parse_jsonl_events(events_or_stdout)
    else:
        events = events_or_stdout

    node_paths: list[str] = []
    final_output: dict[str, Any] = {}
    errors: list[str] = []

    for event in events:
        node_info = event.get("nodeInfo") or {}
        path = node_info.get("path")
        if path:
            node_paths.append(path)

        if event.get("errorMessage"):
            errors.append(f"{event.get('errorCode')}: {event.get('errorMessage')}")

        delta = (event.get("actions") or {}).get("stateDelta") or {}
        if delta.get("final_output"):
            final_output = delta["final_output"]

    return {
        "node_paths": node_paths,
        "final_output": final_output,
        "errors": errors,
    }