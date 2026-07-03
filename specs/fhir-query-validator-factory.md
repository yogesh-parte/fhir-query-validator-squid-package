# Feature Spec: FHIR Query Validator Factory (Squid Implementation)

**Status:** Ready for Planning  
**Version:** 1.0 (Squid-adapted)  
**Last Updated:** 2026-07-02  
**Owner:** Yogesh  
**Related Specs:** `docs/spec/cache-agent-spec.md`, `docs/spec/query-validation-spec.md`, `docs/spec/query-execution-spec.md`, `docs/spec/rule-and-learner-spec.md`, `docs/spec/human-intervention-spec.md`  
**Related ADRs:** ADR-001 and subsequent decisions in `docs/adr/`  
**Related Docs:** `docs/architecture.md`, `docs/traceability.md`, `docs/loop-engineering.md`, `docs/process-overview.md`

## 1. Overview / North Star

Build a production-grade, spec-driven **Generalized FHIR Query Validator Factory** that can validate **any** FHIR search query against a server’s `CapabilityStatement`, optionally execute it, detect repeated invalid patterns, escalate intelligently (learner then human), and maintain full auditability and provenance.

This implementation will use the **Squid Software Factory** (5-agent pipeline) powered by **Grok Build** to generate clean, tested, reviewed code following the detailed agent specifications already defined in `docs/spec/`.

The system must support both public test servers and authenticated servers (including mock.health), while enforcing human-in-the-loop gates at critical points.

## 2. Goals

### Functional Goals
- Dynamically validate any FHIR search query (resource, parameters, modifiers, comparators) against a live or cached `CapabilityStatement`.
- Support multiple public FHIR test servers out of the box (HAPI, Firely, Spark, WildFHIR, etc.).
- Support authenticated servers via Bearer token / OAuth2 (with `mock.health` as first-class citizen).
- Provide two modes: `validate_only` and `validate_and_execute`.
- Detect repeated invalid query patterns from the same `user_id` and escalate appropriately.
- Return a strict, structured output contract + complete audit trail.

### Non-Functional Goals
- **Traceability & Provenance**: Every decision must be auditable (per-agent trace + JSON exportable bundle).
- **Human-in-the-Loop**: Explicit escalation gates (learner at 3+ failures/10min, human at 5+/15min or high severity).
- **Security & Compliance**: OWASP-hardened (as validated in `docs/reviews/owasp-security-review.md`). Secrets never committed. Clear threat model.
- **Testability**: ≥99% unit coverage on core logic + integration tests against public servers.
- **Observability**: Structured logging + optional Langfuse integration.
- **Extensibility**: Specialist agents (not monolithic). Easy to add new servers or escalation rules.

## 3. High-Level Architecture (Reference)

See `docs/architecture.md` for the authoritative diagram and details.

**Key Layers** (to be implemented):
- Human-Centric Planning Layer (already done — this spec + ADRs)
- Agentic Orchestration Layer (Squid-generated agents + workflow)
- Explicit Feedback Loops (caching, pattern detection, learning, escalation)
- Dual Paths support (full ADK/Cloud Run vs lighter direct usage)

**Core Specialist Agents** (detailed specs in `docs/spec/`):
- `CacheAgent`
- `QueryValidator Agent`
- `QueryExecution Agent`
- `Rule Agent`
- `Search Learner Agent`
- `HumanInterventionGate`

## 4. Detailed Behavior (Synthesized from Sub-Specs)

**Inputs** (from `query-validation-spec.md` and others):
- `query_url`: Full FHIR search URL
- `server_key`: e.g. `hapi`, `firely`, `mockhealth`
- `user_id` (optional, for pattern tracking)
- `mode`: `validate_only` | `validate_and_execute`
- `auth_token` (optional)

