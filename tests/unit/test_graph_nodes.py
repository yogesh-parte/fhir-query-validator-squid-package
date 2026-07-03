"""Unit tests for ADK graph workflow nodes."""

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from src.agentic_layer.graph.nodes import (
    finalize_output,
    initialize_workflow,
    run_validation_pipeline,
)
from src.agentic_layer.state.workflow_state import ValidationWorkflowState


class DictState:
    """Minimal ADK-like state bag for node unit tests."""

    def __init__(self, initial: dict | None = None) -> None:
        self._data = dict(initial or {})

    def to_dict(self) -> dict:
        return dict(self._data)

    def __setitem__(self, key: str, value) -> None:
        self._data[key] = value

    def __getitem__(self, key: str):
        return self._data[key]

    def get(self, key: str, default=None):
        return self._data.get(key, default)


async def _run_node(node, ctx, node_input=None):
    events = []
    async for event in node.run(ctx=ctx, node_input=node_input):
        events.append(event)
    return events


def _ctx(state: dict | None = None) -> MagicMock:
    ctx = MagicMock()
    ctx.state = DictState(state)
    return ctx


def test_initialize_workflow_requires_query_url():
    ctx = _ctx({"server_key": "hapi"})

    asyncio.run(_run_node(initialize_workflow, ctx))

    assert ctx.state["workflow_error"] == "query_url or query_generation is required"


def test_initialize_workflow_accepts_query_generation():
    ctx = _ctx({
        "query_generation": {"resource_type": "Patient", "intent": "male patients"},
        "server_key": "hapi",
    })

    asyncio.run(_run_node(initialize_workflow, ctx))

    assert not ctx.state.get("workflow_error")


def test_initialize_workflow_accepts_valid_request():
    ctx = _ctx({"query_url": "Patient?gender=male", "server_key": "hapi"})

    asyncio.run(_run_node(initialize_workflow, ctx))

    assert not ctx.state.get("workflow_error")


def test_run_validation_pipeline_skips_when_workflow_error_set():
    ctx = _ctx({
        "query_url": "Patient?gender=male",
        "workflow_error": "blocked",
    })

    with patch("src.agentic_layer.graph.nodes.execute_workflow") as mock_execute:
        asyncio.run(_run_node(run_validation_pipeline, ctx))
        mock_execute.assert_not_called()


@patch("src.agentic_layer.graph.nodes.execute_workflow")
def test_run_validation_pipeline_delegates_to_engine(mock_execute):
    mock_execute.return_value = ValidationWorkflowState(
        query_url="Patient?gender=male",
        server_key="hapi",
        validation_result={"valid": True, "errors": [], "warnings": []},
        execution_result={"executed": False},
        final_output={"valid": True, "executed": False},
    )
    ctx = _ctx({
        "query_url": "Patient?gender=male",
        "server_key": "hapi",
        "mode": "validate_only",
    })

    asyncio.run(_run_node(run_validation_pipeline, ctx))

    mock_execute.assert_called_once()
    assert ctx.state["final_output"]["valid"] is True


def test_finalize_output_builds_contract_when_missing():
    ctx = _ctx({
        "server_key": "hapi",
        "validation_result": {"valid": True, "errors": [], "warnings": []},
        "execution_result": {"executed": False},
    })

    asyncio.run(_run_node(finalize_output, ctx))

    assert ctx.state["final_output"]["valid"] is True
    assert ctx.state["final_output"]["server_used"] == "hapi"


def test_finalize_output_preserves_existing_payload():
    existing = {"valid": False, "errors": ["already set"], "executed": False}
    ctx = _ctx({"server_key": "hapi", "final_output": existing})

    asyncio.run(_run_node(finalize_output, ctx))

    assert ctx.state["final_output"] == existing