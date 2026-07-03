"""
QueryValidatorAgent
Validates FHIR search queries against interpreted CapabilityStatement.
Includes pattern detection for repeated invalid queries.
"""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

from ..utils.logging_safe import format_query_log_label
from ..utils.query_parser import parse_query_url

# Reconciled thresholds across specs (README priority fix #4).
LEARNER_THRESHOLD = {"count": 3, "window_seconds": 600}   # 3+ in 10 minutes
HUMAN_THRESHOLD = {"count": 5, "window_seconds": 900}     # 5+ in 15 minutes

SENSITIVE_CHAIN_MARKERS = ("patient.", "subject.", "individual.")


class QueryValidatorAgent:
    """
    Validates queries and tracks repeated invalid patterns per user and server.
    """

    def __init__(self) -> None:
        self._pattern_history: dict[str, list[tuple[float, str]]] = defaultdict(list)

    def _history_key(self, user_id: str, server_key: Optional[str]) -> str:
        return f"{user_id}:{server_key or 'default'}"

    def validate(
        self,
        query_url: str,
        interpreted_capability: Dict[str, Any],
        user_id: Optional[str] = None,
        server_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Validate the query and detect patterns when user_id is provided."""
        print(f"[QueryValidator] Validating query: {format_query_log_label(query_url)}")

        errors: list[str] = []
        warnings: list[str] = []
        error_types: list[str] = []
        high_severity = False

        parsed = parse_query_url(query_url)
        supported_resources = interpreted_capability.get("supported_resources", {})

        if not parsed.resource_type:
            errors.append("Query is missing a resource type (e.g. Patient?gender=male).")
            error_types.append("missing_resource")
        elif parsed.resource_type not in supported_resources:
            available = ", ".join(sorted(supported_resources.keys())[:10])
            errors.append(
                f"Resource '{parsed.resource_type}' is not supported by this server."
                + (f" Available examples: {available}" if available else "")
            )
            error_types.append("unknown_resource")
        else:
            resource_def = supported_resources[parsed.resource_type]
            known_params = {
                p["name"]: p for p in resource_def.get("search_params", []) if p.get("name")
            }

            if not parsed.params:
                warnings.append(
                    f"Query for '{parsed.resource_type}' has no search parameters."
                )

            for param in parsed.params:
                if param.name.startswith("_"):
                    if param.name not in {"_count", "_sort", "_include", "_revinclude", "_summary"}:
                        warnings.append(
                            f"Standard parameter '{param.name}' may not be declared in "
                            "CapabilityStatement but is generally allowed."
                        )
                    continue

                if param.chained:
                    if any(marker in param.name.lower() for marker in SENSITIVE_CHAIN_MARKERS):
                        high_severity = True
                        warnings.append(
                            f"Chained parameter '{param.name}' may access sensitive "
                            "related resources; review carefully."
                        )
                    if "." in param.name:
                        root_param = param.name.split(".", 1)[0]
                        if root_param not in known_params:
                            errors.append(
                                f"Chained parameter '{param.name}' references unknown "
                                f"root parameter '{root_param}'."
                            )
                            error_types.append("unknown_parameter")
                    continue

                if param.name not in known_params:
                    suggestions = self._suggest_params(param.name, known_params.keys())
                    message = (
                        f"Search parameter '{param.name}' is not supported for "
                        f"{parsed.resource_type}."
                    )
                    if suggestions:
                        message += f" Did you mean: {', '.join(suggestions)}?"
                    errors.append(message)
                    error_types.append("unknown_parameter")
                    continue

                param_def = known_params[param.name]
                if param.modifier and param.modifier not in param_def.get("modifiers", []):
                    errors.append(
                        f"Modifier ':{param.modifier}' is not supported for parameter "
                        f"'{param.name}' (type: {param_def.get('type')})."
                    )
                    error_types.append("unsupported_modifier")

                if param.comparator:
                    allowed = param_def.get("comparators", [])
                    if param.comparator not in allowed:
                        errors.append(
                            f"Comparator '{param.comparator}' is not supported for parameter "
                            f"'{param.name}' (type: {param_def.get('type')})."
                        )
                        error_types.append("unsupported_comparator")

        is_valid = len(errors) == 0
        result: dict[str, Any] = {
            "valid": is_valid,
            "errors": errors,
            "warnings": warnings,
            "error_types": error_types,
            "high_severity": high_severity,
            "query_url": query_url,
            "resource_type": parsed.resource_type,
            "pattern_detected": False,
            "pattern_stats": {},
        }

        if user_id and not is_valid:
            primary_error = error_types[0] if error_types else "validation_failed"
            self._record_invalid_query(user_id, server_key, primary_error)
            stats = self._pattern_stats(user_id, server_key)
            result["pattern_stats"] = stats
            result["pattern_detected"] = stats["learner_threshold_met"]

        return result

    def get_pattern_stats(
        self,
        user_id: str,
        server_key: Optional[str] = None,
    ) -> dict[str, Any]:
        return self._pattern_stats(user_id, server_key)

    def _suggest_params(self, name: str, candidates: Any) -> list[str]:
        name_lower = name.lower()
        return [
            candidate
            for candidate in candidates
            if candidate.lower().startswith(name_lower[:3]) or name_lower in candidate.lower()
        ][:3]

    def _record_invalid_query(
        self,
        user_id: str,
        server_key: Optional[str],
        error_type: str,
    ) -> None:
        key = self._history_key(user_id, server_key)
        now = time.time()
        self._pattern_history[key].append((now, error_type))
        self._pattern_history[key] = self._pattern_history[key][-20:]

    def _count_in_window(
        self,
        history: list[tuple[float, str]],
        window_seconds: int,
    ) -> int:
        cutoff = time.time() - window_seconds
        return sum(1 for ts, _ in history if ts >= cutoff)

    def _pattern_stats(self, user_id: str, server_key: Optional[str]) -> dict[str, Any]:
        history = self._pattern_history.get(self._history_key(user_id, server_key), [])
        learner_count = self._count_in_window(history, LEARNER_THRESHOLD["window_seconds"])
        human_count = self._count_in_window(history, HUMAN_THRESHOLD["window_seconds"])
        return {
            "invalid_count_10m": learner_count,
            "invalid_count_15m": human_count,
            "learner_threshold_met": learner_count >= LEARNER_THRESHOLD["count"],
            "human_threshold_met": human_count >= HUMAN_THRESHOLD["count"],
            "recent_error_types": [etype for _, etype in history[-5:]],
        }