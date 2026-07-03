"""
ADK / agents-cli entry point for the FHIR Query Validator Factory.

Run with:
  adk web --port 8080          # from repo root (parent of this package)
  adk run fhir_validator_agent
  agents-cli playground        # when scaffolded via agents-cli

Threat model (ADK Web / networked exposure)
-------------------------------------------
This agent executes the full validation workflow in-process, including outbound
HTTP to registered FHIR servers and optional query execution. Treat ADK Web as
**trusted-operator / demo infrastructure**, not a multi-tenant production API.

Risks when exposed on a network without additional controls:
  - Callers can supply query_url, server_key, user_id, and auth_token in workflow
    state (SSRF class mitigated in QueryExecutionAgent; auth tokens forwarded).
  - Module-level workflow singletons share pattern history and human-gate pause
    maps across sessions unless FHIR_WORKFLOW_ISOLATE_STATE=true.
  - Human review resolution (submit_review_decision) is unauthenticated unless
    FHIR_HUMAN_GATE_REQUIRE_AUTH=true and FHIR_HUMAN_GATE_OPERATOR_TOKEN are set.
  - Client-supplied user_id is trusted unless FHIR_TRUST_CLIENT_USER_ID=false.

Recommended production controls:
  - Terminate TLS at an API gateway with authenticated callers.
  - Set FHIR_WORKFLOW_ISOLATE_STATE=true, FHIR_TRUST_CLIENT_USER_ID=false,
    FHIR_HUMAN_GATE_REQUIRE_AUTH=true, FHIR_VERBOSE_LOGGING=false.
  - Do not expose ADK Web directly to the public internet.
"""

from src.agentic_layer.graph.validation_workflow import root_agent

__all__ = ["root_agent"]