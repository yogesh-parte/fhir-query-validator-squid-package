"""
QueryGeneratorAgent
Builds FHIR REST search query URLs from standard resource search parameters.
"""

from __future__ import annotations

from typing import Any, Optional

from ..utils.fhir_resource_registry import (
    SearchParamSpec,
    encode_search_value,
    get_resource_spec,
    list_resource_types,
    registry_metadata,
)
_SPECIAL_PARAMS = frozenset({"_count", "_sort", "_include", "_revinclude", "_summary", "_elements"})


class QueryGeneratorAgent:
    """
    Generates FHIR search queries using standard parameters from build.fhir.org.

    Reference data: src/agentic_layer/data/fhir_standard_search_params.json
    """

    def list_resources(self) -> dict[str, Any]:
        """Return known resource types and registry metadata."""
        return {
            **registry_metadata(),
            "resource_types": list_resource_types(),
        }

    def describe_resource(self, resource_type: str) -> dict[str, Any]:
        """Return standard search parameters for a FHIR resource type."""
        spec = get_resource_spec(resource_type)
        return spec.to_dict()

    def generate(
        self,
        resource_type: str,
        criteria: Optional[dict[str, Any]] = None,
        *,
        count: Optional[int] = None,
        sort: Optional[str] = None,
        interpreted_capability: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Generate a relative FHIR search query URL.

        Args:
            resource_type: FHIR resource (e.g. Patient, Observation).
            criteria: Mapping of search parameter name → value. Values may be
                strings or {"comparator": "ge", "value": "1990-01-01"} for dates.
            count: Optional _count paging parameter.
            sort: Optional _sort parameter.
            interpreted_capability: When provided, flag criteria not declared on
                the target server's CapabilityStatement.
        """
        print(f"[QueryGenerator] Generating query for resource: {resource_type}")

        spec = get_resource_spec(resource_type)
        criteria = criteria or {}
        errors: list[str] = []
        warnings: list[str] = []
        encoded_pairs: list[tuple[str, str]] = []

        server_params = self._server_param_index(interpreted_capability, spec.resource_type)

        for raw_name, raw_value in criteria.items():
            if raw_name in _SPECIAL_PARAMS:
                encoded_pairs.append((raw_name, str(raw_value)))
                continue

            param = spec.get_param(raw_name)
            if param is None:
                errors.append(
                    f"Search parameter '{raw_name}' is not a standard parameter for "
                    f"{spec.resource_type}. See {spec.search_page}"
                )
                continue

            try:
                encoded = encode_search_value(param, raw_value)
            except ValueError as exc:
                errors.append(str(exc))
                continue

            encoded_pairs.append((param.name, encoded))

            if server_params is not None and param.name not in server_params:
                warnings.append(
                    f"Parameter '{param.name}' is standard for {spec.resource_type} but "
                    "not declared on the target server CapabilityStatement."
                )

        if count is not None:
            encoded_pairs.append(("_count", str(count)))
        if sort:
            encoded_pairs.append(("_sort", sort))

        query_string = "&".join(f"{name}={value}" for name, value in encoded_pairs)
        query_url = f"{spec.resource_type}?{query_string}" if query_string else spec.resource_type

        return {
            "generated": not errors,
            "query_url": query_url,
            "resource_type": spec.resource_type,
            "resource_page": spec.resource_page,
            "search_page": spec.search_page,
            "criteria_applied": dict(criteria),
            "parameters_used": [name for name, _ in encoded_pairs],
            "standard_parameters": spec.param_names(),
            "errors": errors,
            "warnings": warnings,
        }

    def generate_from_intent(
        self,
        resource_type: str,
        intent: str,
        *,
        interpreted_capability: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Generate a query from a short intent phrase using built-in templates.

        Examples:
            intent="male patients" → Patient?gender=male
            intent="final observations" → Observation?status=final
        """
        templates = _INTENT_TEMPLATES.get(intent.strip().lower())
        if templates is None:
            available = ", ".join(sorted(_INTENT_TEMPLATES.keys()))
            return {
                "generated": False,
                "query_url": "",
                "resource_type": resource_type,
                "errors": [
                    f"Unknown intent '{intent}'. Available intents: {available}"
                ],
                "warnings": [],
            }

        criteria = templates.get(resource_type) or templates.get("*")
        if criteria is None:
            return {
                "generated": False,
                "query_url": "",
                "resource_type": resource_type,
                "errors": [
                    f"Intent '{intent}' does not apply to resource type '{resource_type}'."
                ],
                "warnings": [],
            }

        return self.generate(
            resource_type,
            criteria,
            interpreted_capability=interpreted_capability,
        )

    def _server_param_index(
        self,
        interpreted_capability: Optional[dict[str, Any]],
        resource_type: str,
    ) -> Optional[set[str]]:
        if not interpreted_capability:
            return None
        resource_def = interpreted_capability.get("supported_resources", {}).get(
            resource_type, {}
        )
        names = {
            p.get("name")
            for p in resource_def.get("search_params", [])
            if p.get("name")
        }
        return names


# intent_key → {resource_type or "*": criteria}
_INTENT_TEMPLATES: dict[str, dict[str, dict[str, Any]]] = {
    "male patients": {
        "Patient": {"gender": "male", "_count": 10},
    },
    "female patients": {
        "Patient": {"gender": "female", "_count": 10},
    },
    "active patients": {
        "Patient": {"active": "true", "_count": 10},
    },
    "final observations": {
        "Observation": {"status": "final", "_count": 10},
    },
    "active conditions": {
        "Condition": {"clinical-status": "active", "_count": 10},
    },
    "finished encounters": {
        "Encounter": {"status": "finished", "_count": 10},
    },
    "active organizations": {
        "Organization": {"active": "true", "_count": 10},
    },
}