# AGENTS.md — FHIR Query Validator Factory (Squid + Grok Build)

**Project Mission**  
Build trustworthy, auditable, spec-driven agentic systems for healthcare data interoperability — starting with a production-grade Generalized FHIR Query Validator that validates, executes, learns, and escalates with full human oversight and provenance.

This project follows **Software Factory principles**: spec before code, specialist agents over monolithic agents, explicit feedback loops, mandatory human gates at critical points, and measurable traceability.

---

## Core Principles (Non-Negotiable)

1. **Spec-Driven Development** — Every feature or agent starts from a clear markdown spec in `specs/` or `docs/spec/`. The master spec is `specs/fhir-query-validator-factory.md`.
2. **Specialist Agents** — Prefer small, focused agents with clear inputs/outputs and acceptance criteria (see `docs/spec/`).
3. **Explicit Feedback Loops** — Caching, pattern detection, learning, and escalation must be first-class and documented (see `docs/loop-engineering.md`).
4. **Human-in-the-Loop by Default** — Escalation thresholds and human gates are configurable but never removed for high-stakes paths.
5. **Traceability & Provenance** — Every decision produces an audit trail. Support per-agent traces and exportable JSON bundles (see `docs/traceability.md`).
6. **Security First** — OWASP mindset. Secrets only via `.env.local`. Threat model lives in the root agent.
7. **High Quality Bar** — ≥99% unit coverage on core logic. All code reviewed via Squid pipeline. CI must be green.
8. **Documentation as Code** — Keep `AGENTS.md`, specs, architecture, and ADRs up to date.

---

## Tech Stack & Tooling

- **Primary**: Python 3.11+, `uv`, `ruff`, `pytest`, Pydantic v2
- **Orchestration (preferred)**: Google ADK 2.0 graph workflows
- **HTTP Client**: `httpx` (with ETag/304, auth, and redirect control)
- **Testing**: `pytest` + `pytest-cov` (target ≥99% on core modules)
- **Observability (optional)**: Langfuse
- **CI/CD**: GitHub Actions + Makefile targets (`test`, `security`, `demo-*`)
- **Docs**: Sphinx + Markdown specs
- **Secrets**: `python-dotenv` + `.env.local` (git-ignored)

**Squid / Grok Build Integration**:
- Use `/squid-plan`, `/squid-implement-task`, `/squid-implement-night`, etc.
- All generated code must respect this `AGENTS.md`.
- Work in git worktrees for parallel agent work.
- Final output must pass PR Reviewer + On-Call + human merge gate.

---

## Project Structure (Expected)

```
specs/                          # Master + detailed feature specs for Squid
docs/
  spec/                         # Agent-level specifications (source of truth)
  adr/                          # Architecture Decision Records
  architecture.md
  traceability.md
  loop-engineering.md
  ...
src/agentic_layer/              # Core agents, workflow, config, auth
fhir_validator_agent/           # ADK root agent entrypoint (or equivalent)
scripts/                        # Demo scripts
tests/                          # High-coverage tests
```

---

## Coding & Quality Standards

- Write **type-hinted** Python. Use Pydantic for all I/O contracts.
- Every public function/class must have a docstring.
- Tests must be co-located or clearly named.
- Never hardcode secrets or server URLs — use configuration layer.
- Log at appropriate levels. Every agent action that affects output must be traceable.
- When implementing from a spec in `docs/spec/`, explicitly reference the acceptance criteria.
- Follow existing patterns for caching (ETag/304), escalation thresholds, and structured output contracts.

---

## Workflow with Squid + Grok Build

1. Update or create a spec in `specs/` or reference `docs/spec/`.
2. Run `/squid-plan <spec-file>` → review & approve plan.
3. Implement via `/squid-implement-task` or `/squid-implement-night`.
4. All code must pass tests + security scan before PR is considered ready.
5. Human performs final review and squash merge.

---

## Key Reference Documents (Agents must read these)

- `specs/fhir-query-validator-factory.md` (master spec)
- `docs/spec/*.md` (individual agent specs — binding)
- `docs/architecture.md`
- `docs/traceability.md`
- `docs/loop-engineering.md`
- `README.md` (demo commands, status)

---

## Definition of Done (for any task)

- Code implements the referenced spec(s) acceptance criteria.
- Tests added/updated and passing (≥99% coverage on changed modules).
- Security scan clean.
- Traceability / audit points added where decisions affect output.
- Documentation updated if behavior or interfaces changed.
- PR reviewed and CI green via Squid pipeline.
- Human approval + merge.

---

## Escalation & Human Gates Policy

Follow the thresholds defined in `docs/spec/rule-and-learner-spec.md` and `docs/spec/human-intervention-spec.md`:
- Learner escalation at 3+ failures / 10 min window.
- Human escalation at 5+ failures / 15 min or high-severity.
- Human must be able to pause, review context, and resume.

All escalations must produce clear, exportable trace reports.

---

## Security & Secrets

- Never commit `.env*` files containing secrets.
- Use `.env.example` + `.env.local`.
- Follow the threat model defined in the root agent.
- Re-run OWASP-style review after significant changes.

---

**This file (`AGENTS.md`) is the single source of truth for all agents (Grok Build, Squid sub-agents, and human developers). Update it when conventions change.**
