"""Tests for OWASP hardening controls."""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from src.agentic_layer.agents.human_gate import HumanInterventionGate
from src.agentic_layer.agents.query_execution import QueryExecutionAgent
from src.agentic_layer.auth.identity import resolve_workflow_user_id
from src.agentic_layer.auth.operator import HumanGateAuthError, verify_human_gate_operator
from src.agentic_layer.graph.workflow_engine import execute_workflow, get_workflow_agents
from src.agentic_layer.utils.url_safety import UnsafeQueryUrlError, build_fhir_target_url


def test_build_fhir_target_url_joins_relative_path():
    url = build_fhir_target_url("https://hapi.fhir.org/baseR4", "Patient?gender=male")
    assert url == "https://hapi.fhir.org/baseR4/Patient?gender=male"


def test_build_fhir_target_url_rejects_absolute_query_url():
    with pytest.raises(UnsafeQueryUrlError, match="Absolute query_url"):
        build_fhir_target_url("https://hapi.fhir.org/baseR4", "https://evil.example/Patient")


def test_query_execution_rejects_absolute_query_url():
    agent = QueryExecutionAgent()
    result = agent.execute("https://evil.example/Patient", server_key="hapi")
    assert result["status"] == "error"
    assert result["error_type"] == "invalid_query_url"
    assert result["executed"] is False


@patch("src.agentic_layer.agents.query_execution.httpx.Client")
def test_query_execution_disables_redirect_following(mock_client_class):
    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.get.return_value = MagicMock(
        status_code=200,
        json=lambda: {"resourceType": "Bundle", "type": "searchset", "total": 0},
        raise_for_status=MagicMock(),
    )
    mock_client_class.return_value = mock_client

    agent = QueryExecutionAgent()
    agent.execute("Patient?gender=male", server_key="hapi")

    mock_client_class.assert_called_once_with(timeout=30.0, follow_redirects=False)


def test_human_gate_auth_disabled_by_default():
    gate = HumanInterventionGate()
    review = gate.request_human_review({
        "query_url": "Patient?bad=true",
        "user_id": "user-1",
        "validation_result": {"pattern_stats": {"human_threshold_met": True}},
    })
    resolved = gate.submit_review_decision(
        review["review_id"],
        reviewer="operator",
        decision="continue_monitoring",
        rationale="ok",
    )
    assert resolved["resumed"] is True


def test_human_gate_auth_required_rejects_missing_token(monkeypatch):
    monkeypatch.setenv("FHIR_HUMAN_GATE_REQUIRE_AUTH", "true")
    monkeypatch.setenv("FHIR_HUMAN_GATE_OPERATOR_TOKEN", "secret-operator-token")

    gate = HumanInterventionGate()
    review = gate.request_human_review({
        "query_url": "Patient?bad=true",
        "user_id": "user-2",
        "validation_result": {"pattern_stats": {"human_threshold_met": True}},
    })

    with pytest.raises(HumanGateAuthError):
        gate.submit_review_decision(
            review["review_id"],
            reviewer="operator",
            decision="continue_monitoring",
            rationale="blocked",
        )


def test_human_gate_auth_required_accepts_valid_token(monkeypatch):
    monkeypatch.setenv("FHIR_HUMAN_GATE_REQUIRE_AUTH", "true")
    monkeypatch.setenv("FHIR_HUMAN_GATE_OPERATOR_TOKEN", "secret-operator-token")

    gate = HumanInterventionGate()
    review = gate.request_human_review({
        "query_url": "Patient?bad=true",
        "user_id": "user-3",
        "validation_result": {"pattern_stats": {"human_threshold_met": True}},
    })

    resolved = gate.submit_review_decision(
        review["review_id"],
        reviewer="operator",
        decision="continue_monitoring",
        rationale="approved",
        operator_token="secret-operator-token",
    )
    assert resolved["resumed"] is True


def test_verify_human_gate_operator_raises_when_token_not_configured(monkeypatch):
    monkeypatch.setenv("FHIR_HUMAN_GATE_REQUIRE_AUTH", "true")
    monkeypatch.delenv("FHIR_HUMAN_GATE_OPERATOR_TOKEN", raising=False)

    with pytest.raises(HumanGateAuthError, match="not configured"):
        verify_human_gate_operator(operator_token="any", reviewer="operator")


def test_resolve_workflow_user_id_trusts_client_by_default(monkeypatch):
    monkeypatch.delenv("FHIR_TRUST_CLIENT_USER_ID", raising=False)
    assert resolve_workflow_user_id("demo-user", None) == "demo-user"


def test_resolve_workflow_user_id_derives_from_token_when_untrusted(monkeypatch):
    monkeypatch.setenv("FHIR_TRUST_CLIENT_USER_ID", "false")
    derived = resolve_workflow_user_id("spoofed-user", "bearer-token-123")
    assert derived.startswith("token:")
    assert derived != "spoofed-user"


@patch("src.agentic_layer.agents.cache_agent.CacheAgent.get_capability_statement")
def test_isolated_workflows_do_not_share_pattern_history(mock_get_capability, monkeypatch):
    mock_get_capability.return_value = {
        "resourceType": "CapabilityStatement",
        "rest": [{
            "resource": [{
                "type": "Patient",
                "searchParam": [{"name": "gender", "type": "token"}],
            }],
        }],
    }

    monkeypatch.setenv("FHIR_WORKFLOW_ISOLATE_STATE", "true")

    for _ in range(3):
        execute_workflow({
            "query_url": "Patient?not_a_real_param=true",
            "server_key": "hapi",
            "user_id": "isolated-learner",
            "mode": "validate_only",
        })

    isolated_state = execute_workflow({
        "query_url": "Patient?not_a_real_param=true",
        "server_key": "hapi",
        "user_id": "isolated-learner-2",
        "mode": "validate_only",
    })

    assert isolated_state.escalation_decision != "learner"

    shared_agents = get_workflow_agents(isolate=False)
    assert not shared_agents.validator._pattern_history