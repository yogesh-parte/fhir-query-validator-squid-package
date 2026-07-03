"""
FHIR R4 resource and standard search parameter registry.

Sourced from HL7 FHIR build.fhir.org resource list and per-resource search pages.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional
from urllib.parse import quote

_DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "fhir_standard_search_params.json"


@dataclass(frozen=True)
class SearchParamSpec:
    name: str
    type: str
    documentation: str = ""
    comparators: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "name": self.name,
            "type": self.type,
            "documentation": self.documentation,
        }
        if self.comparators:
            payload["comparators"] = list(self.comparators)
        return payload


@dataclass(frozen=True)
class ResourceSpec:
    resource_type: str
    resource_page: str
    search_page: str
    search_params: tuple[SearchParamSpec, ...]

    def param_names(self) -> list[str]:
        return [p.name for p in self.search_params]

    def get_param(self, name: str) -> Optional[SearchParamSpec]:
        for param in self.search_params:
            if param.name == name:
                return param
        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "resource_type": self.resource_type,
            "resource_page": self.resource_page,
            "search_page": self.search_page,
            "search_params": [p.to_dict() for p in self.search_params],
        }


@lru_cache(maxsize=1)
def load_registry() -> dict[str, Any]:
    with _DATA_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def registry_metadata() -> dict[str, str]:
    data = load_registry()
    return {
        "source_resource_list": data.get("source_resource_list", ""),
        "fhir_version": data.get("fhir_version", "R4"),
        "note": data.get("note", ""),
    }


def list_resource_types() -> list[str]:
    return sorted(load_registry().get("resources", {}).keys())


def get_resource_spec(resource_type: str) -> ResourceSpec:
    key = resource_type.strip()
    if not key:
        raise ValueError("resource_type must not be empty")

    resources = load_registry().get("resources", {})
    # FHIR resource types are PascalCase; accept case-insensitive lookup.
    match = None
    for name, payload in resources.items():
        if name.lower() == key.lower():
            match = (name, payload)
            break

    if match is None:
        known = ", ".join(sorted(resources.keys()))
        raise ValueError(
            f"Unknown resource_type '{resource_type}'. Known types: {known}"
        )

    canonical_name, payload = match
    params = tuple(
        SearchParamSpec(
            name=p["name"],
            type=p.get("type", "string"),
            documentation=p.get("documentation", ""),
            comparators=tuple(p.get("comparators", ())),
        )
        for p in payload.get("search_params", [])
        if p.get("name")
    )
    return ResourceSpec(
        resource_type=canonical_name,
        resource_page=payload.get("resource_page", ""),
        search_page=payload.get("search_page", ""),
        search_params=params,
    )


def encode_search_value(
    param: SearchParamSpec,
    raw_value: Any,
) -> str:
    """Format a criterion value for a FHIR search parameter."""
    if isinstance(raw_value, dict):
        comparator = raw_value.get("comparator")
        value = raw_value.get("value", "")
        if comparator:
            if param.comparators and comparator not in param.comparators:
                raise ValueError(
                    f"Comparator '{comparator}' is not allowed for parameter "
                    f"'{param.name}' (type={param.type})."
                )
            return f"{comparator}{value}"
        return str(value)

    value = str(raw_value)
    if param.comparators:
        for comp in ("ne", "eq", "ge", "le", "gt", "lt", "sa", "eb", "ap"):
            if value.startswith(comp):
                return value
    return quote(value, safe=":|,-._*")