"""Additional unit tests to reach ≥99% coverage on src/agentic_layer."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.agentic_layer.agents.cache_agent import CacheAgent
from src.agentic_layer.agents.query_generator_agent import QueryGeneratorAgent
from src.agentic_layer.auth.identity import resolve_workflow_user_id
from src.agentic_layer.auth.operator import HumanGateAuthError, verify_human_gate_operator
from src.agentic_layer.auth.provider import resolve_auth_headers
from src.agentic_layer.config.settings import get_server_config
from src.agentic_layer.graph.validation_workflow import run_validation_workflow
from src.agentic_layer.graph.workflow_engine import execute_workflow
from src.agentic_layer.state.workflow_state import ValidationWorkflowState
from src.agentic_layer.utils import logging_safe
from src.agentic_layer.utils.audit_log import AuditLog
from src.agentic_layer.utils.fhir_resource_registry import (
    SearchParamSpec,
    encode_search_value,
    get_resource_spec,
    registry_metadata,
)
from src.agentic_layer.utils.url_safety import UnsafeQueryUrlError, build_fhir_target_url

CAPABILITY = {
    "resourceType": "CapabilityStatement",
    "rest": [
        {
            "resource": [
                {
                    "type": "Patient",
                    "searchParam": [{"name": "gender", "type": "token"}],
                }
            ],
        }
    ],
}


# --- logging_safe ---


def test_verbose_logging_disabled_by_env(monkeypatch):
    monkeypatch.setenv("FHIR_VERBOSE_LOGGING", "false")
    assert logging_safe.verbose_logging_enabled() is False


def test_format_query_log_label_redacts_when_not_verbose(monkeypatch):
    monkeypatch.setenv("FHIR_VERBOSE_LOGGING", "false")
    label = logging_safe.format_query_log_label("Patient?gender=male&active=true")
    assert label == "Patient?[active,gender]"


def test_format_query_log_label_redacts_resource_only(monkeypatch):
    monkeypatch.setenv("FHIR_VERBOSE_LOGGING", "false")
    assert logging_safe.format_query_log_label("Patient") == "Patient"


def test_format_query_log_label_returns_redacted_on_parse_failure(monkeypatch):
    monkeypatch.setenv("FHIR_VERBOSE_LOGGING", "false")
    with patch(
        "src.agentic_layer.utils.logging_safe.parse_query_url",
        side_effect=ValueError("bad"),
    ):
        assert logging_safe.format_query_log_label("???") == "(redacted-query)"


# --- url_safety ---


def test_build_fhir_target_url_rejects_empty_query():
    with pytest.raises(UnsafeQueryUrlError, match="empty"):
        build_fhir_target_url("https://hapi.fhir.org/baseR4", "   ")


def test_build_fhir_target_url_rejects_invalid_base():
    with pytest.raises(UnsafeQueryUrlError, match="Invalid server base_url"):
        build_fhir_target_url("not-a-url", "Patient")


def test_build_fhir_target_url_rejects_invalid_scheme_after_join(monkeypatch):
    with (
        patch(
            "src.agentic_layer.utils.url_safety.urljoin",
            return_value="file:///etc/passwd",
        ),
        pytest.raises(UnsafeQueryUrlError, match="Invalid URL scheme"),
    ):
        build_fhir_target_url("https://hapi.fhir.org/baseR4", "Patient")


def test_build_fhir_target_url_rejects_netloc_mismatch(monkeypatch):
    with (
        patch(
            "src.agentic_layer.utils.url_safety.urljoin",
            return_value="https://evil.example/Patient",
        ),
        pytest.raises(UnsafeQueryUrlError, match="outside server base_url"),
    ):
        build_fhir_target_url("https://hapi.fhir.org/baseR4", "Patient")


# --- fhir_resource_registry ---


def test_search_param_spec_to_dict_includes_comparators():
    spec = SearchParamSpec(name="date", type="date", comparators=("ge", "le"))
    payload = spec.to_dict()
    assert payload["comparators"] == ["ge", "le"]


def test_search_param_spec_to_dict_omits_empty_comparators():
    spec = SearchParamSpec(name="gender", type="token")
    payload = spec.to_dict()
    assert "comparators" not in payload


def test_resource_spec_to_dict():
    spec = get_resource_spec("Patient")
    payload = spec.to_dict()
    assert payload["resource_type"] == "Patient"
    assert isinstance(payload["search_params"], list)


def test_registry_metadata_returns_source_fields():
    meta = registry_metadata()
    assert "fhir_version" in meta
    assert "source_resource_list" in meta


def test_get_resource_spec_rejects_empty_type():
    with pytest.raises(ValueError, match="must not be empty"):
        get_resource_spec("   ")


def test_encode_search_value_rejects_invalid_comparator():
    param = SearchParamSpec(name="date", type="date", comparators=("ge",))
    with pytest.raises(ValueError, match="Comparator"):
        encode_search_value(param, {"comparator": "zz", "value": "2020"})


def test_encode_search_value_dict_without_comparator():
    param = SearchParamSpec(name="gender", type="token")
    assert encode_search_value(param, {"value": "male"}) == "male"


def test_encode_search_value_preserves_existing_comparator_prefix():
    param = SearchParamSpec(name="date", type="date", comparators=("ge", "le"))
    assert encode_search_value(param, "ge2020-01-01") == "ge2020-01-01"


def test_encode_search_value_quotes_plain_strings():
    param = SearchParamSpec(name="gender", type="token")
    assert encode_search_value(param, "male") == "male"


# --- query_generator_agent ---


def test_query_generator_list_resources():
    agent = QueryGeneratorAgent()
    payload = agent.list_resources()
    assert "resource_types" in payload
    assert "Patient" in payload["resource_types"]


def test_query_generator_describe_resource():
    agent = QueryGeneratorAgent()
    payload = agent.describe_resource("Patient")
    assert payload["resource_type"] == "Patient"
    assert "search_params" in payload


def test_query_generator_generate_with_sort():
    agent = QueryGeneratorAgent()
    result = agent.generate("Patient", {"gender": "male"}, sort="birthdate")
    assert "_sort=birthdate" in result["query_url"]


def test_query_generator_generate_value_error_becomes_error_message():
    agent = QueryGeneratorAgent()
    with patch(
        "src.agentic_layer.agents.query_generator_agent.encode_search_value",
        side_effect=ValueError("bad value"),
    ):
        result = agent.generate("Patient", {"gender": "male"})
    assert result["generated"] is False
    assert "bad value" in result["errors"][0]


def test_generate_from_intent_unknown_intent():
    agent = QueryGeneratorAgent()
    result = agent.generate_from_intent("Patient", "totally unknown intent")
    assert result["generated"] is False
    assert "Unknown intent" in result["errors"][0]


def test_generate_from_intent_wrong_resource_type():
    agent = QueryGeneratorAgent()
    result = agent.generate_from_intent("Observation", "male patients")
    assert result["generated"] is False
    assert "does not apply" in result["errors"][0]


# --- cache_agent expired log line ---


@patch("src.agentic_layer.agents.cache_agent.httpx.Client")
@patch("src.agentic_layer.agents.cache_agent.time.time")
def test_cache_expired_logs_and_refetches(mock_time, mock_client_class, capsys):
    mock_time.side_effect = [100.0, 200.0]
    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = CAPABILITY
    response.headers = {"ETag": 'W/"e"'}
    response.raise_for_status = MagicMock()
    mock_client.get.return_value = response
    mock_client_class.return_value = mock_client

    agent = CacheAgent(ttl_seconds=60)
    agent.get_capability_statement("hapi")
    agent.get_capability_statement("hapi")

    captured = capsys.readouterr().out
    assert "Cache EXPIRED" in captured
    assert mock_client.get.call_count == 2


# --- auth / settings ---


def test_resolve_workflow_user_id_returns_none_without_token(monkeypatch):
    monkeypatch.setenv("FHIR_TRUST_CLIENT_USER_ID", "false")
    assert resolve_workflow_user_id("ignored", None) is None


def test_verify_human_gate_operator_rejects_blank_reviewer(monkeypatch):
    monkeypatch.setenv("FHIR_HUMAN_GATE_REQUIRE_AUTH", "true")
    monkeypatch.setenv("FHIR_HUMAN_GATE_OPERATOR_TOKEN", "secret")
    with pytest.raises(HumanGateAuthError, match="Reviewer identity"):
        verify_human_gate_operator(operator_token="secret", reviewer="   ")


def test_resolve_auth_headers_uses_static_token_without_provider():
    headers = resolve_auth_headers(
        requires_auth=True,
        settings={"auth_token": "static-token"},
        auth_token_override=None,
        provider=None,
    )
    assert headers == {"Authorization": "Bearer static-token"}


def test_protected_server_uses_global_auth_token(monkeypatch):
    monkeypatch.setenv("FHIR_USE_AUTH", "true")
    monkeypatch.setenv("FHIR_SERVER_BASE", "https://fhir.example.com/R4")
    monkeypatch.setenv("FHIR_AUTH_TOKEN", "protected-token")
    config = get_server_config("protected")
    assert config.auth_token == "protected-token"


def test_protected_server_without_auth_token_env_var(monkeypatch):
    monkeypatch.setenv("FHIR_USE_AUTH", "true")
    monkeypatch.setenv("FHIR_SERVER_BASE", "https://fhir.example.com/R4")
    monkeypatch.delenv("FHIR_AUTH_TOKEN", raising=False)
    config = get_server_config("protected")
    assert config.requires_auth is True
    assert config.auth_token is None


def test_load_env_files_handles_missing_dotenv(monkeypatch):
    import builtins

    import src.agentic_layer.config.settings as settings_module

    real_import = builtins.__import__

    def mock_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "dotenv":
            raise ImportError("no dotenv")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", mock_import)
    settings_module._load_env_files()


# --- validation_workflow ---


@patch("src.agentic_layer.graph.workflow_engine.cache_agent.get_capability_statement")
def test_run_validation_workflow_accepts_state_model(mock_get_capability):
    mock_get_capability.return_value = CAPABILITY
    state = ValidationWorkflowState(
        query_url="Patient?gender=male",
        server_key="hapi",
        mode="validate_only",
    )
    result = run_validation_workflow(state)
    assert result["final_output"]["valid"] is True


# --- workflow_engine query generation paths ---


def test_execute_workflow_query_generation_missing_resource_type():
    state = execute_workflow(
        {
            "query_generation": {"criteria": {"gender": "male"}},
            "server_key": "hapi",
            "mode": "validate_only",
        }
    )
    assert state.workflow_error is not None
    assert "resource_type" in state.workflow_error


@patch("src.agentic_layer.graph.workflow_engine.cache_agent.get_capability_statement")
def test_execute_workflow_query_generation_from_intent(mock_get_capability):
    mock_get_capability.return_value = CAPABILITY
    state = execute_workflow(
        {
            "query_generation": {
                "resource_type": "Patient",
                "intent": "male patients",
            },
            "server_key": "hapi",
            "mode": "validate_only",
        }
    )
    assert state.query_url is not None
    assert "gender=male" in state.query_url


def test_execute_workflow_query_generation_failure():
    state = execute_workflow(
        {
            "query_generation": {
                "resource_type": "Patient",
                "criteria": {"not_a_real_param": "x"},
            },
            "server_key": "hapi",
            "mode": "validate_only",
        }
    )
    assert state.final_output["valid"] is False
    assert state.validation_result["error_types"] == ["query_generation_failed"]


# --- audit_log ---


def test_audit_log_load_no_op_when_file_missing(tmp_path):
    missing = tmp_path / "does-not-exist.jsonl"
    log = AuditLog(persist_path=str(missing))
    assert log.query() == []


# --- query_validator chained parameter branch ---


@patch("src.agentic_layer.graph.workflow_engine.cache_agent.get_capability_statement")
def test_execute_workflow_chained_unknown_root_parameter(mock_get_capability):
    mock_get_capability.return_value = {
        "resourceType": "CapabilityStatement",
        "rest": [
            {
                "resource": [
                    {
                        "type": "Patient",
                        "searchParam": [{"name": "name", "type": "string"}],
                    }
                ],
            }
        ],
    }
    state = execute_workflow(
        {
            "query_url": "Patient?unknown.chain=value",
            "server_key": "hapi",
            "mode": "validate_only",
        }
    )
    assert state.final_output["valid"] is False
    assert any("unknown" in err.lower() for err in state.final_output["errors"])
