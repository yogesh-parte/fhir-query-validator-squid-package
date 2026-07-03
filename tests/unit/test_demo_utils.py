"""Unit tests for shared demo helpers."""

import json

from _demo_utils import parse_adk_events, parse_jsonl_events


def test_parse_jsonl_events_ignores_non_json_lines():
    stdout = "loading...\n" + json.dumps({"nodeInfo": {"path": "init"}}) + "\ndone"
    events = parse_jsonl_events(stdout)
    assert len(events) == 1
    assert events[0]["nodeInfo"]["path"] == "init"


def test_parse_adk_events_from_stdout():
    stdout = "\n".join([
        json.dumps({"nodeInfo": {"path": "initialize_workflow"}}),
        json.dumps({
            "actions": {
                "stateDelta": {
                    "final_output": {"valid": True, "executed": False},
                }
            }
        }),
    ])
    summary = parse_adk_events(stdout)
    assert summary["node_paths"] == ["initialize_workflow"]
    assert summary["final_output"]["valid"] is True


def test_parse_adk_events_from_event_list():
    events = [
        {"nodeInfo": {"path": "run_validation_pipeline"}},
        {"errorCode": "E1", "errorMessage": "boom"},
    ]
    summary = parse_adk_events(events)
    assert summary["node_paths"] == ["run_validation_pipeline"]
    assert summary["errors"] == ["E1: boom"]