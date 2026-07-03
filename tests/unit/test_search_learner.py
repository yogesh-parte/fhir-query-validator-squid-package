from src.agentic_layer.agents.search_learner_agent import SearchLearnerAgent


def test_search_learner_uses_capability_statement():
    agent = SearchLearnerAgent()
    guidance = agent.provide_guidance(
        query_url="Patient?invalid_param=true",
        validation_result={
            "errors": ["Search parameter 'invalid_param' is not supported for Patient."],
            "error_types": ["unknown_parameter"],
        },
        interpreted_capability={
            "supported_resources": {
                "Patient": {
                    "search_params": [
                        {"name": "gender", "type": "token"},
                        {"name": "birthdate", "type": "date"},
                    ]
                }
            }
        },
    )
    assert "gender" in guidance["supported_parameters"]
    assert "Patient?gender=example" == guidance["example"]


def test_search_learner_unknown_resource_suggestion():
    agent = SearchLearnerAgent()
    guidance = agent.provide_guidance(
        query_url="Observation?code=1234",
        validation_result={
            "errors": ["Resource 'Observation' is not supported by this server."],
            "error_types": ["unknown_resource"],
        },
        interpreted_capability={
            "supported_resources": {
                "Patient": {"search_params": [{"name": "gender", "type": "token"}]},
            }
        },
    )
    assert "Patient" in guidance["suggestion"]
    assert any("CapabilityStatement" in item for item in guidance["suggestions"])


def test_search_learner_modifier_and_comparator_suggestions():
    agent = SearchLearnerAgent()
    guidance = agent.provide_guidance(
        query_url="Patient?gender:text=x&birthdate=gt2020",
        validation_result={
            "errors": ["bad modifier", "bad comparator"],
            "error_types": ["unsupported_modifier", "unsupported_comparator"],
        },
        interpreted_capability={
            "supported_resources": {
                "Patient": {
                    "search_params": [
                        {"name": "gender", "type": "token"},
                        {"name": "birthdate", "type": "date"},
                    ]
                }
            }
        },
    )
    assert any("modifier" in s.lower() for s in guidance["suggestions"])
    assert any("comparator" in s.lower() for s in guidance["suggestions"])


def test_search_learner_fallback_without_capability_or_errors():
    agent = SearchLearnerAgent()
    guidance = agent.provide_guidance(
        query_url="Patient?bad=true",
        validation_result={"errors": [], "error_types": []},
        interpreted_capability=None,
    )
    assert guidance["example"] == "Patient?gender=example"
    assert "CapabilityStatement" in guidance["suggestion"]