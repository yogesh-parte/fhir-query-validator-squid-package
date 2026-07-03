"""
Integration tests for the full validation workflow.
"""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from src.agentic_layer.exceptions import AuthenticationRequiredError, CapabilityFetchError
from src.agentic_layer.graph import workflow_engine
from src.agentic_layer.graph.validation_workflow import run_validation_workflow

from .conftest import PATIENT_CAPABILITY, mock_http_response, mock_shared_httpx_client


@patch("src.agentic_layer.graph.workflow_engine.executor.execute")
@patch("src.agentic_layer.graph.workflow_engine.cache_agent.get_capability_statement")
def test_full_workflow_with_valid_query(mock_get_capability, mock_execute):
    mock_get_capability.return_value = PATIENT_CAPABILITY
    mock_execute.return_value = {
        "executed": True,
        "status": "success",
        "http_status": 200,
        "elapsed_ms": 12.5,
        "bundle_type": "searchset",
        "total": 2,
        "resource_type": "Bundle",
    }

    result = run_validation_workflow({
        "query_url": "Patient?gender=male",
        "server_key": "hapi",
        "user_id": "integration-test",
        "mode": "validate_and_execute",
    })

    output = result["final_output"]
    assert output["valid"] is True
    assert output["server_used"] == "hapi"
    assert output["executed"] is True
    assert output["results"]["total"] == 2


@patch("httpx.Client")
def test_full_stack_cache_and_execution_agents(mock_client_class):
    """Drive real CacheAgent + QueryExecutionAgent with mocked HTTP only."""
    http = mock_shared_httpx_client()
    mock_client_class.return_value = http

    result = run_validation_workflow({
        "query_url": "Patient?gender=male",
        "server_key": "hapi",
        "mode": "validate_and_execute",
    })

    assert result["final_output"]["valid"] is True
    assert result["final_output"]["executed"] is True
    assert result["final_output"]["results"]["total"] == 4
    urls = [call.args[0] for call in http.get.call_args_list]
    assert any("/metadata" in url for url in urls)
    assert any("/Patient?gender=male" in url for url in urls)


@patch("src.agentic_layer.agents.query_execution.httpx.Client")
@patch("src.agentic_layer.graph.workflow_engine.cache_agent.get_capability_statement")
def test_end_to_end_uses_query_execution_agent(mock_get_capability, mock_exec_client):
    """Exercise QueryExecutionAgent through the workflow (not a mocked executor)."""
    mock_get_capability.return_value = PATIENT_CAPABILITY
    exec_http = MagicMock()
    exec_http.__enter__.return_value = exec_http
    exec_http.get.return_value = mock_http_response(
        200,
        {"resourceType": "Bundle", "type": "searchset", "total": 7},
    )
    mock_exec_client.return_value = exec_http

    result = run_validation_workflow({
        "query_url": "Patient?gender=male",
        "server_key": "hapi",
        "user_id": "integration-e2e-exec",
        "mode": "validate_and_execute",
    })

    output = result["final_output"]
    assert output["valid"] is True
    assert output["executed"] is True
    assert output["results"]["status"] == "success"
    assert output["results"]["total"] == 7
    exec_http.get.assert_called_once()
    assert "hapi.fhir.org" in exec_http.get.call_args.args[0]


@patch("src.agentic_layer.graph.workflow_engine.cache_agent.get_capability_statement")
def test_validate_only_skips_execution(mock_get_capability):
    mock_get_capability.return_value = PATIENT_CAPABILITY

    result = run_validation_workflow({
        "query_url": "Patient?gender=male",
        "server_key": "hapi",
        "mode": "validate_only",
    })

    output = result["final_output"]
    assert output["valid"] is True
    assert output["executed"] is False
    assert output["results"] is None


@patch("src.agentic_layer.graph.workflow_engine.executor.execute")
@patch("src.agentic_layer.graph.workflow_engine.cache_agent.get_capability_statement")
def test_full_workflow_firely_server(mock_get_capability, mock_execute):
    mock_get_capability.return_value = PATIENT_CAPABILITY
    mock_execute.return_value = {
        "executed": True,
        "status": "success",
        "http_status": 200,
        "elapsed_ms": 8.0,
        "bundle_type": "searchset",
        "total": 1,
        "resource_type": "Bundle",
    }

    result = run_validation_workflow({
        "query_url": "Patient?gender=male",
        "server_key": "firely",
        "user_id": "integration-firely",
        "mode": "validate_and_execute",
    })

    output = result["final_output"]
    assert output["valid"] is True
    assert output["server_used"] == "firely"
    assert output["executed"] is True
    mock_get_capability.assert_called_once_with("firely", auth_token=None)


