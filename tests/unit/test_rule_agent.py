from src.agentic_layer.agents.rule_agent import RuleAgent


def test_rule_agent_escalates_to_learner():
    agent = RuleAgent()
    decision, audit = agent.decide_escalation(
        pattern_detected=True,
        validation_result={
            "pattern_stats": {
                "learner_threshold_met": True,
                "human_threshold_met": False,
                "invalid_count_10m": 3,
            },
            "high_severity": False,
        },
        user_id="user-1",
        server_key="hapi",
    )
    assert decision == "learner"
    assert audit["decision"] == "learner"


def test_rule_agent_escalates_to_human_on_threshold():
    agent = RuleAgent()
    decision, _ = agent.decide_escalation(
        pattern_detected=True,
        validation_result={
            "pattern_stats": {
                "learner_threshold_met": True,
                "human_threshold_met": True,
                "invalid_count_15m": 5,
            },
            "high_severity": False,
        },
        user_id="user-2",
        server_key="hapi",
    )
    assert decision == "human"


def test_rule_agent_escalates_to_human_on_high_severity():
    agent = RuleAgent()
    decision, _ = agent.decide_escalation(
        pattern_detected=True,
        validation_result={
            "pattern_stats": {"learner_threshold_met": False, "human_threshold_met": False},
            "high_severity": True,
        },
        user_id="user-3",
        server_key="hapi",
    )
    assert decision == "human"


def test_rule_agent_returns_none_without_pattern():
    agent = RuleAgent()
    decision, audit = agent.decide_escalation(
        pattern_detected=False,
        validation_result={"pattern_stats": {}},
        user_id="user-0",
        server_key="hapi",
    )
    assert decision == "none"
    assert audit["decision"] == "none"


def test_rule_agent_pattern_flag_without_thresholds_returns_none():
    agent = RuleAgent()
    decision, audit = agent.decide_escalation(
        pattern_detected=True,
        validation_result={
            "pattern_stats": {
                "learner_threshold_met": False,
                "human_threshold_met": False,
            },
            "high_severity": False,
        },
        user_id="user-4",
        server_key="hapi",
    )
    assert decision == "none"
    assert "thresholds not met" in audit["reasoning"]