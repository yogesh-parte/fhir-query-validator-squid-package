"""Shared fixtures for integration tests (mock and live)."""

from __future__ import annotations

import os
from unittest.mock import MagicMock

import httpx
import pytest

from src.agentic_layer.config.settings import get_server_config

PUBLIC_SERVER_KEYS = ("hapi", "firely", "spark")
LIVE_METADATA_TIMEOUT = 15.0

PATIENT_CAPABILITY = {
    "resourceType": "CapabilityStatement",
    "rest": [
        {
            "resource": [
                {
                    "type": "Patient",
                    "searchParam": [
                        {"name": "gender", "type": "token"},
                        {"name": "subject", "type": "reference"},
                    ],
                }
            ],
        }
    ],
}


@pytest.fixture
def patient_capability():
    return PATIENT_CAPABILITY


def metadata_url(server_key: str) -> str:
    """Return the CapabilityStatement metadata URL for a registered server."""
    server = get_server_config(server_key)
    return f"{server.base_url.rstrip('/')}/metadata"


def is_server_reachable(server_key: str, timeout: float = LIVE_METADATA_TIMEOUT) -> bool:
    """Return True when a server's metadata endpoint responds with HTTP 200."""
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            response = client.get(metadata_url(server_key))
            return response.status_code == 200
    except httpx.HTTPError:
        return False


def require_reachable_server(server_key: str) -> None:
    """Skip the current test when the target FHIR server is offline."""
    if not is_server_reachable(server_key):
        pytest.skip(f"FHIR server '{server_key}' is unreachable")


def require_mockhealth_api_key() -> str:
    """Skip unless MOCK_HEALTH_API_KEY is configured."""
    api_key = os.getenv("MOCK_HEALTH_API_KEY")
    if not api_key:
        pytest.skip("MOCK_HEALTH_API_KEY not set — skipping mock.health live test")
    return api_key


@pytest.fixture
def reachable_public_servers() -> list[str]:
    """Yield public server keys that respond to metadata requests."""
    online = [key for key in PUBLIC_SERVER_KEYS if is_server_reachable(key)]
    if not online:
        pytest.skip("No public FHIR test servers are reachable")
    return online


def mock_http_response(status_code: int, json_data: dict | None = None):
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = json_data or {}
    response.headers = {"ETag": 'W/"etag-1"'}
    response.raise_for_status = MagicMock()
    if status_code >= 400:
        response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "http error",
            request=MagicMock(),
            response=response,
        )
    return response


def mock_shared_httpx_client(
    capability: dict | None = None,
    bundle: dict | None = None,
):
    """
    Build one httpx.Client mock for cache + execution agents.

    Both agents import httpx.Client from the shared httpx module, so patching
    each module separately leaves only the last patch active.
    """
    capability = capability or PATIENT_CAPABILITY
    bundle = bundle or {
        "resourceType": "Bundle",
        "type": "searchset",
        "total": 4,
    }

    http = MagicMock()
    http.__enter__.return_value = http

    def get_side_effect(url: str, **kwargs):
        if "/metadata" in url:
            return mock_http_response(200, capability)
        return mock_http_response(200, bundle)

    http.get.side_effect = get_side_effect
    return http
