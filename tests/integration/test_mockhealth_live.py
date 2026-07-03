"""Live integration tests for mock.health (requires MOCK_HEALTH_API_KEY)."""

import pytest

from src.agentic_layer.agents.cache_agent import CacheAgent
from src.agentic_layer.graph.validation_workflow import run_validation_workflow

from .conftest import require_mockhealth_api_key

pytestmark = [pytest.mark.integration, pytest.mark.mockhealth]


def test_mockhealth_metadata_fetch_with_api_key():
    require_mockhealth_api_key()

    capability = CacheAgent().get_capability_statement("mockhealth")
    assert capability["resourceType"] == "CapabilityStatement"


def test_mockhealth_validate_and_execute_patient_query():
    require_mockhealth_api_key()

    result = run_validation_workflow(
        {
            "query_url": "Patient?_count=1",
            "server_key": "mockhealth",
            "mode": "validate_and_execute",
        }
    )

    output = result["final_output"]
    assert output["valid"] is True
    assert output["server_used"] == "mockhealth"
    assert output["executed"] is True
    assert output["results"]["status"] == "success"