@patch("src.agentic_layer.graph.workflow_engine.executor.execute")
@patch("src.agentic_layer.graph.workflow_engine.cache_agent.get_capability_statement")
def test_mockhealth_workflow_with_api_key(mock_get_capability, mock_execute, monkeypatch):
    monkeypatch.setenv("MOCK_HEALTH_API_KEY", "sk_test_mockhealth_key")
    mock_get_capability.return_value = PATIENT_CAPABILITY
    mock_execute.return_value = {
        "executed": True,
        "status": "success",
        "http_status": 200,
        "elapsed_ms": 42.0,
        "bundle_type": "searchset",
        "total": 5,
        "resource_type": "Bundle",
    }

    result = run_validation_workflow({
        "query_url": "Patient?_count=1",
        "server_key": "mockhealth",
        "user_id": "integration-mockhealth",
        "mode": "validate_and_execute",
    })

    output = result["final_output"]
    assert output["valid"] is True
    assert output["server_used"] == "mockhealth"
    assert output["executed"] is True
    mock_get_capability.assert_called_once_with("mockhealth", auth_token=None)


@patch("src.agentic_layer.graph.workflow_engine.executor.execute")
@patch("src.agentic_layer.graph.workflow_engine.cache_agent.get_capability_statement")
def test_mockhealth_auth_token_override(mock_get_capability, mock_execute, monkeypatch):
    monkeypatch.delenv("MOCK_HEALTH_API_KEY", raising=False)
    mock_get_capability.return_value = PATIENT_CAPABILITY
    mock_execute.return_value = {
        "executed": True,
        "status": "success",
        "http_status": 200,
        "elapsed_ms": 10.0,
        "bundle_type": "searchset",
        "total": 1,
        "resource_type": "Bundle",
    }

    result = run_validation_workflow({
        "query_url": "Patient?_count=1",
        "server_key": "mockhealth",
        "auth_token": "runtime-override-token",
        "mode": "validate_and_execute",
    })

    assert result["final_output"]["valid"] is True
    mock_get_capability.assert_called_once_with("mockhealth", auth_token="runtime-override-token")


def test_mockhealth_missing_api_key_returns_auth_error(monkeypatch):
    monkeypatch.delenv("MOCK_HEALTH_API_KEY", raising=False)
    monkeypatch.setenv("FHIR_USE_AUTH", "false")

    result = run_validation_workflow({
        "query_url": "Patient?_count=1",
        "server_key": "mockhealth",
        "mode": "validate_only",
    })

    output = result["final_output"]
    assert output["valid"] is False
    assert output["server_used"] == "mockhealth"
    assert "Authentication required" in output["errors"][0]
    assert "MOCK_HEALTH_API_KEY" in output["errors"][0]
    assert ".env.local" in output["errors"][0]


@patch("src.agentic_layer.agents.cache_agent.httpx.Client")
def test_full_workflow_human_escalation(mock_cache_client):
    cache_http = MagicMock()
    cache_http.__enter__.return_value = cache_http
    cache_http.get.return_value = mock_http_response(200, PATIENT_CAPABILITY)
    mock_cache_client.return_value = cache_http

    user = "integration-human-user"
    for _ in range(5):
        result = run_validation_workflow({
            "query_url": "Patient?invalid_param=true",
            "server_key": "hapi",
            "user_id": user,
            "mode": "validate_only",
        })

    assert result["final_output"]["valid"] is False
    assert result["final_output"]["escalation"] == "human"
    assert result["final_output"]["human_review_required"] is True
    assert result["final_output"]["human_review"]["severity"] == "high"


