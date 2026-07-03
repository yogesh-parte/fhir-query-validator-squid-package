#!/usr/bin/env python3
"""
demo_agent_traceability.py
Demonstrates per-agent traceability across the validation workflow.

Shows:
- Which agents participated in each run
- Validation, execution, and escalation decisions
- Structured audit trail entries (RuleAgent + HumanInterventionGate)
- Human pause → review → resume lifecycle

Usage:
    python3 scripts/demo_agent_traceability.py
    python3 scripts/demo_agent_traceability.py --server mockhealth
    python3 scripts/demo_agent_traceability.py --export traces.json
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from typing import Any

from _demo_utils import (
    add_project_root_to_path,
    mockhealth_api_key,
    print_scenario_header,
    require_mockhealth_key,
    reset_workflow_singletons,
)

add_project_root_to_path()

from src.agentic_layer.graph import workflow_engine
from src.agentic_layer.graph.validation_workflow import run_validation_workflow


def _agent_steps(state: dict[str, Any]) -> list[str]:
    steps: list[str] = []

    if state.get("capability_statement"):
        resources = state.get("interpreted_capability", {}).get("supported_resources", {})
        resource_list = ", ".join(sorted(resources.keys())[:8]) or "none"
        steps.append(f"[CacheAgent] CapabilityStatement fetched ({len(resources)} resources: {resource_list})")
    elif state.get("workflow_error"):
        steps.append(f"[CacheAgent] Skipped — {state['workflow_error']}")
    else:
        steps.append("[CacheAgent] No capability statement on state")

    if state.get("interpreted_capability"):
        count = len(state["interpreted_capability"].get("supported_resources", {}))
        steps.append(f"[CapabilityInterpreterAgent] Interpreted {count} supported resource type(s)")
    else:
        steps.append("[CapabilityInterpreterAgent] Not invoked")

    validation = state.get("validation_result") or {}
    if validation:
        steps.append(
            "[QueryValidatorAgent] "
            f"valid={validation.get('valid')} "
            f"errors={len(validation.get('errors', []))} "
            f"pattern_detected={validation.get('pattern_detected', state.get('pattern_detected'))}"
        )
    else:
        steps.append("[QueryValidatorAgent] Not invoked")

    execution = state.get("execution_result") or {}
    if execution.get("executed") and execution.get("status") == "success":
        steps.append(
            "[QueryExecutionAgent] Executed successfully "
            f"(http={execution.get('http_status')}, total={execution.get('total')})"
        )
    elif execution.get("executed") and execution.get("status") == "error":
        steps.append(
            "[QueryExecutionAgent] Execution failed "
            f"({execution.get('error_type')}: {execution.get('message', '')})"
        )
    elif state.get("mode") == "validate_and_execute" and validation.get("valid"):
        steps.append("[QueryExecutionAgent] Expected execution but no success result recorded")
    else:
        steps.append("[QueryExecutionAgent] Skipped (validate_only or invalid query)")

    escalation = state.get("escalation_decision") or state.get("final_output", {}).get("escalation")
    if escalation and escalation != "none":
        audit = state.get("escalation_audit", {})
        steps.append(f"[RuleAgent] Escalation decision: {escalation} — {audit.get('reasoning', 'n/a')}")
    else:
        steps.append("[RuleAgent] No escalation (decision=none)")

    if state.get("learner_guidance"):
        guidance = state["learner_guidance"]
        steps.append(
            "[SearchLearnerAgent] Guidance issued — "
            f"{guidance.get('suggestion', guidance.get('message', ''))[:80]}"
        )
    else:
        steps.append("[SearchLearnerAgent] Not invoked")

    human = state.get("human_review") or state.get("final_output", {}).get("human_review")
    if human:
        steps.append(
            "[HumanInterventionGate] Review opened "
            f"(severity={human.get('severity')}, review_id={human.get('review_id', 'n/a')})"
        )
    else:
        steps.append("[HumanInterventionGate] Not invoked")

    return steps


def _audit_section(user_id: str | None) -> list[str]:
    lines = ["", "AUDIT TRAIL", "-" * 78]
    records = workflow_engine._audit_log.query(user_id=user_id)
    if not records:
        lines.append("  (no audit records for this user)")
        return lines

    for record in records[-5:]:
        ts = datetime.fromtimestamp(record.timestamp).isoformat(timespec="seconds")
        lines.append(
            f"  [{ts}] {record.event_type} | decision={record.decision} | {record.reasoning}"
        )
    return lines


def format_agent_trace(state: dict[str, Any]) -> str:
    final = state.get("final_output", {})
    lines = [
        "",
        "=" * 78,
        "AGENT TRACEABILITY REPORT",
        "=" * 78,
        f"Timestamp  : {datetime.now().isoformat(timespec='seconds')}",
        f"Query      : {state.get('query_url')}",
        f"User       : {state.get('user_id', 'N/A')}",
        f"Server     : {state.get('server_key', 'default')}",
        f"Mode       : {state.get('mode', 'validate_only')}",
        "",
        "AGENT PIPELINE",
        "-" * 78,
    ]
    lines.extend(f"  {step}" for step in _agent_steps(state))
    lines.extend(_audit_section(state.get("user_id")))
    lines.extend([
        "",
        "OUTCOME",
        "-" * 78,
        f"  Valid              : {final.get('valid')}",
        f"  Escalation         : {final.get('escalation')}",
        f"  Human Review       : {final.get('human_review_required')}",
        f"  Executed           : {final.get('executed')}",
        "=" * 78,
    ])
    return "\n".join(lines)


def run_workflow(
    *,
    name: str,
    query_url: str,
    server_key: str,
    user_id: str,
    mode: str = "validate_and_execute",
) -> dict[str, Any]:
    print_scenario_header(
        name,
        query_url=query_url,
        server_key=server_key,
        user_id=user_id,
        mode=mode,
    )
    result = run_validation_workflow({
        "query_url": query_url,
        "server_key": server_key,
        "user_id": user_id,
        "mode": mode,
    })
    print(format_agent_trace(result))
    return result


def run_demo(server_key: str, export_path: str | None) -> None:
    print("\n=== Agent Traceability Demo ===\n")
    print("Tracing agent decisions, escalation audits, and human-gate lifecycle.\n")

    traces: list[dict[str, Any]] = []

    reset_workflow_singletons()
    traces.append(run_workflow(
        name="Valid Query — Full Pipeline",
        query_url="Patient?gender=male",
        server_key=server_key,
        user_id="trace-user-valid",
    ))

    reset_workflow_singletons()
    learner_state = None
    for attempt in range(1, 4):
        learner_state = run_workflow(
            name=f"Learner Escalation — Attempt {attempt}/3",
            query_url="Patient?invalid_param=true",
            server_key=server_key,
            user_id="trace-user-learner",
        )
    traces.append(learner_state)

    reset_workflow_singletons()
    human_state = None
    for attempt in range(1, 6):
        human_state = run_workflow(
            name=f"Human Escalation — Attempt {attempt}/5",
            query_url="Patient?invalid_param=true",
            server_key=server_key,
            user_id="trace-user-human",
            mode="validate_only",
        )
    traces.append(human_state)

    review_id = (human_state or {}).get("human_review", {}).get("review_id")
    if review_id:
        print("\n--- HUMAN GATE: submit_review_decision ---")
        resolution = workflow_engine.human_gate.submit_review_decision(
            review_id,
            reviewer="demo-operator",
            decision="continue_monitoring",
            rationale="Demo resume after human review.",
        )
        print(f"Resumed: {resolution['resumed']} | Decision: {resolution['review']['decision']}")
        traces.append({
            "event": "human_review_resolved",
            "review_id": review_id,
            "resolution": resolution,
        })

        resumed = run_workflow(
            name="Post-Resume Valid Query",
            query_url="Patient?gender=male",
            server_key=server_key,
            user_id="trace-user-human",
            mode="validate_only",
        )
        traces.append(resumed)

    if export_path:
        payload = {
            "generated_at": datetime.now().isoformat(),
            "server_key": server_key,
            "traces": traces,
        }
        with open(export_path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, default=str)
        print(f"\nExported trace bundle to {export_path}")

    print("\nDemo completed. Review agent pipeline sections and audit trail above.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Agent traceability demo for FHIR query validation.")
    parser.add_argument(
        "--server",
        default="hapi",
        choices=["hapi", "firely", "mockhealth"],
        help="FHIR server key (default: hapi)",
    )
    parser.add_argument(
        "--export",
        metavar="PATH",
        help="Write trace results to a JSON file",
    )
    args = parser.parse_args()

    if args.server == "mockhealth":
        require_mockhealth_key()
    elif args.server == "firely":
        print("Using public Firely server (no auth required).\n")
    else:
        print("Using public HAPI FHIR server (no auth required).\n")

    run_demo(args.server, args.export)


if __name__ == "__main__":
    main()