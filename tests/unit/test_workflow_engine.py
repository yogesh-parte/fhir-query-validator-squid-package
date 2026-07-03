"""Unit tests for workflow engine helpers and execute_workflow."""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from src.agentic_layer.exceptions import AuthenticationRequiredError, CapabilityFetchError
from src.agentic_layer.graph import workflow_engine
from src.agentic_layer.graph.workflow_engine import (
    build_final_output,
    execute_workflow,
    reset_singletons,
)
from src.agentic_layer.state.workflow_state import ValidationWorkflowState

PATIENT_CAPABILITY = {
    "resourceType": "CapabilityStatement",
    "rest": [{
        "resource": [{
            "type": "Patient",
            "searchParam": [
                {"name": "gender", "type": "token"},
                {"name": "subject", "type": "reference"},
            ],
        }],
    }],
}


def test_build_final_output_includes_spec_contract_fields():
    state = ValidationWorkflowState(
        server_key="hapi",
        validation_result={
            "valid": True,
            "errors": [],
            "warnings": ["optional warning"],
        },
        execution_result={
            "executed": True,
            "status": "success",
            "total": 3,
        },
        pattern_detected=False,
        escalation_decision="none",
    )

    output = build_final_output(state)

    assert output["valid"] is True
    assert output["server_used"] == "hapi"
    assert output["errors"] == []
    assert output["warnings"] == ["optional warning"]
    assert output["executed"] is True
    assert output["results"]["total"] == 3
    assert output["pattern_detected"] is False
    assert output["escalation"] == "none"
    assert output["human_review_required"] is False


def test_build_final_output_marks_human_review_when_present():
    state = ValidationWorkflowState(
        server_key="mockhealth",
        validation_result={"valid": False, "errors": ["bad query"], "warnings": []},
        execution_result={"executed": False},
        pattern_detected=True,
        escalation_decision="human",
        human_review={"review_id": "abc-123", "status": "paused_pending_review"},
    )

    output = build_final_output(state)

    assert output["escalation"] == "human"
    assert output["human_review_required"] is True
    assert output["human_review"]["review_id"] == "abc-123"


def test_build_final_output_omits_results_when_execution_not_successful():
    state = ValidationWorkflowState(
        server_key="hapi",
        validation_result={"valid": True, "errors": [], "warnings": []},
        execution_result={"executed": True, "status": "error", "error_type": "http_error"},
    )

    output = build_final_output(state)

    assert output["valid"] is True
    assert output["executed"] is False
    assert output["results"] is None


@patch("src.agentic_layer.graph.workflow_engine.cache_agent.get_capability_statement")
def test_execute_workflow_generates_query_from_spec(mock_get_capability):
    mock_get_capability.return_value = {
        "resourceType": "CapabilityStatement",
        "rest": [{
            "resource": [{
                "type": "Patient",
                "searchParam": [{"name": "gender", "type": "token"}],
            }],
        }],
    }

    state = execute_workflow({
        "query_generation": {
            "resource_type": "Patient",
            "criteria": {"gender": "male"},
            "count": 3,
        },
        "server_key": "hapi",
        "mode": "validate_only",
    })

    assert state.generated_query["generated"] is True
    assert state.query_url == "Patient?gender=male&_count=3"
    assert state.validation_result["valid"] is True


@patch("src.agentic_layer.graph.workflow_engine.cache_agent.get_capability_statement")
def test_execute_workflow_validate_only_success(mock_get_capability):
    mock_get_capability.return_value = PATIENT_CAPABILITY

    state = execute_workflow({
        "query_url": "Patient?gender=male",
        "server_key": "hapi",
        "mode": "validate_only",
    })

    assert state.final_output["valid"] is True
    assert state.final_output["executed"] is False
    assert state.escalation_decision == "none"
    mock_get_capability.assert_called_once_with("hapi", auth_token=None)


@patch("src.agentic_layer.graph.workflow_engine.executor.execute")
@patch("src.agentic_layer.graph.workflow_engine.cache_agent.get_capability_statement")
def test_execute_workflow_validate_and_execute(mock_get_capability, mock_execute):
    mock_get_capability.return_value = PATIENT_CAPABILITY
    mock_execute.return_value = {
        "executed": True,
        "status": "success",
        "http_status": 200,
        "total": 2,
    }

    state = execute_workflow({
        "query_url": "Patient?gender=male",
        "server_key": "hapi",
        "mode": "validate_and_execute",
    })

    assert state.final_output["valid"] is True
    assert state.final_output["executed"] is True
    assert state.final_output["results"]["total"] == 2
    mock_execute.assert_called_once()


def test_execute_workflow_blocks_paused_user():
    workflow_engine.human_gate._paused_users["paused-user"] = {
        "paused_at": 0,
        "review_id": "r-1",
        "severity": "high",
    }

    state = execute_workflow({
        "query_url": "Patient?gender=male",
        "server_key": "hapi",
        "user_id": "paused-user",
        "mode": "validate_only",
    })

    assert state.final_output["valid"] is False
    assert "paused" in state.final_output["errors"][0].lower()
    assert state.final_output["server_used"] == "hapi"
    assert state.final_output["executed"] is False
    assert state.final_output["pattern_detected"] is False
    assert state.final_output["human_review_required"] is False


