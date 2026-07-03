"""Live integration tests for query execution against public FHIR servers."""

import pytest

from src.agentic_layer.graph.validation_workflow import run_validation_workflow

from .conftest import PUBLIC_SERVER_KEYS, require_reachable_server

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("server_key", PUBLIC_SERVER_KEYS)
def test_validate_and_execute_returns_bundle(server_key: str):
    require_reachable_server(server_key)

    result = run_validation_workflow(
        {
            "query_url": "Patient?_count=1",
            "server_key": server_key,
            "mode": "validate_and_execute",
        }
    )

    output = result["final_output"]
    assert output["valid"] is True
    assert output["executed"] is True
    assert output["results"] is not None
    assert output["results"]["status"] == "success"
    assert output["results"]["resource_type"] == "Bundle"
    total = output["results"].get("total")
    assert total is None or total >= 0
