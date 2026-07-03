"""
Core validation workflow engine shared by ADK graph nodes and legacy runner.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Optional

import httpx

from ..agents import (
    CacheAgent,
    CapabilityInterpreterAgent,
    HumanInterventionGate,
    QueryExecutionAgent,
    QueryValidatorAgent,
    RuleAgent,
    QueryGeneratorAgent,
    SearchLearnerAgent,
)
from ..auth.identity import resolve_workflow_user_id
from ..config.settings import DEFAULT_SERVERS, get_auth_headers, get_server_config
from ..exceptions import AuthenticationRequiredError, CapabilityFetchError, UnknownServerKeyError
from ..state.workflow_state import ValidationWorkflowState
from ..utils.audit_log import AuditLog


@dataclass
class WorkflowAgents:
    """Bundle of workflow agents — shared singleton or per-request isolated instance."""

    audit_log: AuditLog
    cache_agent: CacheAgent
    interpreter: CapabilityInterpreterAgent
    validator: QueryValidatorAgent
    executor: QueryExecutionAgent
    rule_agent: RuleAgent
    learner_agent: SearchLearnerAgent
    human_gate: HumanInterventionGate
    query_generator: QueryGeneratorAgent

    def reset(self) -> None:
        """Clear in-memory agent state."""
        self.cache_agent._cache.clear()
        self.validator._pattern_history.clear()
        self.human_gate._paused_users.clear()
        self.human_gate._pending_reviews.clear()
        self.audit_log._records.clear()


_default_agents: Optional[WorkflowAgents] = None


def _build_agents() -> WorkflowAgents:
    audit_log = AuditLog()
    return WorkflowAgents(
        audit_log=audit_log,
        cache_agent=CacheAgent(),
        interpreter=CapabilityInterpreterAgent(),
        validator=QueryValidatorAgent(),
        executor=QueryExecutionAgent(),
        rule_agent=RuleAgent(audit_log=audit_log),
        learner_agent=SearchLearnerAgent(),
        human_gate=HumanInterventionGate(audit_log=audit_log),
        query_generator=QueryGeneratorAgent(),
    )


def workflow_isolation_enabled() -> bool:
    """When true, each execute_workflow call uses a fresh agent bundle."""
    return os.getenv("FHIR_WORKFLOW_ISOLATE_STATE", "false").lower() == "true"


def get_workflow_agents(*, isolate: bool = False) -> WorkflowAgents:
    """Return shared singleton agents or a fresh isolated bundle."""
    global _default_agents
    if isolate:
        return _build_agents()
    if _default_agents is None:
        _default_agents = _build_agents()
    return _default_agents


def _sync_module_exports(agents: WorkflowAgents) -> None:
    """Keep legacy module-level aliases pointed at the default singleton."""
    global _audit_log, cache_agent, interpreter, validator, executor, rule_agent, learner_agent, human_gate, query_generator
    _audit_log = agents.audit_log
    cache_agent = agents.cache_agent
    interpreter = agents.interpreter
    validator = agents.validator
    executor = agents.executor
    rule_agent = agents.rule_agent
    learner_agent = agents.learner_agent
    human_gate = agents.human_gate
    query_generator = agents.query_generator


_default = get_workflow_agents()
_sync_module_exports(_default)


def reset_singletons() -> None:
    """Clear module-level agent state between demos and tests."""
    get_workflow_agents().reset()


def _maybe_generate_query(
    state: ValidationWorkflowState,
    agents: WorkflowAgents,
) -> None:
    """Populate query_url from query_generation when not provided."""
    if state.query_url or not state.query_generation:
        return

    spec = state.query_generation
    resource_type = spec.get("resource_type")
    if not resource_type:
        state.workflow_error = "query_generation requires resource_type when query_url is omitted."
        return

    intent = spec.get("intent")
    if intent:
        state.generated_query = agents.query_generator.generate_from_intent(
            resource_type,
            intent,
        )
    else:
        state.generated_query = agents.query_generator.generate(
            resource_type,
            spec.get("criteria"),
            count=spec.get("count"),
            sort=spec.get("sort"),
        )

    if not state.generated_query.get("generated"):
        errors = state.generated_query.get("errors", ["Query generation failed."])
        state.workflow_error = "; ".join(errors)
        return

    state.query_url = state.generated_query["query_url"]
    print(f"[QueryGenerator] Generated query_url: {state.query_url}")


def build_final_output(state: ValidationWorkflowState) -> dict[str, Any]:
    """Align final output with query-validation-spec JSON contract."""
    validation = state.validation_result or {}
    execution = state.execution_result or {}
    executed = bool(execution.get("executed")) and execution.get("status") == "success"

    return {
        "valid": validation.get("valid", False),
        "server_used": state.server_key,
        "errors": validation.get("errors", []),
        "warnings": validation.get("warnings", []),
        "executed": executed,
        "results": execution if executed else None,
        "pattern_detected": state.pattern_detected,
        "escalation": state.escalation_decision,
        "guidance": state.learner_guidance or None,
        "human_review_required": bool(state.human_review),
        "human_review": state.human_review or None,
    }


def execute_workflow(initial: dict[str, Any]) -> ValidationWorkflowState:
    """Run the full validation workflow synchronously."""
    state = ValidationWorkflowState.model_validate(initial)
    isolate = workflow_isolation_enabled() or bool(initial.get("isolate_state"))
    agents = get_workflow_agents(isolate=isolate)

    state.user_id = resolve_workflow_user_id(state.user_id, state.auth_token)
    _maybe_generate_query(state, agents)

    if state.workflow_error and not state.query_url:
        state.validation_result = {
            "valid": False,
            "errors": [state.workflow_error],
            "warnings": state.generated_query.get("warnings", []) if state.generated_query else [],
            "error_types": ["query_generation_failed"],
            "pattern_detected": False,
        }
        state.execution_result = {"executed": False}
        state.final_output = build_final_output(state)
        return state

    if state.user_id and agents.human_gate.is_paused(state.user_id):
        state.workflow_error = f"User '{state.user_id}' is paused pending human review."
        state.validation_result = {
            "valid": False,
            "errors": [state.workflow_error],
            "warnings": [],
            "error_types": ["user_paused"],
            "pattern_detected": False,
        }
        state.execution_result = {"executed": False}
        state.final_output = build_final_output(state)
        return state

    try:
        server = get_server_config(state.server_key)
    except UnknownServerKeyError as exc:
        state.workflow_error = str(exc)
        state.validation_result = {
            "valid": False,
            "errors": [str(exc)],
            "warnings": [],
            "error_types": ["unknown_server"],
            "pattern_detected": False,
        }
        state.final_output = build_final_output(state)
        return state

    auth_headers = get_auth_headers(server, auth_token_override=state.auth_token)
    if server.requires_auth and not auth_headers:
        env_hint = DEFAULT_SERVERS.get(server.key, {}).get("auth_token_env")
        hint = (
            f" Set {env_hint} in .env.local (git-ignored) or pass auth_token at runtime."
            if env_hint
            else " Provide credentials via .env.local or auth_token at runtime."
        )
        message = (
            f"Authentication required for server '{server.key}' but no credentials were provided."
            + hint
        )
        state.workflow_error = message
        state.validation_result = {
            "valid": False,
            "errors": [message],
            "warnings": [],
            "error_types": ["authentication_required"],
            "pattern_detected": False,
        }
        state.final_output = build_final_output(state)
        return state

    print("\n=== [LOOP] Cache Invalidation Loop ===")
    try:
        state.capability_statement = agents.cache_agent.get_capability_statement(
            state.server_key,
            auth_token=state.auth_token,
        )
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code in {401, 403}:
            raise AuthenticationRequiredError(str(exc)) from exc
        raise CapabilityFetchError(str(exc)) from exc
    except httpx.RequestError as exc:
        raise CapabilityFetchError(str(exc)) from exc

    state.interpreted_capability = agents.interpreter.interpret(state.capability_statement)

    print("\n=== [LOOP] Validation + Pattern Detection ===")
    state.validation_result = agents.validator.validate(
        query_url=state.query_url,
        interpreted_capability=state.interpreted_capability,
        user_id=state.user_id,
        server_key=state.server_key,
    )
    state.pattern_detected = state.validation_result.get("pattern_detected", False)

    if state.validation_result.get("valid") and state.mode == "validate_and_execute":
        print("\n=== [LOOP] Validation → Execution Loop ===")
        state.execution_result = agents.executor.execute(
            query_url=state.query_url,
            server_key=state.server_key,
            auth_token=state.auth_token,
        )
    else:
        state.execution_result = {"executed": False}

    print("\n=== [LOOP] Pattern Detection → Learning / Human Escalation ===")
    if state.pattern_detected:
        decision, audit = agents.rule_agent.decide_escalation(
            pattern_detected=True,
            validation_result=state.validation_result,
            user_id=state.user_id,
            server_key=state.server_key,
        )
        state.escalation_decision = decision
        state.escalation_audit = audit

        if decision == "learner":
            state.learner_guidance = agents.learner_agent.provide_guidance(
                query_url=state.query_url,
                validation_result=state.validation_result,
                interpreted_capability=state.interpreted_capability,
            )
        elif decision == "human":
            state.human_review = agents.human_gate.request_human_review({
                "query_url": state.query_url,
                "user_id": state.user_id,
                "server_key": state.server_key,
                "validation_result": state.validation_result,
            })
    else:
        state.escalation_decision = "none"

    state.final_output = build_final_output(state)
    return state