@patch("src.agentic_layer.agents.cache_agent.httpx.Client")
def test_paused_user_blocked_from_subsequent_workflow(mock_cache_client):
    cache_http = MagicMock()
    cache_http.__enter__.return_value = cache_http
    cache_http.get.return_value = mock_http_response(200, PATIENT_CAPABILITY)
    mock_cache_client.return_value = cache_http

    user = "integration-paused-user"
    for _ in range(5):
        run_validation_workflow({
            "query_url": "Patient?invalid_param=true",
            "server_key": "hapi",
            "user_id": user,
            "mode": "validate_only",
        })

    blocked = run_validation_workflow({
        "query_url": "Patient?gender=male",
        "server_key": "hapi",
        "user_id": user,
        "mode": "validate_only",
    })

    assert blocked["final_output"]["valid"] is False
    assert "paused" in blocked["final_output"]["errors"][0].lower()


@patch("src.agentic_layer.graph.workflow_engine.cache_agent.get_capability_statement")
def test_human_pause_resume_full_flow(mock_get_capability):
    mock_get_capability.return_value = PATIENT_CAPABILITY
    user = "integration-resume-user"

    last = None
    for _ in range(5):
        last = run_validation_workflow({
            "query_url": "Patient?invalid_param=true",
            "server_key": "hapi",
            "user_id": user,
            "mode": "validate_only",
        })

    review_id = last["final_output"]["human_review"]["review_id"]
    resolution = workflow_engine.human_gate.submit_review_decision(
        review_id,
        reviewer="integration-operator",
        decision="continue_monitoring",
        rationale="Resume after review.",
    )
    assert resolution["resumed"] is True

    resumed = run_validation_workflow({
        "query_url": "Patient?gender=male",
        "server_key": "hapi",
        "user_id": user,
        "mode": "validate_only",
    })
    assert resumed["final_output"]["valid"] is True


@patch("src.agentic_layer.agents.cache_agent.httpx.Client")
def test_learner_escalation_after_three_invalid_queries(mock_cache_client):
    cache_http = MagicMock()
    cache_http.__enter__.return_value = cache_http
    cache_http.get.return_value = mock_http_response(200, PATIENT_CAPABILITY)
    mock_cache_client.return_value = cache_http

    user = "integration-learner-user"
    for _ in range(3):
        result = run_validation_workflow({
            "query_url": "Patient?invalid_param=true",
            "server_key": "hapi",
            "user_id": user,
            "mode": "validate_only",
        })

    assert result["final_output"]["escalation"] == "learner"
    assert result["final_output"]["pattern_detected"] is True
    assert result.get("learner_guidance")
    assert result["escalation_audit"]["decision"] == "learner"


@patch("src.agentic_layer.graph.workflow_engine.cache_agent.get_capability_statement")
def test_no_escalation_without_user_id(mock_get_capability):
    mock_get_capability.return_value = PATIENT_CAPABILITY

    result = run_validation_workflow({
        "query_url": "Patient?invalid_param=true",
        "server_key": "hapi",
        "mode": "validate_only",
    })

    assert result["final_output"]["valid"] is False
    assert result["final_output"]["escalation"] == "none"
    assert result["final_output"]["pattern_detected"] is False


@patch("src.agentic_layer.graph.workflow_engine.cache_agent.get_capability_statement")
def test_sensitive_chained_parameter_sets_high_severity(mock_get_capability):
    mock_get_capability.return_value = PATIENT_CAPABILITY

    result = run_validation_workflow({
        "query_url": "Patient?subject.name=Smith",
        "server_key": "hapi",
        "user_id": "integration-chain-user",
        "mode": "validate_only",
    })

    assert result["validation_result"]["high_severity"] is True
    assert any("sensitive" in w.lower() for w in result["validation_result"]["warnings"])


@patch("src.agentic_layer.graph.workflow_engine.cache_agent.get_capability_statement")
def test_unknown_resource_type_fails_validation(mock_get_capability):
    mock_get_capability.return_value = PATIENT_CAPABILITY

    result = run_validation_workflow({
        "query_url": "Observation?code=1234",
        "server_key": "hapi",
        "mode": "validate_only",
    })

    output = result["final_output"]
    assert output["valid"] is False
    assert "Observation" in output["errors"][0]


