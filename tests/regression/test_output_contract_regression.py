"""
Regression tests for final_output JSON contract stability.
"""

from unittest.mock import patch

from src.agentic_layer.graph.validation_workflow import run_validation_workflow
from tests.integration.conftest import PATIENT_CAPABILITY
from tests.regression.conftest import FINAL_OUTPUT_REQUIRED_KEYS


@patch("src.agentic_layer.graph.workflow_engine.cache_agent.get_capability_statement")
def test_final_output_contract_fields_remain_stable(mock_get_capability):
    mock_get_capability.return_value = PATIENT_CAPABILITY

    result = run_validation_workflow(
        {
            "query_url": "Patient?gender=male",
            "server_key": "hapi",
            "mode": "validate_only",
        }
    )

    output = result["final_output"]
    assert FINAL_OUTPUT_REQUIRED_KEYS.issubset(output.keys())
    assert output["valid"] is True
    assert output["server_used"] == "hapi"
    assert output["executed"] is False
    assert output["results"] is None
    assert output["escalation"] == "none"
    assert output["human_review_required"] is False
