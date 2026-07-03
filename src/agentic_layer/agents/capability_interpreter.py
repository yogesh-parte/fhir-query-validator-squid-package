"""
CapabilityInterpreterAgent
Dynamically interprets CapabilityStatement to support generalized validation.
"""

from typing import Dict, Any, List

# Modifiers commonly supported per FHIR search parameter type.
_MODIFIERS_BY_TYPE: dict[str, list[str]] = {
    "string": ["exact", "contains", "text", "in", "not-in", "missing"],
    "token": ["exact", "in", "not-in", "text", "of-type", "missing"],
    "reference": ["exact", "identifier", "missing"],
    "uri": ["exact", "contains", "missing"],
    "date": ["missing"],
    "dateTime": ["missing"],
    "instant": ["missing"],
    "number": ["missing"],
    "quantity": ["missing"],
    "composite": ["missing"],
    "special": ["missing"],
}

_COMPARATORS_BY_TYPE: dict[str, list[str]] = {
    "date": ["eq", "ne", "gt", "lt", "ge", "le", "sa", "eb", "ap"],
    "dateTime": ["eq", "ne", "gt", "lt", "ge", "le", "sa", "eb", "ap"],
    "instant": ["eq", "ne", "gt", "lt", "ge", "le", "sa", "eb", "ap"],
    "number": ["eq", "ne", "gt", "lt", "ge", "le", "sa", "eb", "ap"],
    "quantity": ["eq", "ne", "gt", "lt", "ge", "le", "sa", "eb", "ap"],
}


class CapabilityInterpreterAgent:
    """
    Specialist agent that extracts usable information from CapabilityStatement.
    """

    def interpret(self, capability_statement: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract supported resources, search parameters, modifiers, and comparators.
        """
        print("[CapabilityInterpreter] Interpreting CapabilityStatement...")

        supported: dict[str, dict] = {}

        try:
            for rest_entry in capability_statement.get("rest", []):
                for resource in rest_entry.get("resource", []):
                    resource_type = resource.get("type")
                    if not resource_type:
                        continue

                    search_params: List[dict] = []
                    for param in resource.get("searchParam", []):
                        param_type = param.get("type", "string")
                        search_params.append({
                            "name": param.get("name"),
                            "type": param_type,
                            "documentation": param.get("documentation"),
                            "modifiers": _MODIFIERS_BY_TYPE.get(param_type, ["missing"]),
                            "comparators": _COMPARATORS_BY_TYPE.get(param_type, []),
                        })

                    supported[resource_type] = {
                        "search_params": search_params,
                        "interactions": [
                            interaction.get("code")
                            for interaction in resource.get("interaction", [])
                            if interaction.get("code")
                        ],
                    }
        except Exception as exc:
            print(f"[CapabilityInterpreter] Error interpreting CapabilityStatement: {exc}")
            return {"supported_resources": {}, "software": {}}

        return {
            "supported_resources": supported,
            "software": capability_statement.get("software", {}),
            "fhir_version": capability_statement.get("fhirVersion"),
        }