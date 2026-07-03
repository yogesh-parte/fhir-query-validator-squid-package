"""
Operator authentication for human-gate review resolution.
"""

from __future__ import annotations

import os


class HumanGateAuthError(PermissionError):
    """Raised when human-gate operator credentials are missing or invalid."""


def human_gate_auth_required() -> bool:
    """When true, submit_review_decision requires a valid operator token."""
    return os.getenv("FHIR_HUMAN_GATE_REQUIRE_AUTH", "false").lower() == "true"


def verify_human_gate_operator(
    *,
    operator_token: str | None,
    reviewer: str,
) -> None:
    """
    Validate operator credentials for human review resolution.

    Demo and local workflows leave FHIR_HUMAN_GATE_REQUIRE_AUTH unset (false).
    Production deployments set FHIR_HUMAN_GATE_REQUIRE_AUTH=true and configure
    FHIR_HUMAN_GATE_OPERATOR_TOKEN.
    """
    if not human_gate_auth_required():
        return

    expected = os.getenv("FHIR_HUMAN_GATE_OPERATOR_TOKEN")
    if not expected:
        raise HumanGateAuthError(
            "Human gate auth is enabled but FHIR_HUMAN_GATE_OPERATOR_TOKEN is not configured."
        )
    if not operator_token or operator_token != expected:
        raise HumanGateAuthError("Invalid or missing operator credentials.")
    if not reviewer.strip():
        raise HumanGateAuthError("Reviewer identity is required.")