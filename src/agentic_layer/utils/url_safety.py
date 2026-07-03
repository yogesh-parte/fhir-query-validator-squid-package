"""
Safe URL construction for outbound FHIR requests.
"""

from __future__ import annotations

from urllib.parse import urljoin, urlparse


class UnsafeQueryUrlError(ValueError):
    """Raised when query_url cannot be safely joined to a server base URL."""


def build_fhir_target_url(base_url: str, query_url: str) -> str:
    """
    Join a relative FHIR search path to a registered server base URL.

    Rejects absolute URLs, unexpected schemes, and netloc mismatches to reduce
    SSRF and credential-relay risk.
    """
    raw = query_url.strip()
    if not raw:
        raise UnsafeQueryUrlError("query_url must not be empty")
    if "://" in raw:
        raise UnsafeQueryUrlError("Absolute query_url is not allowed")

    base_parsed = urlparse(base_url.rstrip("/"))
    if base_parsed.scheme not in {"http", "https"} or not base_parsed.netloc:
        raise UnsafeQueryUrlError("Invalid server base_url")

    joined = urljoin(base_url.rstrip("/") + "/", raw.lstrip("/"))
    parsed = urlparse(joined)
    if parsed.scheme not in {"http", "https"}:
        raise UnsafeQueryUrlError("Invalid URL scheme")
    if parsed.netloc != base_parsed.netloc:
        raise UnsafeQueryUrlError("query_url resolved outside server base_url")

    return joined