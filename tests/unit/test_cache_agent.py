from unittest.mock import MagicMock, patch

import pytest

from src.agentic_layer.agents.cache_agent import CacheAgent


def _mock_response(status_code: int, json_data: dict | None = None, etag: str | None = None):
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = json_data or {}
    response.headers = {"ETag": etag} if etag else {}
    response.raise_for_status = MagicMock()
    return response


CAPABILITY = {
    "resourceType": "CapabilityStatement",
    "status": "active",
    "software": {"name": "HAPI FHIR"},
}


@patch("src.agentic_layer.agents.cache_agent.httpx.Client")
def test_cache_miss_then_hit(mock_client_class):
    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.get.return_value = _mock_response(200, CAPABILITY, 'W/"etag-1"')
    mock_client_class.return_value = mock_client

    agent = CacheAgent(ttl_seconds=60)

    result1 = agent.get_capability_statement("hapi")
    result2 = agent.get_capability_statement("hapi")

    assert result1["resourceType"] == "CapabilityStatement"
    assert result2 == result1
    assert mock_client.get.call_count == 2


@patch("src.agentic_layer.agents.cache_agent.httpx.Client")
def test_cache_sends_authorization_header(mock_client_class):
    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.get.return_value = _mock_response(200, CAPABILITY, 'W/"etag-1"')
    mock_client_class.return_value = mock_client

    agent = CacheAgent(ttl_seconds=60)
    agent.get_capability_statement("hapi", auth_token="secret-token")

    headers = mock_client.get.call_args.kwargs["headers"]
    assert headers["Authorization"] == "Bearer secret-token"


@patch("src.agentic_layer.agents.cache_agent.httpx.Client")
def test_auth_scoped_cache_keys_are_isolated(mock_client_class):
    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.get.return_value = _mock_response(200, CAPABILITY, 'W/"etag-1"')
    mock_client_class.return_value = mock_client

    agent = CacheAgent(ttl_seconds=60)
    agent.get_capability_statement("hapi", auth_token="token-a")
    agent.get_capability_statement("hapi", auth_token="token-b")

    assert len(agent._cache) == 2


@patch("src.agentic_layer.agents.cache_agent.httpx.Client")
def test_cache_handles_304_not_modified(mock_client_class):
    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.get.side_effect = [
        _mock_response(200, CAPABILITY, 'W/"etag-1"'),
        _mock_response(304, CAPABILITY, 'W/"etag-1"'),
    ]
    mock_client_class.return_value = mock_client

    agent = CacheAgent(ttl_seconds=60)
    first = agent.get_capability_statement("hapi")
    second = agent.get_capability_statement("hapi")

    assert first == second
    assert mock_client.get.call_count == 2
    assert "If-None-Match" in mock_client.get.call_args_list[1].kwargs["headers"]


def test_invalidate_removes_auth_scoped_entry():
    agent = CacheAgent(ttl_seconds=60)
    key = agent._cache_key("hapi", {"Authorization": "Bearer token"})
    agent._cache[key] = {"data": CAPABILITY, "timestamp": 0, "etag": "etag"}
    agent.invalidate("hapi", auth_token="token")
    assert key not in agent._cache


@patch("src.agentic_layer.agents.cache_agent.httpx.Client")
def test_admin_global_invalidation_refetches(mock_client_class, monkeypatch):
    monkeypatch.setenv("FHIR_CACHE_INVALIDATE", "true")
    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.get.return_value = _mock_response(200, CAPABILITY, 'W/"etag-1"')
    mock_client_class.return_value = mock_client

    agent = CacheAgent(ttl_seconds=60)
    agent.get_capability_statement("hapi")
    agent.get_capability_statement("hapi")

    assert mock_client.get.call_count == 2


@patch("src.agentic_layer.agents.cache_agent.httpx.Client")
def test_admin_targeted_invalidation_refetches(mock_client_class, monkeypatch):
    monkeypatch.setenv("FHIR_CACHE_INVALIDATE_KEYS", "hapi")
    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.get.return_value = _mock_response(200, CAPABILITY, 'W/"etag-1"')
    mock_client_class.return_value = mock_client

    agent = CacheAgent(ttl_seconds=60)
    agent.get_capability_statement("hapi")
    agent.get_capability_statement("hapi")

    assert mock_client.get.call_count == 2


@patch("src.agentic_layer.agents.cache_agent.httpx.Client")
@patch("src.agentic_layer.agents.cache_agent.time.time")
def test_cache_expired_refetches(mock_time, mock_client_class):
    mock_time.side_effect = [100.0, 100.0, 200.0, 200.0]
    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.get.return_value = _mock_response(200, CAPABILITY, 'W/"etag-1"')
    mock_client_class.return_value = mock_client

    agent = CacheAgent(ttl_seconds=60)
    first = agent.get_capability_statement("hapi")
    second = agent.get_capability_statement("hapi")

    assert first == second
    assert mock_client.get.call_count == 2