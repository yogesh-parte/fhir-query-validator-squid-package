"""Live integration tests for query validation against public FHIR servers."""

import pytest

from src.agentic_layer.graph.validation_workflow import run_validation_workflow

from .conftest import PUBLIC_SERVER_KEYS, require_reachable_server

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("server_key", PUBLIC_SERVER_KEYS)
def test_valid_patient_gender_query_passes(server_key: str):
    require_reachable_server(server_key)

    result = run_validation_workflow(
        {
            "query_url": "Patient?gender=male",
            "server_key": server_key,
            "mode": "validate_only",
        }
    )

    output = result["final_output"]
    assert output["valid"] is True
    assert output["server_used"] == server_key
    assert output["executed"] is False


@pytest.mark.parametrize("server_key", PUBLIC_SERVER_KEYS)
def test_invalid_parameter_query_fails(server_key: str):
    require_reachable_server(server_key)

    result = run_validation_workflow(
        {
            "query_url": "Patient?this_param_should_not_exist=1",
            "server_key": server_key,
            "mode": "validate_only",
        }
    )

    output = result["final_output"]
    assert output["valid"] is False
    assert output["errors"]
