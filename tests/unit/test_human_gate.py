from src.agentic_layer.agents.human_gate import HumanInterventionGate


def test_human_gate_pause_notify_and_resume():
    gate = HumanInterventionGate()
    review = gate.request_human_review({
        "query_url": "Patient?bad=true",
        "user_id": "user-paused",
        "server_key": "hapi",
        "validation_result": {
            "pattern_stats": {"human_threshold_met": True},
            "high_severity": False,
        },
    })

    assert review["paused"] is True
    assert review["severity"] in {"high", "medium", "critical"}
    assert gate.is_paused("user-paused")

    resolved = gate.submit_review_decision(
        review["review_id"],
        reviewer="operator-1",
        decision="continue_monitoring",
        rationale="Benign learning pattern.",
    )
    assert resolved["resumed"] is True
    assert not gate.is_paused("user-paused")


def test_classify_severity_levels():
    gate = HumanInterventionGate()
    assert gate.classify_severity({"high_severity": True}).value == "critical"
    assert gate.classify_severity({
        "pattern_stats": {"human_threshold_met": True},
    }).value == "high"
    assert gate.classify_severity({
        "pattern_stats": {"learner_threshold_met": True},
    }).value == "medium"
    assert gate.classify_severity({}).value == "low"


def test_submit_review_decision_unknown_review_raises():
    gate = HumanInterventionGate()
    try:
        gate.submit_review_decision(
            "missing-review",
            reviewer="operator",
            decision="continue_monitoring",
            rationale="n/a",
        )
        raised = False
    except ValueError as exc:
        raised = True
        assert "Unknown review_id" in str(exc)
    assert raised


def test_request_human_review_defaults_anonymous_user():
    gate = HumanInterventionGate()
    review = gate.request_human_review({
        "query_url": "Patient?bad=true",
        "validation_result": {"pattern_stats": {"human_threshold_met": True}},
    })
    assert review["context"].get("user_id") is None
    assert gate.is_paused("anonymous")


def test_submit_review_decision_resolves_when_user_not_in_pause_map():
    gate = HumanInterventionGate()
    review = gate.request_human_review({
        "query_url": "Patient?bad=true",
        "user_id": "resolved-user",
        "validation_result": {"pattern_stats": {"human_threshold_met": True}},
    })
    gate._paused_users.clear()

    resolved = gate.submit_review_decision(
        review["review_id"],
        reviewer="operator",
        decision="mark_false_positive",
        rationale="Benign.",
    )

    assert resolved["resumed"] is True
    assert resolved["review"]["decision"] == "mark_false_positive"