"""
ADK graph workflow nodes for the FHIR query validation factory.
"""

from __future__ import annotations

from google.adk.agents.context import Context
from google.adk.workflow import node

from ..state.workflow_state import ValidationWorkflowState
from .workflow_engine import build_final_output, execute_workflow


def _load_state(ctx: Context) -> ValidationWorkflowState:
    return ValidationWorkflowState.model_validate(ctx.state.to_dict())


def _save_state(ctx: Context, state: ValidationWorkflowState) -> None:
    for key, value in state.model_dump().items():
        ctx.state[key] = value


@node
def initialize_workflow(ctx: Context) -> None:
    """Seed workflow state from incoming request fields."""
    state = _load_state(ctx)
    if not state.query_url and not state.query_generation:
        state.workflow_error = "query_url or query_generation is required"
    _save_state(ctx, state)


@node
def run_validation_pipeline(ctx: Context) -> None:
    """Execute cache → interpret → validate → execute → escalate pipeline."""
    state = _load_state(ctx)
    if state.workflow_error:
        return
    updated = execute_workflow(state.model_dump())
    _save_state(ctx, updated)


@node
def finalize_output(ctx: Context) -> None:
    """Ensure spec-compliant final_output is present on state."""
    state = _load_state(ctx)
    if not state.final_output:
        state.final_output = build_final_output(state)
    _save_state(ctx, state)