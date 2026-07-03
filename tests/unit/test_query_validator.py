import pytest

from src.agentic_layer.agents.query_validator import QueryValidatorAgent


PATIENT_CAPABILITY = {
    "supported_resources": {
        "Patient": {
            "search_params": [
                {"name": "gender", "type": "token", "modifiers": ["exact", "missing"], "comparators": []},
                {"name": "birthdate", "type": "date", "modifiers": ["missing"], "comparators": ["gt", "lt"]},
                {"name": "subject", "type": "reference", "modifiers": ["missing"], "comparators": []},
            ]
        }
    }
}


def test_valid_query():
    validator = QueryValidatorAgent()
    result = validator.validate(
        query_url="Patient?gender=male",
        interpreted_capability=PATIENT_CAPABILITY,
        user_id="test-user",
        server_key="hapi",
    )
    assert result["valid"] is True


def test_invalid_parameter():
    validator = QueryValidatorAgent()
    result = validator.validate(
        query_url="Patient?invalid=true",
        interpreted_capability=PATIENT_CAPABILITY,
        user_id="test-user",
        server_key="hapi",
    )
    assert result["valid"] is False
    assert "unknown_parameter" in result["error_types"]


def test_unsupported_modifier():
    validator = QueryValidatorAgent()
    result = validator.validate(
        query_url="Patient?gender:text=smith",
        interpreted_capability=PATIENT_CAPABILITY,
        user_id="test-user",
        server_key="hapi",
    )
    assert result["valid"] is False
    assert "unsupported_modifier" in result["error_types"]


def test_pattern_detection_per_user_and_server():
    validator = QueryValidatorAgent()
    user = "test-user-pattern"

    for _ in range(3):
        result = validator.validate(
            query_url="Patient?invalid=true",
            interpreted_capability=PATIENT_CAPABILITY,
            user_id=user,
            server_key="hapi",
        )

    assert result.get("pattern_detected") is True
    assert result["pattern_stats"]["invalid_count_10m"] >= 3


def test_missing_resource_type():
    validator = QueryValidatorAgent()
    result = validator.validate(
        query_url="?gender=male",
        interpreted_capability=PATIENT_CAPABILITY,
    )
    assert result["valid"] is False
    assert "missing_resource" in result["error_types"]


def test_unknown_resource_type_lists_available_examples():
    validator = QueryValidatorAgent()
    result = validator.validate(
        query_url="Observation?code=1234",
        interpreted_capability=PATIENT_CAPABILITY,
    )
    assert result["valid"] is False
    assert "unknown_resource" in result["error_types"]
    assert "Patient" in result["errors"][0]


def test_query_without_search_params_warns():
    validator = QueryValidatorAgent()
    result = validator.validate(
        query_url="Patient",
        interpreted_capability=PATIENT_CAPABILITY,
    )
    assert result["valid"] is True
    assert any("no search parameters" in warning.lower() for warning in result["warnings"])


def test_nonstandard_meta_parameter_warns():
    validator = QueryValidatorAgent()
    result = validator.validate(
        query_url="Patient?_filter=name eq Smith",
        interpreted_capability=PATIENT_CAPABILITY,
    )
    assert result["valid"] is True
    assert any("_filter" in warning for warning in result["warnings"])


def test_sensitive_chained_parameter_sets_high_severity():
    validator = QueryValidatorAgent()
    result = validator.validate(
        query_url="Patient?subject.name=Smith",
        interpreted_capability=PATIENT_CAPABILITY,
        user_id="chain-user",
        server_key="hapi",
    )
    assert result["high_severity"] is True
    assert any("sensitive" in warning.lower() for warning in result["warnings"])


def test_chained_parameter_with_unknown_root_fails():
    validator = QueryValidatorAgent()
    result = validator.validate(
        query_url="Patient?unknown.chain=value",
        interpreted_capability=PATIENT_CAPABILITY,
    )
    assert result["valid"] is False
    assert "unknown_parameter" in result["error_types"]


def test_unsupported_comparator():
    validator = QueryValidatorAgent()
    result = validator.validate(
        query_url="Patient?gender=gtmale",
        interpreted_capability=PATIENT_CAPABILITY,
    )
    assert result["valid"] is False
    assert "unsupported_comparator" in result["error_types"]


def test_unknown_parameter_includes_suggestions():
    validator = QueryValidatorAgent()
    result = validator.validate(
        query_url="Patient?gende=male",
        interpreted_capability=PATIENT_CAPABILITY,
    )
    assert result["valid"] is False
    assert "Did you mean" in result["errors"][0]


def test_get_pattern_stats_exposes_threshold_flags():
    validator = QueryValidatorAgent()
    user = "stats-user"
    for _ in range(2):
        validator.validate(
            query_url="Patient?invalid=true",
            interpreted_capability=PATIENT_CAPABILITY,
            user_id=user,
            server_key="hapi",
        )

    stats = validator.get_pattern_stats(user, "hapi")
    assert stats["invalid_count_10m"] == 2
    assert stats["learner_threshold_met"] is False
    assert stats["human_threshold_met"] is False


def test_standard_count_parameter_is_allowed_without_warning():
    validator = QueryValidatorAgent()
    result = validator.validate(
        query_url="Patient?_count=10",
        interpreted_capability=PATIENT_CAPABILITY,
    )
    assert result["valid"] is True
    assert not any("_count" in warning for warning in result["warnings"])


def test_valid_comparator_on_date_parameter():
    validator = QueryValidatorAgent()
    result = validator.validate(
        query_url="Patient?birthdate=gt2000",
        interpreted_capability=PATIENT_CAPABILITY,
    )
    assert result["valid"] is True
    assert "unsupported_comparator" not in result["error_types"]


def test_valid_query_without_user_id_skips_pattern_tracking():
    validator = QueryValidatorAgent()
    result = validator.validate(
        query_url="Patient?invalid=true",
        interpreted_capability=PATIENT_CAPABILITY,
    )
    assert result["valid"] is False
    assert result["pattern_stats"] == {}


def test_pattern_history_isolated_per_server_key():
    """Same user on different servers should not share invalid-query history."""
    validator = QueryValidatorAgent()
    user = "cross-server-user"
    invalid = "Patient?invalid=true"

    for _ in range(3):
        validator.validate(
            query_url=invalid,
            interpreted_capability=PATIENT_CAPABILITY,
            user_id=user,
            server_key="hapi",
        )

    firely_result = validator.validate(
        query_url=invalid,
        interpreted_capability=PATIENT_CAPABILITY,
        user_id=user,
        server_key="firely",
    )

    assert firely_result.get("pattern_detected") is False
    assert firely_result["pattern_stats"]["invalid_count_10m"] == 1