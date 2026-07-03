# Agent Specifications — README

This folder (`docs/spec/`) contains the **detailed, machine-readable specifications** for each specialist agent in the FHIR Query Validator Factory.

These specs are the primary source of truth for implementation. They are designed to be consumed directly by AI coding agents (especially Squid's Product Architect) during planning and implementation.

## Purpose

- Define clear **inputs, outputs, behavior, and acceptance criteria** for every agent.
- Enable **spec-driven development** — code is generated to satisfy these specs rather than from vague requirements.
- Support **traceability** — every implementation decision can be linked back to a specific section of a spec.
- Facilitate **review and iteration** — specs can be versioned, reviewed, and refined independently of code.

## Standard Spec Structure

Every spec in this folder follows a consistent template:

| Section                    | Description                                                                 | Why it matters for Squid |
|----------------------------|-----------------------------------------------------------------------------|--------------------------|
| **Overview**               | One-paragraph description of the agent's responsibility                     | Helps PA understand scope |
| **Goals**                  | What success looks like functionally and non-functionally                   | Drives acceptance criteria |
| **Inputs**                 | Table of required/optional inputs with types and descriptions               | Used for interface design & validation |
| **Outputs**                | Example JSON contracts for success and error cases                          | Enables contract-first development & testing |
| **Core Behavior**          | Step-by-step logic the agent must follow                                    | Primary implementation guidance |
| **Feedback Loops**         | How this agent interacts with other agents and the overall workflow         | Critical for the "explicit loops" principle |
| **Edge Cases & Error Handling** | Known difficult scenarios and how they should be handled               | Prevents fragile implementations |
| **Acceptance Criteria**    | Measurable checklist that must be satisfied                                 | Used by Tester agent and human reviewers |
| **Open Questions**         | Known ambiguities or future work                                            | Captures technical debt and roadmap items |

## Current Specs

| File                              | Agent / Capability                     | Status     | Notes |
|-----------------------------------|----------------------------------------|------------|-------|
| `cache-agent-spec.md`             | CapabilityStatement caching + invalidation | Complete  | Foundational |
| `query-validation-spec.md`        | Core query validation against CapabilityStatement | Complete | Original spec |
| `query-execution-spec.md`         | Execute validated queries              | Complete  | New |
| `rule-and-learner-spec.md`        | Pattern detection + learner + escalation decision | Complete | New |
| `human-intervention-spec.md`      | Human gate, pause/resume, override     | Complete  | New |

## How These Specs Are Used

1. **Planning Phase** (`/squid-plan`):
   - Squid's Product Architect reads the master spec + individual agent specs.
   - It produces a task breakdown that maps to these acceptance criteria.

2. **Implementation Phase**:
   - Software Engineer agent implements behavior described in "Core Behavior".
   - Tester agent writes tests that verify the "Acceptance Criteria".

3. **Review Phase**:
   - PR Reviewer checks that the implementation satisfies the spec sections.
   - Human reviewers can trace code back to specific spec requirements.

## Versioning & Status Conventions

- **Status**: `Draft` → `Ready for Implementation` → `Implemented` → `Deprecated`
- **Version**: Semantic (major.minor). Increment minor for clarifications, major for breaking changes.
- **Last Updated**: Date of last meaningful change.
- **Related ADRs / Specs**: Cross-references for context.

## Best Practices

- Keep specs **focused** — one spec per agent or major capability.
- Use tables for Inputs/Outputs — easier for agents to parse.
- Include realistic JSON examples.
- Update specs **before** asking Squid to implement changes.
- When a spec is implemented, consider moving or linking the final acceptance criteria into tests or documentation.

## Related Documents

- `specs/fhir-query-validator-factory.md` — Master feature spec that orchestrates all agent specs.
- `AGENTS.md` — Project constitution and workflow rules.
- `docs/architecture.md` — High-level system view and data flow.
- `docs/loop-engineering.md` — Guidance on designing explicit feedback loops.
- `docs/traceability.md` — Requirements for audit trails and provenance.

---

**These specifications are living documents.** Update them as requirements evolve, and re-run `/squid-plan` on the master spec to propagate changes through the factory.
