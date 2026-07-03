"""Shared pytest fixtures."""

import sys
from pathlib import Path

import pytest

_SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))


@pytest.fixture(autouse=True)
def reset_workflow_singletons():
    """Isolate module-level workflow singletons between tests."""
    from src.agentic_layer.graph.workflow_engine import reset_singletons

    reset_singletons()
    yield
    reset_singletons()