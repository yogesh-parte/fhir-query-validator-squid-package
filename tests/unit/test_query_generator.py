"""Unit tests for QueryGeneratorAgent and FHIR resource registry."""

import pytest

from src.agentic_layer.agents.query_generator_agent import QueryGeneratorAgent
from src.agentic_layer.utils.fhir_resource_registry import (
    get_resource_spec,
    list_resource_types,
)


def test_list_resource_types_includes_patient_and_observation():
    types = list_resource_types()
    assert "Patient" in types
    assert "Observation" in types


def test_patient_spec_links_to_build_fhir_search_page():
    spec = get_resource_spec("patient")
    assert spec.resource_type == "Patient"
    assert "patient-search.html" in spec.search_page
    assert "gender" in spec.param_names()


def test_generate_patient_gender_query():
    agent = QueryGeneratorAgent()
    result = agent.generate("Patient", {"gender": "male", "_count": 5})

    assert result["generated"] is True
    assert result["query_url"] == "Patient?gender=male&_count=5"
    assert "gender" in result["parameters_used"]


def test_generate_observation_status_and_date():
    agent = QueryGeneratorAgent()
    result = agent.generate(
        "Observation",
        {
            "status": "final",
            "date": {"comparator": "ge", "value": "2024-01-01"},
        },
        count=10,
    )

    assert result["generated"] is True
    assert "Observation?" in result["query_url"]
    assert "status=final" in result["query_url"]
    assert "date=ge2024-01-01" in result["query_url"]
    assert "_count=10" in result["query_url"]


def test_generate_rejects_unknown_parameter():
    agent = QueryGeneratorAgent()
    result = agent.generate("Patient", {"not_a_real_param": "true"})

    assert result["generated"] is False
    assert result["query_url"] == "Patient"
    assert any("not_a_real_param" in err for err in result["errors"])


def test_generate_from_intent_male_patients():
    agent = QueryGeneratorAgent()
    result = agent.generate_from_intent("Patient", "male patients")

    assert result["generated"] is True
    assert "gender=male" in result["query_url"]


def test_generate_warns_when_param_missing_from_capability():
    agent = QueryGeneratorAgent()
    result = agent.generate(
        "Patient",
        {"gender": "male"},
        interpreted_capability={
            "supported_resources": {
                "Patient": {"search_params": [{"name": "name", "type": "string"}]},
            }
        },
    )

    assert result["generated"] is True
    assert result["warnings"]


def test_unknown_resource_type_raises():
    agent = QueryGeneratorAgent()
    with pytest.raises(ValueError, match="Unknown resource_type"):
        agent.describe_resource("NotARealResource")