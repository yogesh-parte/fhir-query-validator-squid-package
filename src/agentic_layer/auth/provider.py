"""
Authentication providers for FHIR server requests.

Supports static Bearer tokens and OAuth2 client credentials (via authlib).
"""

from __future__ import annotations

import hashlib
from typing import Optional, Protocol

from authlib.integrations.httpx_client import OAuth2Client


class AuthProvider(Protocol):
    """Protocol for resolving Authorization headers."""

    def get_headers(self) -> dict[str, str]:
        ...


class BearerTokenProvider:
    """Static Bearer token authentication."""

    def __init__(self, token: str) -> None:
        self._token = token

    def get_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._token}"}


class OAuth2ClientCredentialsProvider:
    """OAuth2 client credentials flow with in-memory token reuse."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        token_url: str,
        scope: Optional[str] = None,
    ) -> None:
        self._client = OAuth2Client(client_id=client_id, client_secret=client_secret)
        self._token_url = token_url
        self._scope = scope
        self._headers: Optional[dict[str, str]] = None

    def get_headers(self) -> dict[str, str]:
        if self._headers is not None:
            return dict(self._headers)
        token = self._client.fetch_token(self._token_url, scope=self._scope)
        self._headers = {"Authorization": f"Bearer {token['access_token']}"}
        return dict(self._headers)


def build_auth_provider(settings: dict) -> Optional[AuthProvider]:
    """Build an auth provider from application settings."""
    if not settings.get("use_auth"):
        return None

    auth_type = (settings.get("auth_type") or "bearer").lower()

    if auth_type == "oauth2":
        client_id = settings.get("oauth_client_id")
        client_secret = settings.get("oauth_client_secret")
        token_url = settings.get("oauth_token_url")
        if client_id and client_secret and token_url:
            return OAuth2ClientCredentialsProvider(
                client_id=client_id,
                client_secret=client_secret,
                token_url=token_url,
                scope=settings.get("oauth_scope"),
            )
        return None

    token = settings.get("auth_token")
    if token:
        return BearerTokenProvider(token)
    return None


def resolve_auth_headers(
    requires_auth: bool,
    settings: dict,
    auth_token_override: Optional[str] = None,
    provider: Optional[AuthProvider] = None,
) -> dict[str, str]:
    """
    Resolve HTTP headers for authenticated requests.

    Priority: explicit override token > configured provider > static env token.
    """
    if auth_token_override:
        return {"Authorization": f"Bearer {auth_token_override}"}

    if not requires_auth:
        return {}

    if provider is None:
        provider = build_auth_provider(settings)

    if provider is not None:
        return provider.get_headers()

    token = settings.get("auth_token")
    if token:
        return {"Authorization": f"Bearer {token}"}

    return {}


def auth_cache_suffix(auth_headers: dict[str, str]) -> str:
    """Derive a stable cache suffix from auth context (avoids cross-user leakage)."""
    if not auth_headers:
        return ""
    auth_value = auth_headers.get("Authorization", "")
    digest = hashlib.sha256(auth_value.encode()).hexdigest()[:16]
    return f":auth:{digest}"