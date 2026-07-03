"""
FHIR search query parsing utilities.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import parse_qsl, urlparse

FHIR_MODIFIERS = frozenset({
    "exact",
    "contains",
    "text",
    "in",
    "not-in",
    "below",
    "above",
    "type",
    "identifier",
    "of-type",
    "missing",
})

FHIR_COMPARATORS = frozenset({"eq", "ne", "gt", "lt", "ge", "le", "sa", "eb", "ap"})

# Longer prefixes first to avoid partial matches (e.g. "ne" before "e").
_COMPARATOR_PREFIXES = ("ne", "eq", "ge", "le", "gt", "lt", "sa", "eb", "ap")

CHAIN_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9]*(?:\.[A-Za-z][A-Za-z0-9]*)+$")


@dataclass
class ParsedSearchParam:
    name: str
    value: str = ""
    modifier: Optional[str] = None
    comparator: Optional[str] = None
    chained: bool = False


@dataclass
class ParsedQuery:
    resource_type: str
    params: list[ParsedSearchParam] = field(default_factory=list)
    raw_query: str = ""


def _extract_comparator(value: str) -> tuple[Optional[str], str]:
    for prefix in _COMPARATOR_PREFIXES:
        if value.startswith(prefix) and len(value) > len(prefix):
            return prefix, value[len(prefix):]
    return None, value


def _split_param_name(raw_name: str) -> tuple[str, Optional[str], bool]:
    chained = bool(CHAIN_PATTERN.match(raw_name))
    if chained:
        return raw_name, None, True

    if ":" in raw_name:
        base, suffix = raw_name.rsplit(":", 1)
        if suffix in FHIR_MODIFIERS:
            return base, suffix, False
    return raw_name, None, False


def parse_query_url(query_url: str) -> ParsedQuery:
    """Parse a FHIR search query URL or relative query string."""
    raw = query_url.strip()
    if "://" in raw:
        parsed = urlparse(raw)
        path = parsed.path.strip("/")
        resource_type = path.split("/")[-1] if path else ""
        query_string = parsed.query
    elif "?" in raw:
        resource_type, query_string = raw.split("?", 1)
        resource_type = resource_type.strip("/").split("/")[-1]
    else:
        resource_type = raw.strip("/").split("/")[-1]
        query_string = ""

    params: list[ParsedSearchParam] = []
    for name, value in parse_qsl(query_string, keep_blank_values=True):
        param_name, modifier, chained = _split_param_name(name)
        comparator, stripped_value = _extract_comparator(value)
        params.append(
            ParsedSearchParam(
                name=param_name,
                value=stripped_value,
                modifier=modifier,
                comparator=comparator,
                chained=chained,
            )
        )

    return ParsedQuery(resource_type=resource_type, params=params, raw_query=raw)