@patch("src.agentic_layer.agents.query_execution.httpx.Client")
@patch("src.agentic_layer.graph.workflow_engine.cache_agent.get_capability_statement")
def test_execution_auth_failure_surfaces_error_result(mock_get_capability, mock_exec_client):
    mock_get_capability.return_value = PATIENT_CAPABILITY
    exec_http = MagicMock()
    exec_http.__enter__.return_value = exec_http
    exec_http.get.return_value = mock_http_response(401)
    mock_exec_client.return_value = exec_http

    result = run_validation_workflow({
        "query_url": "Patient?gender=male",
        "server_key": "mockhealth",
        "auth_token": "bad-token",
        "mode": "validate_and_execute",
    })

    output = result["final_output"]
    assert output["valid"] is True
    assert output["executed"] is False
    assert output["results"] is None
    assert result["execution_result"]["status"] == "error"
    assert result["execution_result"]["error_type"] == "authentication_failed"


@patch("src.agentic_layer.agents.query_execution.httpx.Client")
@patch("src.agentic_layer.graph.workflow_engine.cache_agent.get_capability_statement")
def test_execution_forbidden_returns_authorization_error(mock_get_capability, mock_exec_client):
    mock_get_capability.return_value = PATIENT_CAPABILITY
    exec_http = MagicMock()
    exec_http.__enter__.return_value = exec_http
    exec_http.get.return_value = mock_http_response(403)
    mock_exec_client.return_value = exec_http

    result = run_validation_workflow({
        "query_url": "Patient?gender=male",
        "server_key": "mockhealth",
        "auth_token": "limited-token",
        "mode": "validate_and_execute",
    })

    assert result["final_output"]["executed"] is False
    assert result["execution_result"]["error_type"] == "authorization_failed"
    assert result["execution_result"]["http_status"] == 403


@patch("src.agentic_layer.agents.cache_agent.httpx.Client")
def test_cache_metadata_401_raises_authentication_required(mock_cache_client):
    cache_http = MagicMock()
    cache_http.__enter__.return_value = cache_http
    cache_http.get.return_value = mock_http_response(401)
    mock_cache_client.return_value = cache_http

    with pytest.raises(AuthenticationRequiredError):
        run_validation_workflow({
            "query_url": "Patient?gender=male",
            "server_key": "mockhealth",
            "auth_token": "bad-token",
            "mode": "validate_only",
        })


@patch("src.agentic_layer.agents.cache_agent.httpx.Client")
def test_cache_metadata_500_raises_capability_fetch(mock_cache_client):
    cache_http = MagicMock()
    cache_http.__enter__.return_value = cache_http
    cache_http.get.return_value = mock_http_response(500)
    mock_cache_client.return_value = cache_http

    with pytest.raises(CapabilityFetchError):
        run_validation_workflow({
            "query_url": "Patient?gender=male",
            "server_key": "hapi",
            "mode": "validate_only",
        })


@patch("src.agentic_layer.agents.cache_agent.httpx.Client")
def test_cache_metadata_network_error_raises_capability_fetch(mock_cache_client):
    cache_http = MagicMock()
    cache_http.__enter__.return_value = cache_http
    cache_http.get.side_effect = httpx.ConnectError("connection refused")
    mock_cache_client.return_value = cache_http

    with pytest.raises(CapabilityFetchError):
        run_validation_workflow({
            "query_url": "Patient?gender=male",
            "server_key": "hapi",
            "mode": "validate_only",
        })


@patch("httpx.Client")
def test_workflow_cache_304_reuses_capability(mock_client_class):
    """Second workflow call should reuse cached CapabilityStatement on 304."""
    http = MagicMock()
    http.__enter__.return_value = http
    http.get.side_effect = [
        mock_http_response(200, PATIENT_CAPABILITY),
        mock_http_response(304, PATIENT_CAPABILITY),
    ]
    mock_client_class.return_value = http

    first = run_validation_workflow({
        "query_url": "Patient?gender=male",
        "server_key": "hapi",
        "mode": "validate_only",
    })
    second = run_validation_workflow({
        "query_url": "Patient?gender=male",
        "server_key": "hapi",
        "mode": "validate_only",
    })

    assert first["final_output"]["valid"] is True
    assert second["final_output"]["valid"] is True
    assert http.get.call_count == 2
    assert "If-None-Match" in http.get.call_args_list[1].kwargs["headers"]


def test_unknown_server_key_returns_error():
    result = run_validation_workflow({
        "query_url": "Patient?gender=male",
        "server_key": "does-not-exist",
        "mode": "validate_only",
    })
    assert result["final_output"]["valid"] is False
    assert "Unknown server_key" in result["final_output"]["errors"][0]