from src.agentic_layer.agents.capability_interpreter import CapabilityInterpreterAgent


def test_interpreter_extracts_modifiers_and_comparators():
    capability = {
        "resourceType": "CapabilityStatement",
        "rest": [{
            "resource": [{
                "type": "Patient",
                "searchParam": [
                    {"name": "gender", "type": "token"},
                    {"name": "birthdate", "type": "date"},
                ],
            }],
        }],
    }
    agent = CapabilityInterpreterAgent()
    result = agent.interpret(capability)
    patient = result["supported_resources"]["Patient"]
    gender = next(p for p in patient["search_params"] if p["name"] == "gender")
    birthdate = next(p for p in patient["search_params"] if p["name"] == "birthdate")
    assert "exact" in gender["modifiers"]
    assert "gt" in birthdate["comparators"]


def test_interpreter_skips_resources_without_type():
    capability = {
        "resourceType": "CapabilityStatement",
        "rest": [{"resource": [{"searchParam": [{"name": "x", "type": "string"}]}]}],
    }
    agent = CapabilityInterpreterAgent()
    result = agent.interpret(capability)
    assert result["supported_resources"] == {}


def test_interpreter_extracts_interactions_and_software():
    capability = {
        "resourceType": "CapabilityStatement",
        "fhirVersion": "4.0.1",
        "software": {"name": "TestServer"},
        "rest": [{
            "resource": [{
                "type": "Patient",
                "interaction": [{"code": "search-type"}, {"code": "read"}],
                "searchParam": [{"name": "name", "type": "string"}],
            }],
        }],
    }
    agent = CapabilityInterpreterAgent()
    result = agent.interpret(capability)
    patient = result["supported_resources"]["Patient"]
    assert patient["interactions"] == ["search-type", "read"]
    assert result["software"]["name"] == "TestServer"
    assert result["fhir_version"] == "4.0.1"


def test_interpreter_returns_empty_on_malformed_payload():
    agent = CapabilityInterpreterAgent()
    result = agent.interpret({"rest": None})
    assert result["supported_resources"] == {}