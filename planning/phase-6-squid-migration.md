# Phase 6: Squid + Grok Build Implementation & Migration Plan

**Phase:** 6 — Software Factory Migration  
**Status:** Planning  
**Owner:** Yogesh  
**Date:** 2026-07-03  
**Related Specs:** All files in `docs/spec/` and `specs/fhir-query-validator-factory.md`  
**Goal:** Re-implement (or significantly harden) the FHIR Query Validator Factory using the Squid multi-agent software factory powered by Grok Build, while preserving all existing functional and non-functional requirements.

---

## 1. Objectives

- Leverage Squid’s 5-agent pipeline (PA → SWE → Tester → PR Reviewer → On-Call) to produce higher-quality, better-tested, and better-reviewed code with minimal manual effort.
- Maintain 100% compatibility with the original acceptance criteria defined in `docs/spec/`.
- Improve traceability, consistency, and governance through explicit spec-driven development.
- Create a repeatable pattern that can be applied to future healthcare agentic systems (DaVita renal ontology, Mayo semantic layer, clinical trial automation, etc.).
- Reduce long-term maintenance burden through higher test coverage and automated review gates.

## 2. Scope

**In Scope**
- Full re-implementation of the five core agents using the specs in `docs/spec/`.
- Integration with existing configuration, public test servers, and `mock.health` support.
- Preservation of escalation logic, human gate, learner, caching (ETag/304), and audit trail.
- Demo scripts (`demo-loops`, `demo-agent-trace`, `demo-mockhealth`, query generator).
- Security hardening (re-validation of OWASP controls).
- High test coverage target (≥99% on core logic).

**Out of Scope (Phase 6)**
- Major new functional features (e.g., full SMART on FHIR OAuth2 PKCE, distributed cache).
- Production deployment automation (Cloud Run / Agent Engine) — deferred to Phase 7.
- Nanopublication provenance assertions on every decision (future extension).
- Web UI for human intervention gate.

## 3. Migration Strategy

### Option A — Greenfield (Recommended for cleanest result)
- Create a new repository or major feature branch.
- Use `/squid-scaffold` to establish project structure.
- Copy specs + `AGENTS.md` from this package.
- Run full `/squid-plan` + `/squid-implement-night`.
- Port only the best parts of the original implementation (tests, demo utilities, configuration patterns).

**Advantages**: Clean architecture, full benefit of Squid discipline, easier to maintain going forward.

### Option B — Incremental Enhancement (of existing repo)
- Keep the current ADK-based implementation as the "reference".
- Use Squid to implement new/refactored modules in parallel (e.g., new `CacheAgent` implementation).
- Gradually replace components while running both versions side-by-side for validation.
- Use feature flags or dual-mode execution during transition.

**Advantages**: Lower risk, can validate behavior against existing tests.

**Recommendation**: Start with **Option A** in a new worktree or separate repo for the first end-to-end run. Merge learnings back into the main repository.

## 4. High-Level Task Breakdown (Expected from Squid PA)

1. **Foundation**
   - Project scaffolding + `AGENTS.md` alignment
   - Configuration layer (`.env`, settings, server registry)
   - Shared data models (Pydantic contracts for inputs/outputs)

2. **Core Agents** (one task or sub-tasks per spec)
   - CacheAgent (ETag/304, TTL, graceful degradation)
   - QueryValidator Agent (dynamic CapabilityStatement interpretation + pattern detection hooks)
   - QueryExecution Agent (safe execution + result structuring)
   - Rule + Search Learner Agents (threshold evaluation, suggestions)
   - HumanInterventionGate (pause/resume context packaging + decision recording)

3. **Workflow Orchestration**
   - Main workflow engine (ADK graph or lightweight equivalent)
   - Integration of all agents with explicit feedback loops
   - Audit trail assembly and export

4. **Demos & Observability**
   - Port / recreate `demo-loops.py`, `demo_agent_traceability.py`, etc.
   - Structured logging + optional Langfuse integration
   - Human gate demo with pause/resume

5. **Testing & Quality**
   - Unit tests for every agent (target ≥99% coverage)
   - Integration tests against public servers + mock.health
   - Security scan (Bandit + pip-audit)
   - CI pipeline via GitHub Actions (Squid On-Call)

6. **Documentation & Traceability**
   - Update architecture and traceability docs
   - Generate Sphinx documentation
   - Final spec compliance review

## 5. Risks & Mitigations

| Risk                              | Likelihood | Impact | Mitigation |
|-----------------------------------|------------|--------|----------|
| Behavioral drift from original    | Medium     | High   | Run parallel validation against original test suite and public servers |
| Human gate UX too basic for demos | Low        | Medium | Start with rich console/JSON output; plan web UI later |
| ADK integration complexity        | Medium     | Medium | Support both ADK graph and pure Python workflow in spec |
| Token / cost of full Squid run    | Medium     | Low    | Use task-by-task mode first; run full night build during off-peak |
| Loss of institutional knowledge   | Low        | High   | Keep original repo as reference; document key design decisions in ADRs |

## 6. Success Criteria

- All five agent specs have passing implementations that meet their Acceptance Criteria.
- `make demo-loops`, `make demo-agent-trace`, and `make demo-mockhealth` work end-to-end.
- Human pause/resume gate functions in at least one demo path.
- Test coverage ≥99% on `src/agentic_layer` equivalent.
- OWASP security review passes (or documented exceptions).
- Full audit trail + exportable JSON trace bundle works.
- Code is reviewed and merged via Squid pipeline with two human gates.

## 7. Timeline Estimate (Rough)

- **Week 1**: Setup, scaffolding, foundation tasks, CacheAgent + QueryValidator
- **Week 2**: Remaining agents + workflow orchestration + basic demos
- **Week 3**: Testing, security, human gate polish, documentation
- **Week 4**: Final review, migration learnings captured, Phase 7 planning

Actual timeline will be refined by the Squid Product Architect during the planning phase.

## 8. Post-Phase 6 Opportunities (Phase 7+)

- Automated deployment to Cloud Run / Vertex AI Agent Engine
- Web-based Human Intervention dashboard
- Long-term learner memory + pattern store
- Nanopublication provenance on decisions
- Integration into larger clinical trial or patient triage platforms
- Apply the same Squid + spec-driven pattern to other domains (renal ontology, Mayo Digital Front Door, etc.)

---

**This document serves as the high-level migration charter.** The detailed task plan will be generated dynamically by Squid when you run:

```bash
/squid-plan specs/fhir-query-validator-factory.md
```

Update this document with actual outcomes after the first planning and implementation runs.
