"""
Regression tests for query validation behavior.

Golden cases lock core validation rules so refactors cannot silently change
accepted/rejected query semantics.
"""

from src.agentic_layer.agents.query_validator import QueryValidatorAgent
from tests.regression.conftest import PATIENT_CAPABILITY


def test_basic_patient_gender_query_still_works():
    """Ensure basic valid queries continue to pass."""
    validator = QueryValidatorAgent()
    result = validator.validate(
        query_url="Patient?gender=male",
        interpreted_capability=PATIENT_CAPABILITY,
    )
    assert result["valid"] is True


def test_unknown_parameter_still_rejected():
    validator = QueryValidatorAgent()
    result = validator.validate(
        query_url="Patient?invalid_param=true",
        interpreted_capability=PATIENT_CAPABILITY,
        user_id="regression-user",
        server_key="hapi",
    )
    assert result["valid"] is False
    assert "unknown_parameter" in result["error_types"]


def test_unknown_resource_still_rejected_with_examples():
    validator = QueryValidatorAgent()
    result = validator.validate(
        query_url="Observation?code=1234",
        interpreted_capability=PATIENT_CAPABILITY,
    )
    assert result["valid"] is False
    assert "unknown_resource" in result["error_types"]
    assert "Patient" in result["errors"][0]


def test_sensitive_chained_parameter_still_high_severity():
    validator = QueryValidatorAgent()
    result = validator.validate(
        query_url="Patient?subject.name=Smith",
        interpreted_capability=PATIENT_CAPABILITY,
        user_id="regression-chain-user",
        server_key="hapi",
    )
    assert result["high_severity"] is True
    assert any("sensitive" in warning.lower() for warning in result["warnings"])


def test_high_severity_still_triggers_pattern_on_first_failure():
    validator = QueryValidatorAgent()
    result = validator.validate(
        query_url="Patient?patient.unknown=value",
        interpreted_capability=PATIENT_CAPABILITY,
        user_id="regression-high-severity",
        server_key="hapi",
    )
    assert result["valid"] is False
    assert result["high_severity"] is True
    assert result["pattern_detected"] is True


def test_count_parameter_still_allowed_without_warning():
    validator = QueryValidatorAgent()
    result = validator.validate(
        query_url="Patient?_count=10",
        interpreted_capability=PATIENT_CAPABILITY,
    )
    assert result["valid"] is True
    assert not any("_count" in warning for warning in result["warnings"])


def test_typo_parameter_still_suggests_correction():
    validator = QueryValidatorAgent()
    result = validator.validate(
        query_url="Patient?gende=male",
        interpreted_capability=PATIENT_CAPABILITY,
    )
    assert result["valid"] is False
    assert "Did you mean" in result["errors"][0]
