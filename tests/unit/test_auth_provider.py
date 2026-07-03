import os
from unittest.mock import MagicMock, patch

import pytest

from src.agentic_layer.auth.provider import (
    BearerTokenProvider,
    OAuth2ClientCredentialsProvider,
    auth_cache_suffix,
    build_auth_provider,
    resolve_auth_headers,
)


def test_bearer_token_provider_headers():
    provider = BearerTokenProvider("secret-token")
    assert provider.get_headers() == {"Authorization": "Bearer secret-token"}


def test_build_auth_provider_bearer():
    settings = {
        "use_auth": True,
        "auth_type": "bearer",
        "auth_token": "static-token",
    }
    provider = build_auth_provider(settings)
    assert provider is not None
    assert provider.get_headers() == {"Authorization": "Bearer static-token"}


def test_build_auth_provider_oauth2():
    settings = {
        "use_auth": True,
        "auth_type": "oauth2",
        "oauth_client_id": "client-id",
        "oauth_client_secret": "client-secret",
        "oauth_token_url": "https://auth.example.com/token",
        "oauth_scope": "fhir.read",
    }
    provider = build_auth_provider(settings)
    assert isinstance(provider, OAuth2ClientCredentialsProvider)


def test_build_auth_provider_returns_none_without_credentials():
    settings = {"use_auth": True, "auth_type": "bearer", "auth_token": None}
    assert build_auth_provider(settings) is None


def test_build_auth_provider_oauth2_missing_fields_returns_none():
    settings = {
        "use_auth": True,
        "auth_type": "oauth2",
        "oauth_client_id": "id",
        "oauth_client_secret": None,
        "oauth_token_url": "https://auth.example.com/token",
    }
    assert build_auth_provider(settings) is None


def test_build_auth_provider_disabled_when_use_auth_false():
    assert build_auth_provider({"use_auth": False, "auth_token": "ignored"}) is None


def test_resolve_auth_headers_uses_provider_when_configured():
    provider = BearerTokenProvider("provider-token")
    settings = {"use_auth": True, "auth_type": "bearer", "auth_token": "env-token"}
    headers = resolve_auth_headers(
        requires_auth=True,
        settings=settings,
        provider=provider,
    )
    assert headers == {"Authorization": "Bearer provider-token"}


def test_resolve_auth_headers_falls_back_to_static_token():
    settings = {"use_auth": True, "auth_type": "bearer", "auth_token": "env-token"}
    headers = resolve_auth_headers(requires_auth=True, settings=settings)
    assert headers == {"Authorization": "Bearer env-token"}


def test_resolve_auth_headers_returns_empty_when_auth_required_but_unconfigured():
    settings = {"use_auth": True, "auth_type": "bearer", "auth_token": None}
    assert resolve_auth_headers(requires_auth=True, settings=settings) == {}


def test_resolve_auth_headers_override_takes_priority():
    settings = {"use_auth": True, "auth_type": "bearer", "auth_token": "env-token"}
    headers = resolve_auth_headers(
        requires_auth=True,
        settings=settings,
        auth_token_override="override-token",
    )
    assert headers == {"Authorization": "Bearer override-token"}


def test_resolve_auth_headers_public_server():
    settings = {"use_auth": False}
    assert resolve_auth_headers(requires_auth=False, settings=settings) == {}


@patch("src.agentic_layer.auth.provider.OAuth2Client")
def test_oauth2_provider_fetches_token(mock_oauth_client):
    mock_client = MagicMock()
    mock_client.fetch_token.return_value = {"access_token": "oauth-access-token"}
    mock_oauth_client.return_value = mock_client

    provider = OAuth2ClientCredentialsProvider(
        client_id="id",
        client_secret="secret",
        token_url="https://auth.example.com/token",
        scope="fhir.read",
    )
    assert provider.get_headers() == {"Authorization": "Bearer oauth-access-token"}
    mock_client.fetch_token.assert_called_once_with(
        "https://auth.example.com/token",
        scope="fhir.read",
    )


@patch("src.agentic_layer.auth.provider.OAuth2Client")
def test_oauth2_provider_reuses_cached_token(mock_oauth_client):
    mock_client = MagicMock()
    mock_client.fetch_token.return_value = {"access_token": "oauth-access-token"}
    mock_oauth_client.return_value = mock_client

    provider = OAuth2ClientCredentialsProvider(
        client_id="id",
        client_secret="secret",
        token_url="https://auth.example.com/token",
    )
    provider.get_headers()
    provider.get_headers()
    mock_client.fetch_token.assert_called_once()


def test_auth_cache_suffix_empty_without_auth():
    assert auth_cache_suffix({}) == ""


def test_auth_cache_suffix_differs_by_token():
    suffix_a = auth_cache_suffix({"Authorization": "Bearer token-a"})
    suffix_b = auth_cache_suffix({"Authorization": "Bearer token-b"})
    assert suffix_a != suffix_b
    assert suffix_a.startswith(":auth:")


def test_get_auth_provider_caches_provider(monkeypatch):
    monkeypatch.setenv("FHIR_USE_AUTH", "true")
    monkeypatch.setenv("FHIR_AUTH_TYPE", "bearer")
    monkeypatch.setenv("FHIR_AUTH_TOKEN", "cached-token")

    from src.agentic_layer.config import settings as settings_module

    settings_module._auth_provider_cache = None
    first = settings_module.get_auth_provider()
    second = settings_module.get_auth_provider()
    assert first is second