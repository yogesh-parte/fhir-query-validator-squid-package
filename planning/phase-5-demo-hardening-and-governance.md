# Phase 5: Demo Parity, Security Hardening & Governance

**Phase Duration (Actual):** ~2 days (2026-06-30)  
**Focus:** Close the gap between implementation and demonstration; add production-oriented security controls; establish review artifacts  
**Status:** Complete

## 1. Objectives

- Achieve **demo parity** across CLI scripts, mock.health, and Google ADK entry points
- Expand **test coverage** and integration paths for the full workflow engine
- Run **security and compliance reviews** with tracked remediation
- Add **opt-in production hardening** without breaking local demo behavior
- Document **ADK Web threat model** and security configuration

## 2. Scope of This Phase

**In Scope:**
- New demo scripts: agent traceability, mock.health loops, ADK CLI/Web
- Shared demo utilities (`scripts/_demo_utils.py`)
- Makefile targets wired to real demos and `make test`
- Unit and integration test expansion (workflow engine, graph nodes, security hardening)
- OWASP Pass 1 review → remediation → Pass 2 review
- Spec implementation compliance review (Pass 2)
- Security controls: URL safety, human-gate operator auth, workflow isolation, identity resolution, log redaction
- Pinned runtime dependencies; Bandit + `pip-audit` CI (`.github/workflows/security.yml`)
- Planning roadmap update (this file)

**Out of Scope:**
- Production deployment automation (Agent Engine / Cloud Run)
- Distributed cache (Redis), Langfuse enabled by default
- Full OAuth authorization-code / PKCE flows
- Human-gate email/ticket notification integrations

## 3. Key Deliverables

| Deliverable | Location | Status |
|-------------|----------|--------|
| Agent traceability demo | `scripts/demo_agent_traceability.py` | Done |
| mock.health loop demo | `scripts/demo_loops_mockhealth.py` | Done |
| Google ADK CLI demo | `scripts/demo_adk_cli.py` | Done |
| Google ADK Web demo | `scripts/demo_adk_web.py` | Done |
| ADK entry point + threat model | `fhir_validator_agent/agent.py` | Done |
| Shared demo helpers | `scripts/_demo_utils.py` | Done |
| SSRF mitigation (URL builder, no redirects) | `src/agentic_layer/utils/url_safety.py`, `query_execution.py` | Done |
| Human-gate operator auth (opt-in) | `src/agentic_layer/auth/operator.py` | Done |
| Workflow identity resolution (opt-in) | `src/agentic_layer/auth/identity.py` | Done |
| Per-request workflow isolation (opt-in) | `workflow_engine.py` (`WorkflowAgents`) | Done |
| Production log redaction (opt-in) | `src/agentic_layer/utils/logging_safe.py` | Done |
| Security env documentation | `.env.example` | Done |
| OWASP security review (Pass 1 + Pass 2) | `docs/reviews/owasp-security-review.md` | Done |
| Spec compliance review (Pass 2) | `docs/reviews/spec-implementation-compliance-review.md` | Done |
| Security hardening tests | `tests/unit/test_security_hardening.py` | Done |
| CI security workflow | `.github/workflows/security.yml` | Done |
| Pinned runtime dependencies | `pyproject.toml` | Done |

## 4. Demo matrix (end of Phase 5)

| Behavior | Code | `demo_loops` | `demo_traceability` | `demo_agent_traceability` | `demo_loops_mockhealth` | ADK CLI/Web | Notebook |
|----------|------|--------------|---------------------|---------------------------|-------------------------|-------------|----------|
| Cache + validate + execute | ✅ | ✅ HAPI | ✅ HAPI | ✅ multi-server | ✅ mockhealth | ✅ HAPI | ✅ |
| Learner escalation | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ in-process | ✅ |
| Human escalation + pause/resume | ✅ | ❌ | ❌ | ✅ | partial | ❌ | ✅ |
| mock.health authenticated | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ | partial |
| Per-agent audit trail | ✅ | ❌ | partial | ✅ | ❌ | partial (JSONL) | partial |
| `validate_only` mode | ✅ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |

## 5. Security posture (end of Phase 5)

| Control | Default (demos) | Production (`FHIR_*` flags) |
|---------|-----------------|-------------------------------|
| Absolute `query_url` blocked | ✅ always | ✅ always |
| Redirect following on execution | ❌ disabled | ❌ disabled |
| Human-gate operator auth | Off | `FHIR_HUMAN_GATE_REQUIRE_AUTH=true` |
| Per-request agent isolation | Off (singletons) | `FHIR_WORKFLOW_ISOLATE_STATE=true` |
| Trusted client `user_id` | On | `FHIR_TRUST_CLIENT_USER_ID=false` |
| Verbose query logging | On | `FHIR_VERBOSE_LOGGING=false` |

See `docs/reviews/owasp-security-review.md` (Pass 2) for full findings and retest criteria.

## 6. Test & review evidence

| Metric | Value (2026-06-30) |
|--------|---------------------|
| Tests passing | **148** (unit + integration + regression) |
| `src/agentic_layer` unit coverage | ~99% |
| Bandit (`-ll`) | 0 High / 0 Medium |
| `pip-audit .` (pinned runtime deps) | No known vulnerabilities |
| OWASP review | Pass 1 → remediated → Pass 2 |
| Spec compliance review | Pass 2 (see `docs/reviews/`) |

## 7. Success Criteria

- [x] Demo scripts cover HAPI, mock.health, and ADK CLI/Web entry points
- [x] Human-gate pause → review → resume demonstrated in at least one script and integration test
- [x] OWASP review completed with documented remediation and Pass 2 retest
- [x] Security hardening implemented with opt-in production flags (demos unchanged by default)
- [x] CI runs Bandit and pip-audit on push/PR
- [x] Planning roadmap reflects Phases 0–5 completion

## 8. Remaining follow-ups (post–Phase 5)

| Priority | Item |
|----------|------|
| P2 | Notebook parity — add mock.health and human-gate cells to match CLI demos |
| P2 | Align `docs/loop-engineering.md` thresholds and ETag wording with code |
| P3 | Commit `uv.lock` / reproducible lockfile for transitive deps |
| P3 | `follow_redirects=False` on `CacheAgent` metadata fetch (consistency) |
| suggestion | Langfuse observability enabled in a dedicated demo path |
| suggestion | Agent Engine / Cloud Run deployment automation |

## 9. Alignment with Software Factory

Phase 5 demonstrates that **planning and review artifacts stay current** as the system matures — not only building features, but proving them (tests), governing them (security/spec reviews), and making them observable (demos, traceability, audit log).

---

**Phase 5 Complete — 2026-06-30**