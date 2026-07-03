"""
HumanInterventionGate
Handles escalation to human review when needed.
"""

from __future__ import annotations

import time
import uuid
from enum import Enum
from typing import Any, Dict, Optional

from ..auth.operator import verify_human_gate_operator
from ..utils.audit_log import AuditLog
from ..utils.logging_safe import format_query_log_label, verbose_logging_enabled


class InterventionSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class HumanInterventionGate:
    """
    Pause/notify/review/resume workflow for human oversight with audit records.
    """

    def __init__(self, audit_log: Optional[AuditLog] = None) -> None:
        self.audit_log = audit_log or AuditLog()
        self._paused_users: dict[str, dict[str, Any]] = {}
        self._pending_reviews: dict[str, dict[str, Any]] = {}

    def classify_severity(self, validation_result: Dict[str, Any]) -> InterventionSeverity:
        if validation_result.get("high_severity"):
            return InterventionSeverity.CRITICAL
        stats = validation_result.get("pattern_stats", {})
        if stats.get("human_threshold_met"):
            return InterventionSeverity.HIGH
        if stats.get("learner_threshold_met"):
            return InterventionSeverity.MEDIUM
        return InterventionSeverity.LOW

    def request_human_review(self, context: Dict[str, Any]) -> Dict[str, Any]:
        user_id = context.get("user_id") or "anonymous"
        validation_result = context.get("validation_result", {})
        severity = self.classify_severity(validation_result)

        review_id = str(uuid.uuid4())
        now = time.time()

        self._paused_users[user_id] = {
            "paused_at": now,
            "review_id": review_id,
            "severity": severity.value,
        }

        review_record = {
            "review_id": review_id,
            "status": "paused_pending_review",
            "severity": severity.value,
            "message": "Automated processing paused pending human review.",
            "user_id": user_id,
            "query_url": context.get("query_url"),
            "server_key": context.get("server_key"),
            "validation_result": validation_result,
            "created_at": now,
            "decision_options": [
                "continue_monitoring",
                "show_enhanced_learning",
                "temporarily_block_user",
                "update_validation_rules",
                "mark_false_positive",
                "escalate_security",
            ],
        }
        self._pending_reviews[review_id] = review_record

        print(f"[HumanInterventionGate] Human review requested (severity={severity.value}).")
        self._notify(review_record)

        audit_context = review_record if verbose_logging_enabled() else {
            "review_id": review_id,
            "severity": severity.value,
            "server_key": context.get("server_key"),
            "query_label": format_query_log_label(context.get("query_url") or ""),
        }

        audit = self.audit_log.record(
            event_type="human_intervention_requested",
            decision="paused_pending_review",
            reasoning=f"Human review triggered with severity {severity.value}.",
            user_id=user_id,
            server_key=context.get("server_key"),
            context=audit_context,
        )

        return {
            "status": "human_review_required",
            "review_id": review_id,
            "severity": severity.value,
            "paused": True,
            "message": review_record["message"],
            "decision_options": review_record["decision_options"],
            "context": context,
            "audit": audit.to_dict(),
        }

    def submit_review_decision(
        self,
        review_id: str,
        *,
        reviewer: str,
        decision: str,
        rationale: str,
        operator_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        verify_human_gate_operator(operator_token=operator_token, reviewer=reviewer)

        review = self._pending_reviews.get(review_id)
        if not review:
            raise ValueError(f"Unknown review_id: {review_id}")

        user_id = review.get("user_id", "anonymous")
        review["status"] = "resolved"
        review["reviewer"] = reviewer
        review["decision"] = decision
        review["rationale"] = rationale
        review["resolved_at"] = time.time()

        if user_id in self._paused_users:
            del self._paused_users[user_id]

        audit = self.audit_log.record(
            event_type="human_intervention_resolved",
            decision=decision,
            reasoning=rationale,
            user_id=user_id,
            server_key=review.get("server_key"),
            context={"review_id": review_id, "reviewer": reviewer},
        )

        print(f"[HumanInterventionGate] Review {review_id} resolved: {decision}")
        return {"review": review, "audit": audit.to_dict(), "resumed": True}

    def is_paused(self, user_id: str) -> bool:
        return user_id in self._paused_users

    def _notify(self, review_record: Dict[str, Any]) -> None:
        # Demo notification channel — replace with email/ticket integration in production.
        print(
            "[HumanInterventionGate] NOTIFICATION → operators: "
            f"review_id={review_record['review_id']} "
            f"user={review_record['user_id']} "
            f"severity={review_record['severity']}"
        )