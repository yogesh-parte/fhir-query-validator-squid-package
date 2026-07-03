"""Live integration tests for learner escalation using real CapabilityStatement data."""

import uuid

import pytest

from src.agentic_layer.graph.validation_workflow import run_validation_workflow

from .conftest import require_reachable_server

pytestmark = pytest.mark.integration


def test_learner_escalation_after_three_invalid_queries_on_hapi():
    require_reachable_server("hapi")
    user = f"live-learner-{uuid.uuid4()}"

    last = None
    for _ in range(3):
        last = run_validation_workflow(
            {
                "query_url": "Patient?invalid_param_live_test=1",
                "server_key": "hapi",
                "user_id": user,
                "mode": "validate_only",
            }
        )

    assert last is not None
    output = last["final_output"]
    assert output["valid"] is False
    assert output["escalation"] == "learner"
    assert output["pattern_detected"] is True
    assert last.get("learner_guidance")
