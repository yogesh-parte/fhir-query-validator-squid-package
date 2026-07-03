"""
Configuration loader for fhir-query-validator-factory.
Supports multiple servers via server_key and basic authentication.
"""

import os
from dataclasses import dataclass
from typing import Dict, Optional

from ..auth.provider import AuthProvider, build_auth_provider, resolve_auth_headers
from ..exceptions import UnknownServerKeyError


def _load_env_files() -> None:
    """
    Load secrets from local env files without committing them to git.

    Priority (later files do not override earlier ones):
      1. .env.local  — developer secrets (git-ignored)
      2. .env        — optional shared non-secret defaults (git-ignored)
    """
    try:
        from dotenv import load_dotenv
    except ImportError:
        return

    load_dotenv(".env.local", override=False)
    load_dotenv(".env", override=False)


_load_env_files()

# Built-in public test servers (immutable — never mutated at runtime).
BASE_SERVERS: Dict[str, dict] = {
    "hapi": {
        "name": "HAPI FHIR",
        "base_url": "https://hapi.fhir.org/baseR4",
        "requires_auth": False,
    },
    "firely": {
        "name": "Firely",
        "base_url": "https://server.fire.ly/R4",
        "requires_auth": False,
    },
    "spark": {
        "name": "Spark",
        "base_url": "https://spark.fhir.org/r4",
        "requires_auth": False,
    },
    "wildfhir": {
        "name": "WildFHIR",
        "base_url": "https://wildfhir4.wildfhir.org/r4",
        "requires_auth": False,
    },
    "mockhealth": {
        "name": "mock.health",
        "base_url": "https://api.mock.health/fhir",
        "requires_auth": True,
        # Per-server secret — set in .env.local, never commit to git.
        # Obtain a key at https://mock.health/docs
        "auth_token_env": "MOCK_HEALTH_API_KEY",
    },
}

# Backward-compatible alias for docs and callers that import DEFAULT_SERVERS.
DEFAULT_SERVERS = BASE_SERVERS


@dataclass
class ServerConfig:
    key: str
    name: str
    base_url: str
    requires_auth: bool = False
    auth_token: Optional[str] = None


_auth_provider_cache: Optional[AuthProvider] = None


def get_settings() -> dict:
    """Load settings from environment variables."""
    return {
        "default_server_key": os.getenv("FHIR_DEFAULT_SERVER_KEY", "hapi"),
        "server_base": os.getenv("FHIR_SERVER_BASE"),
        "use_auth": os.getenv("FHIR_USE_AUTH", "false").lower() == "true",
        "auth_type": os.getenv("FHIR_AUTH_TYPE", "bearer"),
        "auth_token": os.getenv("FHIR_AUTH_TOKEN"),
        "oauth_client_id": os.getenv("OAUTH_CLIENT_ID"),
        "oauth_client_secret": os.getenv("OAUTH_CLIENT_SECRET"),
        "oauth_token_url": os.getenv("OAUTH_TOKEN_URL"),
        "oauth_scope": os.getenv("OAUTH_SCOPE"),
    }


def _resolve_server_auth_token(server_info: dict, settings: dict) -> Optional[str]:
    """Resolve a server-specific API key/token from its dedicated env var."""
    env_var = server_info.get("auth_token_env")
    if env_var:
        return os.getenv(env_var)
    if server_info.get("requires_auth"):
        return settings.get("auth_token")
    return None


def _server_registry(settings: dict) -> Dict[str, dict]:
    """Return a fresh registry snapshot; optionally overlay a protected server."""
    registry = dict(BASE_SERVERS)
    if settings.get("use_auth") and settings.get("server_base"):
        registry["protected"] = {
            "name": "Protected FHIR Server",
            "base_url": settings["server_base"].rstrip("/"),
            "requires_auth": True,
        }
    return registry


def get_auth_provider() -> Optional[AuthProvider]:
    """Return a cached auth provider built from current settings."""
    global _auth_provider_cache
    settings = get_settings()
    if not settings.get("use_auth"):
        _auth_provider_cache = None
        return None
    if _auth_provider_cache is None:
        _auth_provider_cache = build_auth_provider(settings)
    return _auth_provider_cache


def get_auth_headers(
    server: ServerConfig,
    auth_token_override: Optional[str] = None,
) -> dict[str, str]:
    """Resolve Authorization headers for a server request."""
    if auth_token_override:
        return {"Authorization": f"Bearer {auth_token_override}"}

    if not server.requires_auth:
        return {}

    if server.auth_token:
        return {"Authorization": f"Bearer {server.auth_token}"}

    settings = get_settings()
    return resolve_auth_headers(
        requires_auth=server.requires_auth,
        settings=settings,
        auth_token_override=None,
        provider=get_auth_provider(),
    )


def get_server_config(server_key: Optional[str] = None) -> ServerConfig:
    """
    Get server configuration by key.
    Raises UnknownServerKeyError when an explicit unknown key is provided.
    """
    settings = get_settings()
    registry = _server_registry(settings)

    key = server_key or settings["default_server_key"]
    if settings.get("use_auth") and key not in registry and settings.get("server_base"):
        key = "protected"

    if server_key and server_key not in registry:
        raise UnknownServerKeyError(
            f"Unknown server_key '{server_key}'. "
            f"Registered keys: {', '.join(sorted(registry.keys()))}"
        )

    if key not in registry:
        raise UnknownServerKeyError(
            f"Default server_key '{key}' is not registered. "
            f"Registered keys: {', '.join(sorted(registry.keys()))}"
        )

    server_info = registry[key]
    requires_auth = server_info.get("requires_auth", False) or (
        settings.get("use_auth", False) and key == "protected"
    )
    auth_token = _resolve_server_auth_token(server_info, settings) if requires_auth else None

    return ServerConfig(
        key=key,
        name=server_info["name"],
        base_url=server_info["base_url"],
        requires_auth=requires_auth,
        auth_token=auth_token,
    )