def test_reset_singletons_clears_pattern_history_and_cache():
    workflow_engine.cache_agent._cache["hapi"] = {"data": {}, "timestamp": 0}
    workflow_engine.validator._pattern_history["user:hapi"] = [(0, "x")]
    workflow_engine.human_gate._paused_users["user"] = {"review_id": "r-1"}

    reset_singletons()

    assert not workflow_engine.cache_agent._cache
    assert not workflow_engine.validator._pattern_history
    assert not workflow_engine.human_gate._paused_users


def test_execute_workflow_unknown_server_key():
    state = execute_workflow({
        "query_url": "Patient?gender=male",
        "server_key": "does-not-exist",
        "mode": "validate_only",
    })

    assert state.final_output["valid"] is False
    assert "Unknown server_key" in state.final_output["errors"][0]
    assert state.validation_result["error_types"] == ["unknown_server"]


def test_execute_workflow_mockhealth_missing_credentials(monkeypatch):
    monkeypatch.delenv("MOCK_HEALTH_API_KEY", raising=False)
    monkeypatch.setenv("FHIR_USE_AUTH", "false")

    state = execute_workflow({
        "query_url": "Patient?_count=1",
        "server_key": "mockhealth",
        "mode": "validate_only",
    })

    assert state.final_output["valid"] is False
    assert state.validation_result["error_types"] == ["authentication_required"]
    assert "MOCK_HEALTH_API_KEY" in state.final_output["errors"][0]


@patch("src.agentic_layer.graph.workflow_engine.cache_agent.get_capability_statement")
def test_execute_workflow_learner_escalation(mock_get_capability):
    mock_get_capability.return_value = PATIENT_CAPABILITY
    user = "learner-escalation-user"

    state = None
    for _ in range(3):
        state = execute_workflow({
            "query_url": "Patient?invalid_param=true",
            "server_key": "hapi",
            "user_id": user,
            "mode": "validate_only",
        })

    assert state.final_output["valid"] is False
    assert state.escalation_decision == "learner"
    assert state.learner_guidance is not None
    assert state.learner_guidance["resource_type"] == "Patient"


@patch("src.agentic_layer.graph.workflow_engine.cache_agent.get_capability_statement")
def test_execute_workflow_human_escalation(mock_get_capability):
    mock_get_capability.return_value = PATIENT_CAPABILITY
    user = "human-escalation-user"

    state = None
    for _ in range(5):
        state = execute_workflow({
            "query_url": "Patient?invalid_param=true",
            "server_key": "hapi",
            "user_id": user,
            "mode": "validate_only",
        })

    assert state.escalation_decision == "human"
    assert state.human_review is not None
    assert state.human_review["paused"] is True


@patch("src.agentic_layer.graph.workflow_engine.cache_agent.get_capability_statement")
def test_execute_workflow_invalid_query_skips_execution(mock_get_capability):
    mock_get_capability.return_value = PATIENT_CAPABILITY

    state = execute_workflow({
        "query_url": "Observation?code=1234",
        "server_key": "hapi",
        "mode": "validate_and_execute",
    })

    assert state.final_output["valid"] is False
    assert state.execution_result == {"executed": False}


def _http_status_error(status_code: int) -> httpx.HTTPStatusError:
    response = MagicMock()
    response.status_code = status_code
    return httpx.HTTPStatusError("error", request=MagicMock(), response=response)


@patch("src.agentic_layer.graph.workflow_engine.cache_agent.get_capability_statement")
def test_execute_workflow_cache_401_raises_auth_error(mock_get_capability):
    mock_get_capability.side_effect = _http_status_error(401)

    with pytest.raises(AuthenticationRequiredError):
        execute_workflow({
            "query_url": "Patient?gender=male",
            "server_key": "mockhealth",
            "auth_token": "bad-token",
            "mode": "validate_only",
        })


@patch("src.agentic_layer.graph.workflow_engine.cache_agent.get_capability_statement")
def test_execute_workflow_cache_403_raises_auth_error(mock_get_capability):
    mock_get_capability.side_effect = _http_status_error(403)

    with pytest.raises(AuthenticationRequiredError):
        execute_workflow({
            "query_url": "Patient?gender=male",
            "server_key": "mockhealth",
            "auth_token": "bad-token",
            "mode": "validate_only",
        })


@patch("src.agentic_layer.graph.workflow_engine.cache_agent.get_capability_statement")
def test_execute_workflow_cache_500_raises_capability_fetch(mock_get_capability):
    mock_get_capability.side_effect = _http_status_error(500)

    with pytest.raises(CapabilityFetchError):
        execute_workflow({
            "query_url": "Patient?gender=male",
            "server_key": "hapi",
            "mode": "validate_only",
        })


@patch("src.agentic_layer.graph.workflow_engine.cache_agent.get_capability_statement")
def test_execute_workflow_cache_network_error_raises_capability_fetch(mock_get_capability):
    mock_get_capability.side_effect = httpx.ConnectError("connection refused")

    with pytest.raises(CapabilityFetchError):
        execute_workflow({
            "query_url": "Patient?gender=male",
            "server_key": "hapi",
            "mode": "validate_only",
        })