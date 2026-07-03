"""
SearchLearnerAgent
Provides helpful explanations and suggestions when repeated invalid queries are detected.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from ..utils.query_parser import parse_query_url


class SearchLearnerAgent:
    """
    Educates the user and suggests improvements based on CapabilityStatement data.
    """

    def provide_guidance(
        self,
        query_url: str,
        validation_result: Dict[str, Any],
        interpreted_capability: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        print("[SearchLearnerAgent] Providing guidance for repeated invalid queries...")

        parsed = parse_query_url(query_url)
        resource_type = parsed.resource_type
        supported_resources = (interpreted_capability or {}).get("supported_resources", {})
        resource_def = supported_resources.get(resource_type, {})
        param_names = [
            p["name"] for p in resource_def.get("search_params", []) if p.get("name")
        ]

        errors = validation_result.get("errors", [])
        error_types = validation_result.get("error_types", [])

        suggestions: list[str] = []
        if "unknown_resource" in error_types:
            available = sorted(supported_resources.keys())[:8]
            suggestions.append(
                "Pick a resource type declared in the server CapabilityStatement: "
                + ", ".join(available)
            )
        if "unknown_parameter" in error_types and param_names:
            suggestions.append(
                f"Supported search parameters for {resource_type}: "
                + ", ".join(param_names[:12])
            )
        if "unsupported_modifier" in error_types:
            suggestions.append(
                "Remove or change the parameter modifier (e.g. :exact, :contains) "
                "to one supported for that parameter type."
            )
        if "unsupported_comparator" in error_types:
            suggestions.append(
                "Use a valid comparator prefix (eq, gt, lt, ge, le) only on "
                "date/number/quantity parameters."
            )

        example_param = param_names[0] if param_names else "gender"
        example = f"{resource_type}?{example_param}=example"

        return {
            "message": (
                "Repeated invalid queries detected. "
                + (errors[0] if errors else "Review your query structure.")
            ),
            "suggestion": suggestions[0] if suggestions else (
                "Use supported search parameters from the server's CapabilityStatement."
            ),
            "suggestions": suggestions,
            "example": example,
            "query_url": query_url,
            "resource_type": resource_type,
            "supported_parameters": param_names[:20],
        }