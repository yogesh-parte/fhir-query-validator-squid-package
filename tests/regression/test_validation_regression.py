"""
Regression tests for query validation behavior.
These tests ensure that core validation logic does not regress over time.
"""

import pytest
from src.agentic_layer.agents.query_validator import QueryValidatorAgent


def test_basic_patient_gender_query_still_works():
    """Ensure basic valid queries continue to pass."""
    validator = QueryValidatorAgent()
    result = validator.validate(
        query_url="Patient?gender=male",
        interpreted_capability={
            "supported_resources": {
                "Patient": {
                    "search_params": [{"name": "gender", "type": "token", "modifiers": [], "comparators": []}],
                }
            }
        },
    )
    assert result["valid"] is True
