"""
CacheAgent
Handles fetching and caching of CapabilityStatement with hybrid invalidation.
"""

import os
import time
from typing import Optional, Dict, Any

import httpx

from ..auth.provider import auth_cache_suffix
from ..config.settings import get_server_config, get_auth_headers


class CacheAgent:
    """
    Specialist agent responsible for CapabilityStatement caching.
    Supports TTL-based and conditional (ETag) invalidation with auth-aware keys.
    """

    def __init__(self, ttl_seconds: int = 7 * 24 * 3600):  # Default 7 days
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, Dict[str, Any]] = {}

    def _cache_key(self, server_key: str, auth_headers: dict[str, str]) -> str:
        return f"{server_key}{auth_cache_suffix(auth_headers)}"

    def _check_admin_invalidation(
        self,
        server_key: str,
        auth_token: Optional[str] = None,
    ) -> None:
        """Honor admin/config invalidation signals from environment."""
        global_flag = os.getenv("FHIR_CACHE_INVALIDATE", "false").lower() == "true"
        targeted = os.getenv("FHIR_CACHE_INVALIDATE_KEYS", "")
        targeted_keys = {k.strip() for k in targeted.split(",") if k.strip()}
        if global_flag or server_key in targeted_keys:
            self.invalidate(server_key, auth_token=auth_token)

    def get_capability_statement(
        self,
        server_key: Optional[str] = None,
        auth_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get CapabilityStatement. Uses cache if valid, otherwise fetches.
        """
        server = get_server_config(server_key)
        auth_headers = get_auth_headers(server, auth_token_override=auth_token)
        self._check_admin_invalidation(server.key, auth_token=auth_token)
        key = self._cache_key(server.key, auth_headers)

        now = time.time()

        if key in self._cache:
            cached = self._cache[key]
            age = now - cached["timestamp"]

            if age < self.ttl_seconds:
                result = self._fetch_from_server(
                    server,
                    auth_headers,
                    etag=cached.get("etag"),
                    cached_data=cached["data"],
                )
                if result is None:
                    print(f"[CacheAgent] Cache HIT (304) for '{key}' (age: {int(age)}s)")
                    return cached["data"]

                capability_statement, etag = result
                cached["data"] = capability_statement
                cached["etag"] = etag
                cached["timestamp"] = now
                print(f"[CacheAgent] Cache REFRESH for '{key}' (conditional miss)")
                return capability_statement

            print(f"[CacheAgent] Cache EXPIRED for '{key}' (age: {int(age)}s)")

        print(f"[CacheAgent] Cache MISS for '{key}' — fetching from {server.base_url}")
        capability_statement, etag = self._fetch_from_server(server, auth_headers)
        self._cache[key] = {
            "data": capability_statement,
            "timestamp": now,
            "etag": etag,
        }
        return capability_statement

    def _fetch_from_server(
        self,
        server,
        auth_headers: dict[str, str],
        etag: Optional[str] = None,
        cached_data: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Fetch CapabilityStatement from FHIR server.

        When etag is provided, sends a conditional request and returns None on 304.
        Otherwise returns (capability_statement, etag).
        """
        url = f"{server.base_url}/metadata"
        headers = {
            "Accept": "application/fhir+json, application/json",
            **auth_headers,
        }
        if etag:
            headers["If-None-Match"] = etag

        with httpx.Client(timeout=30.0) as client:
            response = client.get(url, headers=headers)

            if response.status_code == 304 and cached_data is not None:
                return None

            response.raise_for_status()
            return response.json(), response.headers.get("ETag")

    def invalidate(self, server_key: str, auth_token: Optional[str] = None):
        """Force invalidation of cache for a server (auth-scoped when provided)."""
        server = get_server_config(server_key)
        auth_headers = get_auth_headers(server, auth_token_override=auth_token)
        key = self._cache_key(server.key, auth_headers)
        if key in self._cache:
            del self._cache[key]
            print(f"[CacheAgent] Cache invalidated for '{key}'")