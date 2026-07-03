from unittest.mock import MagicMock, patch

import httpx

from src.agentic_layer.agents.query_execution import QueryExecutionAgent


def _mock_response(status_code: int, json_data: dict | None = None):
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = json_data or {}
    response.raise_for_status = MagicMock()
    if status_code >= 400:
        response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "error",
            request=MagicMock(),
            response=response,
        )
    return response


@patch("src.agentic_layer.agents.query_execution.httpx.Client")
def test_execute_success_includes_timing(mock_client_class):
    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.get.return_value = _mock_response(
        200,
        {"resourceType": "Bundle", "type": "searchset", "total": 3},
    )
    mock_client_class.return_value = mock_client

    agent = QueryExecutionAgent()
    result = agent.execute("Patient?gender=male", server_key="hapi")

    assert result["status"] == "success"
    assert result["total"] == 3
    assert result["bundle_type"] == "searchset"
    assert "elapsed_ms" in result
    mock_client.get.assert_called_once()
    call_kwargs = mock_client.get.call_args.kwargs
    assert "Authorization" not in call_kwargs["headers"]


@patch("src.agentic_layer.agents.query_execution.httpx.Client")
def test_execute_forwards_bearer_token(mock_client_class):
    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.get.return_value = _mock_response(
        200,
        {"resourceType": "Bundle", "type": "searchset", "total": 1},
    )
    mock_client_class.return_value = mock_client

    agent = QueryExecutionAgent()
    result = agent.execute(
        "Patient?gender=male",
        server_key="hapi",
        auth_token="test-bearer-token",
    )

    assert result["status"] == "success"
    headers = mock_client.get.call_args.kwargs["headers"]
    assert headers["Authorization"] == "Bearer test-bearer-token"


@patch("src.agentic_layer.agents.query_execution.httpx.Client")
def test_execute_forbidden_returns_authorization_error(mock_client_class):
    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.get.return_value = _mock_response(403)
    mock_client_class.return_value = mock_client

    agent = QueryExecutionAgent()
    result = agent.execute("Patient?gender=male", server_key="hapi", auth_token="limited-token")

    assert result["status"] == "error"
    assert result["error_type"] == "authorization_failed"
    assert result["http_status"] == 403


@patch("src.agentic_layer.agents.query_execution.httpx.Client")
def test_execute_auth_failure(mock_client_class):
    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.get.return_value = _mock_response(401)
    mock_client_class.return_value = mock_client

    agent = QueryExecutionAgent()
    result = agent.execute("Patient?gender=male", server_key="hapi", auth_token="bad-token")

    assert result["status"] == "error"
    assert result["error_type"] == "authentication_failed"
    assert result["http_status"] == 401


@patch("src.agentic_layer.agents.query_execution.httpx.Client")
def test_execute_http_status_error(mock_client_class):
    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.get.return_value = _mock_response(500)
    mock_client_class.return_value = mock_client

    agent = QueryExecutionAgent()
    result = agent.execute("Patient?gender=male", server_key="hapi")

    assert result["status"] == "error"
    assert result["error_type"] == "http_error"
    assert result["http_status"] == 500


@patch("src.agentic_layer.agents.query_execution.httpx.Client")
def test_execute_request_error(mock_client_class):
    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.get.side_effect = httpx.ConnectError("connection refused")
    mock_client_class.return_value = mock_client

    agent = QueryExecutionAgent()
    result = agent.execute("Patient?gender=male", server_key="hapi")

    assert result["status"] == "error"
    assert result["error_type"] == "request_failed"
    assert "connection refused" in result["message"]