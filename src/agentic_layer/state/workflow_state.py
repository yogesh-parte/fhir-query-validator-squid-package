"""
Pydantic state model for the ADK validation workflow graph.
"""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class ValidationWorkflowState(BaseModel):
    """Shared workflow state passed through ADK graph nodes."""

    query_url: str = ""
    query_generation: dict[str, Any] = Field(default_factory=dict)
    generated_query: dict[str, Any] = Field(default_factory=dict)
    server_key: str = "hapi"
    user_id: Optional[str] = None
    auth_token: Optional[str] = None
    mode: Literal["validate_only", "validate_and_execute"] = "validate_only"

    capability_statement: dict[str, Any] = Field(default_factory=dict)
    interpreted_capability: dict[str, Any] = Field(default_factory=dict)
    validation_result: dict[str, Any] = Field(default_factory=dict)
    execution_result: dict[str, Any] = Field(default_factory=dict)

    pattern_detected: bool = False
    escalation_decision: Optional[str] = None
    escalation_audit: dict[str, Any] = Field(default_factory=dict)
    learner_guidance: dict[str, Any] = Field(default_factory=dict)
    human_review: dict[str, Any] = Field(default_factory=dict)

    final_output: dict[str, Any] = Field(default_factory=dict)
    workflow_error: Optional[str] = None