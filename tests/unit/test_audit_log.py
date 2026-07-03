"""Unit tests for structured audit logging."""

import json

from src.agentic_layer.utils.audit_log import AuditLog


def test_record_and_query_filters_by_user_and_event_type():
    log = AuditLog()
    log.record("escalation", "learner threshold met", user_id="u1", decision="learner")
    log.record("human_review", "human threshold met", user_id="u1", decision="human")
    log.record("escalation", "other user", user_id="u2", decision="learner")

    user_events = log.query(user_id="u1")
    assert len(user_events) == 2

    escalations = log.query(event_type="escalation")
    assert len(escalations) == 2
    assert all(record.event_type == "escalation" for record in escalations)


def test_persist_and_reload_records(tmp_path):
    path = tmp_path / "audit" / "events.jsonl"
    first = AuditLog(persist_path=str(path))
    first.record(
        "human_review",
        "paused pending review",
        user_id="paused-user",
        server_key="hapi",
        decision="human",
        context={"review_id": "r-1"},
    )

    second = AuditLog(persist_path=str(path))
    records = second.query(user_id="paused-user")

    assert len(records) == 1
    assert records[0].decision == "human"
    assert records[0].context["review_id"] == "r-1"
    assert path.read_text(encoding="utf-8").strip().startswith("{")


def test_load_skips_blank_lines_and_missing_file(tmp_path):
    path = tmp_path / "audit.jsonl"
    path.write_text(
        '\n{"timestamp": 1.0, "event_type": "escalation", "user_id": "u1", '
        '"server_key": null, "decision": "learner", "reasoning": "test", "context": {}}\n\n',
        encoding="utf-8",
    )

    log = AuditLog(persist_path=str(path))
    assert len(log.query(user_id="u1")) == 1

    empty = AuditLog(persist_path=str(tmp_path / "blank.jsonl"))
    (tmp_path / "blank.jsonl").write_text("\n", encoding="utf-8")
    assert empty.query() == []