"""Shared fixtures for integration tests."""

from unittest.mock import MagicMock

import httpx
import pytest

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


@pytest.fixture
def patient_capability():
    return PATIENT_CAPABILITY


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