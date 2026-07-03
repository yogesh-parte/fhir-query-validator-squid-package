"""
validation_workflow.py
Google ADK graph workflow for FHIR query validation with loop engineering.
"""

from __future__ import annotations

from typing import Any, Mapping

from google.adk import Workflow

from ..state.workflow_state import ValidationWorkflowState
from .nodes import finalize_output, initialize_workflow, run_validation_pipeline
from .workflow_engine import execute_workflow


# ADK 2.0 graph workflow — runnable via `adk run` / `adk web` / agents-cli.
# Escalation (learner/human) runs inside execute_workflow(); the graph is a
# thin I/O wrapper so demos and tests share one orchestration implementation.
root_agent = Workflow(
    name="fhir_query_validator",
    description=(
        "Validates FHIR search queries against CapabilityStatement, executes valid "
        "queries, detects error patterns, and escalates to learner or human agents."
    ),
    state_schema=ValidationWorkflowState,
    edges=[
        ("START", initialize_workflow, run_validation_pipeline, finalize_output),
    ],
)


def run_validation_workflow(
    state: Mapping[str, Any] | ValidationWorkflowState,
) -> dict[str, Any]:
    """
    Synchronous workflow entry point for demos, scripts, and tests.
    Delegates to the shared workflow engine used by ADK graph nodes.
    """
    if isinstance(state, ValidationWorkflowState):
        initial = state.model_dump()
    else:
        initial = dict(state)
    result = execute_workflow(initial)
    return result.model_dump()