---
id: 006-capability-interpreter
feature: fhir-validator
status: done
---

# CapabilityInterpreter Agent

## Scope

Implement `src/agentic_layer/agents/capability_interpreter.py` to dynamically interpret a FHIR `CapabilityStatement` into a structured index usable by QueryValidator: supported resources, search parameters, types, modifiers, and comparators.

**Deliverables:**
- `CapabilityInterpreter` class with `interpret(capability_statement: dict) -> CapabilityIndex` (Pydantic model in entities)
- Extract from `rest[].resource[]`: resource type, supported interactions, `searchParam` definitions (name, type, modifier lists)
- Build lookup maps: `resource → {param_name → SearchParamInfo}` including supported comparators per param type (date, number, string, token, etc.)
- Handle missing or partial CapabilityStatement sections with clear warnings (not silent failures)
- Unit tests using fixture CapabilityStatement JSON snippets from HAPI and mock.health shapes
- Integration test chaining CacheAgent → CapabilityInterpreter against live HAPI metadata

Referenced in `docs/architecture.md` specialist agents table; consumed by QueryValidator (task 007).

## Acceptance criteria

- [ ] Given a HAPI CapabilityStatement fixture, `interpret()` returns `Patient` with `birthDate` (and not `birthdate`) as a supported search parameter with correct type and comparators.
- [ ] Unsupported resource types are absent from the index; QueryValidator can query `index.supports_param("Patient", "birthDate")` in O(1) or near-O(1) lookup.
- [ ] Modifiers declared in CapabilityStatement (e.g., `:exact`, `:missing`) are captured per parameter; undeclared modifiers are flagged as unsupported downstream.
- [ ] Invalid or non-FHIR JSON input raises `CapabilityInterpretError` with structured detail; partial statements produce warnings in output model.
- [ ] ≥99% unit test coverage on interpreter logic; integration test passes with live HAPI CapabilityStatement.

## Out of scope

- Custom operations or `$validate` operation parsing beyond search parameters.
- FHIR version negotiation across R4/R5 mixed servers.
- Caching interpreted indexes separately from raw CapabilityStatement (interpreter runs on cache hit/miss each time in v1).

## Log
### [PA] 2026-07-03 — Grooming
Initial task from /squid-plan on specs/fhir-query-validator-factory.md.