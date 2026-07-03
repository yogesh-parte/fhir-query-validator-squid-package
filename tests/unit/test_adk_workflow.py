from src.agentic_layer.graph.validation_workflow import root_agent


def test_root_agent_is_adk_workflow():
    assert root_agent.name == "fhir_query_validator"
    assert root_agent.state_schema is not None
    assert root_agent.graph is not None
    node_names = {node.name for node in root_agent.graph.nodes}
    assert "initialize_workflow" in node_names
    assert "run_validation_pipeline" in node_names
    assert "finalize_output" in node_names
    assert "route_escalation" not in node_names