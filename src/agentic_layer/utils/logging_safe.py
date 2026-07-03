"""
Production-safe logging helpers that redact sensitive query details.
"""

from __future__ import annotations

import os

from .query_parser import parse_query_url


def verbose_logging_enabled() -> bool:
    """When false, agent stdout omits full query URLs and search parameters."""
    return os.getenv("FHIR_VERBOSE_LOGGING", "true").lower() == "true"


def format_query_log_label(query_url: str) -> str:
    """Return a log-safe label for a FHIR search query."""
    if verbose_logging_enabled():
        return query_url
    try:
        parsed = parse_query_url(query_url)
        param_names = sorted({param.name for param in parsed.params})
        if param_names:
            return f"{parsed.resource_type}?[{','.join(param_names)}]"
        return parsed.resource_type or "(unknown-resource)"
    except Exception:
        return "(redacted-query)"