**Core Flow**:
1. Resolve `server_key` → base URL + auth config (from `.env` / settings).
2. `CacheAgent`: Fetch or retrieve cached `CapabilityStatement` (respect ETag/304, TTL, auth).
3. Interpret supported resources/parameters dynamically.
4. `QueryValidator Agent`: Validate query + detect invalid patterns.
5. If valid + `validate_and_execute` → `QueryExecution Agent`.
6. `Rule Agent`: On repeated invalid patterns → decide escalation (learner or human).
7. `Search Learner Agent`: Provide explanations + suggestions when triggered.
8. Always return structured result + full per-agent audit trail.

**Escalation Policy** (from specs + traceability):
- 3+ failures in 10 min window → activate learner.
- 5+ failures in 15 min or high-severity issue → human gate.
- Human can pause/resume/review (as demonstrated in `demo_agent_traceability.py`).

**Supported Servers** (from `query-validation-spec.md` + `public-test-servers.md`):
- Public: HAPI, Firely, Spark, WildFHIR, etc.
- Authenticated: mock.health (via `MOCK_HEALTH_API_KEY`)

## 5. Output Contract (Strict)

```json
{
  "valid": true,
  "server_used": "hapi",
  "errors": [],
  "warnings": [],
  "executed": false,
  "results": null,
  "audit_trail": { ... },
  "escalation": { "required": false, "type": null }
}
```

## 6. Acceptance Criteria (High-Level + Cross-Cutting)

**Must-Have (for v1 via Squid)**:
- All five agent specs in `docs/spec/` are implemented and pass their individual acceptance criteria.
- Supports all listed public + mock.health servers.
- Pattern detection + escalation logic works across servers.
- Full per-agent audit trail + exportable JSON trace bundle.
- ≥99% unit test coverage on `src/agentic_layer` equivalent.
- OWASP security review passes (re-validate after implementation).
- Human pause/resume gate works in at least one demo path.
- Clear, actionable error messages.
- Secrets loaded only from `.env.local` (never committed).

**Nice-to-Have (Phase 2+)**:
- Langfuse observability enabled in one demo path.
- OAuth2 / PKCE support for mock.health (beyond Bearer key).
- Distributed cache option (Redis).
- Automated deployment to Cloud Run / Agent Engine.

## 7. Tech Stack & Constraints (for Squid)

- **Primary**: Python 3.11+, `uv`, `ruff`, `pytest`, Pydantic v2
- **Orchestration**: Google ADK 2.0 graph workflow (preferred) **or** clean Python-native workflow engine compatible with Squid’s Python backend support
- **HTTP**: `httpx` (with proper auth, redirects control, ETag support)
- **Testing**: 148+ tests style (unit + integration against live public servers)
- **Security**: Bandit + pip-audit in CI; follow existing threat model
- **Docs**: Sphinx + clear agent specs
- **Deployment**: Docker + GitHub Actions (Squid scaffold defaults are acceptable)

**Constraints**:
- Follow the exact folder structure and naming from `AGENTS.md` once generated.
- All code must be traceable back to this spec + sub-specs in `docs/spec/`.
- No secrets in git.
- Human gates must remain explicit and configurable.

## 8. Quality Gates (Squid Pipeline)

- Product Architect produces detailed task plan + ADR updates.
- Every task must include tests (unit + at least one integration where applicable).
- PR Reviewer + On-Call must pass before merge.
- Final human review + squash merge only after green CI.

## 9. Demo & Validation Scenarios

At minimum, the following must work after implementation:
- `make demo-loops` (or equivalent) against HAPI
- `make demo-agent-trace` with human pause/resume
- `make demo-mockhealth` (requires `MOCK_HEALTH_API_KEY`)
- Query generator → validate flow
- Escalation trace export

## 10. Open Questions / Future Work

- Preferred OAuth flow for protected servers (SMART on FHIR PKCE)?
- Distributed caching strategy?
- Notification mechanism for human escalation (email / ticket / dashboard)?
- Full nanopublication provenance assertions on every decision (future extension)?

---
