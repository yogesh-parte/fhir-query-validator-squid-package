"""
Regression tests for learner/human escalation thresholds.
"""

from unittest.mock import patch

from src.agentic_layer.graph.validation_workflow import run_validation_workflow
from tests.integration.conftest import PATIENT_CAPABILITY


@patch("src.agentic_layer.graph.workflow_engine.cache_agent.get_capability_statement")
def test_learner_threshold_still_triggers_at_three_failures(mock_get_capability):
    mock_get_capability.return_value = PATIENT_CAPABILITY
    user = "regression-learner-threshold"

    last = None
    for _ in range(3):
        last = run_validation_workflow(
            {
                "query_url": "Patient?invalid_param=true",
                "server_key": "hapi",
                "user_id": user,
                "mode": "validate_only",
            }
        )

    assert last is not None
    output = last["final_output"]
    assert output["escalation"] == "learner"
    assert output["pattern_detected"] is True
    assert last.get("learner_guidance")


@patch("src.agentic_layer.graph.workflow_engine.cache_agent.get_capability_statement")
def test_human_threshold_still_triggers_at_five_failures(mock_get_capability):
    mock_get_capability.return_value = PATIENT_CAPABILITY
    user = "regression-human-threshold"

    last = None
    for _ in range(5):
        last = run_validation_workflow(
            {
                "query_url": "Patient?invalid_param=true",
                "server_key": "hapi",
                "user_id": user,
                "mode": "validate_only",
            }
        )

    assert last is not None
    output = last["final_output"]
    assert output["escalation"] == "human"
    assert output["human_review_required"] is True
    assert output["human_review"]["severity"] == "high"


@patch("src.agentic_layer.graph.workflow_engine.cache_agent.get_capability_statement")
def test_high_severity_still_escalates_to_human_on_first_query(mock_get_capability):
    mock_get_capability.return_value = PATIENT_CAPABILITY

    result = run_validation_workflow(
        {
            "query_url": "Patient?subject.name=Smith",
            "server_key": "hapi",
            "user_id": "regression-high-severity-workflow",
            "mode": "validate_only",
        }
    )

    output = result["final_output"]
    assert output["escalation"] == "human"
    assert output["human_review_required"] is True
    assert output["pattern_detected"] is True
