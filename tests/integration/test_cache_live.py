"""Live integration tests for CacheAgent against public FHIR servers."""

import pytest

from src.agentic_layer.agents.cache_agent import CacheAgent

from .conftest import PUBLIC_SERVER_KEYS, require_reachable_server

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("server_key", PUBLIC_SERVER_KEYS)
def test_cache_agent_fetches_capability_statement(server_key: str):
    require_reachable_server(server_key)

    agent = CacheAgent()
    capability = agent.get_capability_statement(server_key)

    assert capability["resourceType"] == "CapabilityStatement"
    assert capability.get("rest") or capability.get("resourceType") == "CapabilityStatement"
