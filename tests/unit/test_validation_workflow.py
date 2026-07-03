"""Unit tests for the synchronous validation workflow entry point."""

from unittest.mock import patch

from src.agentic_layer.graph.validation_workflow import run_validation_workflow

PATIENT_CAPABILITY = {
    "resourceType": "CapabilityStatement",
    "rest": [{
        "resource": [{
            "type": "Patient",
            "searchParam": [{"name": "gender", "type": "token"}],
        }],
    }],
}


@patch("src.agentic_layer.graph.workflow_engine.cache_agent.get_capability_statement")
def test_run_validation_workflow_returns_dict_contract(mock_get_capability):
    mock_get_capability.return_value = PATIENT_CAPABILITY

    result = run_validation_workflow({
        "query_url": "Patient?gender=male",
        "server_key": "hapi",
        "mode": "validate_only",
    })

    assert isinstance(result, dict)
    assert result["final_output"]["valid"] is True
    assert result["server_key"] == "hapi"
    assert "validation_result" in result