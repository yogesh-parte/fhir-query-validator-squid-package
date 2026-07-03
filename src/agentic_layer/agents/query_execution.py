"""
QueryExecutionAgent
Executes validated FHIR search queries.
"""

import time
from typing import Dict, Any, Optional

import httpx

from ..config.settings import get_server_config, get_auth_headers
from ..utils.logging_safe import format_query_log_label
from ..utils.url_safety import UnsafeQueryUrlError, build_fhir_target_url


class QueryExecutionAgent:
    """
    Executes FHIR queries after successful validation.
    """

    def execute(
        self,
        query_url: str,
        server_key: Optional[str] = None,
        auth_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute the query against the FHIR server.
        """
        server = get_server_config(server_key)
        auth_headers = get_auth_headers(server, auth_token_override=auth_token)

        try:
            target_url = build_fhir_target_url(server.base_url, query_url)
        except UnsafeQueryUrlError as exc:
            return {
                "executed": False,
                "status": "error",
                "error_type": "invalid_query_url",
                "message": str(exc),
            }

        log_label = format_query_log_label(query_url)
        print(f"[QueryExecution] Executing query on {server.name}: {log_label}")

        headers = {
            "Accept": "application/fhir+json, application/json",
            **auth_headers,
        }

        start = time.perf_counter()
        try:
            with httpx.Client(timeout=30.0, follow_redirects=False) as client:
                response = client.get(target_url, headers=headers)
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)

            if response.status_code == 401:
                return {
                    "executed": True,
                    "status": "error",
                    "error_type": "authentication_failed",
                    "message": "Server rejected credentials (401 Unauthorized)",
                    "http_status": 401,
                    "elapsed_ms": elapsed_ms,
                }

            if response.status_code == 403:
                return {
                    "executed": True,
                    "status": "error",
                    "error_type": "authorization_failed",
                    "message": "Access denied (403 Forbidden)",
                    "http_status": 403,
                    "elapsed_ms": elapsed_ms,
                }

            response.raise_for_status()
            payload = response.json()

            return {
                "executed": True,
                "status": "success",
                "http_status": response.status_code,
                "elapsed_ms": elapsed_ms,
                "bundle_type": payload.get("type"),
                "total": payload.get("total"),
                "resource_type": payload.get("resourceType"),
            }
        except httpx.HTTPStatusError as exc:
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            return {
                "executed": True,
                "status": "error",
                "error_type": "http_error",
                "message": str(exc),
                "http_status": exc.response.status_code,
                "elapsed_ms": elapsed_ms,
            }
        except httpx.RequestError as exc:
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            return {
                "executed": True,
                "status": "error",
                "error_type": "request_failed",
                "message": str(exc),
                "elapsed_ms": elapsed_ms,
            }