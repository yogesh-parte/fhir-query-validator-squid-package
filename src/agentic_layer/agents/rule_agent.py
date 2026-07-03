"""
RuleAgent
Evaluates pattern detection signals and decides escalation path.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from ..utils.audit_log import AuditLog


class RuleAgent:
    """
    Decides whether to activate Search Learner or trigger Human Intervention.
    """

    def __init__(self, audit_log: Optional[AuditLog] = None) -> None:
        self.audit_log = audit_log or AuditLog()

    def decide_escalation(
        self,
        pattern_detected: bool,
        validation_result: Dict[str, Any],
        *,
        user_id: Optional[str] = None,
        server_key: Optional[str] = None,
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Returns (decision, audit_record) where decision is
        'learner', 'human', or 'none'.
        """
        if not pattern_detected:
            audit = self._log(
                decision="none",
                reasoning="No repeated invalid pattern detected.",
                user_id=user_id,
                server_key=server_key,
                validation_result=validation_result,
            )
            return "none", audit

        print("[RuleAgent] Repeated invalid pattern detected. Deciding escalation...")

        stats = validation_result.get("pattern_stats", {})
        high_severity = validation_result.get("high_severity", False)
        human_threshold_met = stats.get("human_threshold_met", False)
        learner_threshold_met = stats.get("learner_threshold_met", False)

        if high_severity:
            decision = "human"
            reasoning = (
                "High-severity validation concern detected "
                "(potential sensitive data access pattern)."
            )
        elif human_threshold_met:
            decision = "human"
            reasoning = (
                f"User exceeded human threshold: {stats.get('invalid_count_15m', 0)} "
                "invalid queries within 15 minutes."
            )
        elif learner_threshold_met:
            decision = "learner"
            reasoning = (
                f"User exceeded learner threshold: {stats.get('invalid_count_10m', 0)} "
                "invalid queries within 10 minutes."
            )
        else:
            decision = "none"
            reasoning = "Pattern flag set but thresholds not met."

        audit = self._log(
            decision=decision,
            reasoning=reasoning,
            user_id=user_id,
            server_key=server_key,
            validation_result=validation_result,
        )
        return decision, audit

    def _log(
        self,
        *,
        decision: str,
        reasoning: str,
        user_id: Optional[str],
        server_key: Optional[str],
        validation_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        record = self.audit_log.record(
            event_type="escalation_decision",
            decision=decision,
            reasoning=reasoning,
            user_id=user_id,
            server_key=server_key,
            context={
                "error_types": validation_result.get("error_types", []),
                "pattern_stats": validation_result.get("pattern_stats", {}),
                "high_severity": validation_result.get("high_severity", False),
            },
        )
        return record.to_dict()