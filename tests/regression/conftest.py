"""Shared fixtures for regression (golden behavior) tests."""

PATIENT_CAPABILITY = {
    "supported_resources": {
        "Patient": {
            "search_params": [
                {
                    "name": "gender",
                    "type": "token",
                    "modifiers": ["exact", "missing"],
                    "comparators": [],
                },
                {
                    "name": "birthdate",
                    "type": "date",
                    "modifiers": ["missing"],
                    "comparators": ["gt", "lt"],
                },
                {
                    "name": "subject",
                    "type": "reference",
                    "modifiers": ["missing"],
                    "comparators": [],
                },
            ]
        }
    }
}

FINAL_OUTPUT_REQUIRED_KEYS = frozenset(
    {
        "valid",
        "server_used",
        "errors",
        "warnings",
        "executed",
        "results",
        "pattern_detected",
        "escalation",
        "guidance",
        "human_review_required",
        "human_review",
    }
)
