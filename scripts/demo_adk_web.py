#!/usr/bin/env python3
"""
demo_adk_web.py
Showcase the FHIR Query Validator via Google ADK Web UI and HTTP API.

Starts `adk web` for the fhir_validator_agent package, optionally runs
scripted scenarios through the /run API, and prints the browser URL.

Usage:
    # Start server + run API demo scenarios (default)
    python3 scripts/demo_adk_web.py

    # Only launch the web UI (blocks until Ctrl+C)
    python3 scripts/demo_adk_web.py --serve-only

    # API demo against an already-running server
    python3 scripts/demo_adk_web.py --api-only --port 8080

Requirements:
    pip install google-adk httpx
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from typing import Any

import httpx

from _demo_utils import (
    HAPI_DEMO_SCENARIOS,
    adk_available,
    agent_dir,
    parse_adk_events,
    project_root,
    require_adk,
    summarize_final_output,
)

APP_NAME = "fhir_validator_agent"
DEFAULT_PORT = 8080


def _api_scenarios() -> list[dict[str, Any]]:
    return [
        {
            "name": HAPI_DEMO_SCENARIOS["valid"]["title"],
            "user_id": "web-demo-alice",
            "state": {
                **HAPI_DEMO_SCENARIOS["valid"]["state"],
            },
        },
        {
            "name": HAPI_DEMO_SCENARIOS["invalid"]["title"],
            "user_id": "web-demo-bob",
            "state": {
                **HAPI_DEMO_SCENARIOS["invalid"]["state"],
            },
        },
    ]


def _base_url(port: int) -> str:
    return f"http://127.0.0.1:{port}"


def wait_for_server(port: int, timeout: float = 30.0) -> None:
    deadline = time.time() + timeout
    url = f"{_base_url(port)}/list-apps"
    while time.time() < deadline:
        try:
            response = httpx.get(url, timeout=2.0)
            if response.status_code == 200:
                return
        except httpx.RequestError:
            pass
        time.sleep(0.5)
    raise TimeoutError(f"ADK web server did not become ready on port {port}")


def start_web_server(port: int) -> subprocess.Popen[str]:
    cmd = ["adk", "web", "--port", str(port), str(agent_dir())]
    return subprocess.Popen(
        cmd,
        cwd=project_root(),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )


def create_session(client: httpx.Client, user_id: str, state: dict[str, Any]) -> str:
    response = client.post(
        f"/apps/{APP_NAME}/users/{user_id}/sessions",
        json={"state": {**state, "user_id": user_id}},
    )
    response.raise_for_status()
    return response.json()["id"]


def run_agent(client: httpx.Client, user_id: str, session_id: str) -> list[dict[str, Any]]:
    payload = {
        "app_name": APP_NAME,
        "user_id": user_id,
        "session_id": session_id,
        "new_message": {
            "role": "user",
            "parts": [{"text": "run FHIR validation workflow"}],
        },
    }
    response = client.post("/run", json=payload, timeout=120.0)
    response.raise_for_status()
    return response.json()


def run_api_demo(port: int) -> None:
    print("\n" + "=" * 78)
    print("ADK WEB API DEMO")
    print("=" * 78)

    with httpx.Client(base_url=_base_url(port), timeout=120.0) as client:
        apps = client.get("/list-apps").json()
        print(f"Registered apps: {apps}")
        if APP_NAME not in apps:
            print(f"Expected app '{APP_NAME}' not found. Apps listed: {apps}")
            sys.exit(1)

        for scenario in _api_scenarios():
            user_id = scenario["user_id"]
            state = scenario["state"]
            print("\n" + "-" * 78)
            print(f"Scenario : {scenario['name']}")
            print(f"User     : {user_id}")
            print(f"State    : {json.dumps(state)}")

            session_id = create_session(client, user_id, state)
            events = run_agent(client, user_id, session_id)
            summary = parse_adk_events(events)

            if summary["node_paths"]:
                print("\nADK graph nodes:")
                for path in summary["node_paths"]:
                    print(f"  • {path}")

            if summary["final_output"]:
                summarize_final_output(summary["final_output"])
            else:
                print("No final_output returned from /run")

    print("=" * 78)


def print_web_instructions(port: int) -> None:
    url = _base_url(port)
    print("\n" + "=" * 78)
    print("ADK WEB UI")
    print("=" * 78)
    print(f"Open: {url}")
    print(f"Select agent: {APP_NAME}")
    print()
    print("Set initial session state in the UI (or via API) with fields such as:")
    print("  query_url, server_key, mode, user_id")
    print()
    print("Example state JSON:")
    print(
        json.dumps(
            {
                "query_url": "Patient?gender=male",
                "server_key": "hapi",
                "mode": "validate_and_execute",
                "user_id": "web-ui-user",
            },
            indent=2,
        )
    )
    print()
    print("Manual server start:")
    print(f"  adk web --port {port} {agent_dir()}")
    print("=" * 78)


def main() -> None:
    parser = argparse.ArgumentParser(description="Google ADK Web demo for FHIR Query Validator")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port for adk web")
    parser.add_argument(
        "--serve-only",
        action="store_true",
        help="Only start adk web and block (no API demo)",
    )
    parser.add_argument(
        "--api-only",
        action="store_true",
        help="Run API demo against an already-running server (do not start adk web)",
    )
    args = parser.parse_args()

    require_adk()
    if not agent_dir().exists():
        print(f"Agent folder not found: {agent_dir()}")
        sys.exit(1)

    print("FHIR Query Validator Factory — Google ADK Web Demo")

    server: subprocess.Popen[str] | None = None
    try:
        if not args.api_only:
            print(f"Starting ADK web on port {args.port} ...")
            server = start_web_server(args.port)
            wait_for_server(args.port)
            print(f"ADK web ready at {_base_url(args.port)}")

        if not args.serve_only:
            run_api_demo(args.port)

        print_web_instructions(args.port)

        if args.serve_only or (server and not args.api_only):
            print("\nPress Ctrl+C to stop the ADK web server.")
            if server:
                server.wait()
    except KeyboardInterrupt:
        print("\nStopping ADK web server...")
    finally:
        if server and server.poll() is None:
            server.terminate()
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()


if __name__ == "__main__":
    main()