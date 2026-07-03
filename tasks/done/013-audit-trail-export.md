---
id: 013-audit-trail-export
feature: fhir-validator
status: done
---

# Audit Trail Export

## Scope

Implement audit trail assembly and JSON export bundle per `docs/traceability.md` and master spec §5, enabling per-agent provenance and demo `--export` functionality.

**Deliverables:**
- `src/agentic_layer/state/audit_trail.py` — `AuditTrailAssembler` collecting per-agent blocks from workflow run
- `export_trace_bundle(response: ValidationResponse, metadata: dict) -> dict` producing versioned JSON schema (`trace_bundle_version: "1.0"`)
- Bundle contents: `correlation_id`, `server_key`, `query_url`, `mode`, per-agent sections (Cache, Interpreter, Validator, Execution, Rule, Learner, Human), timestamps, durations, decisions
- `export_to_file(path: Path, bundle: dict)` with atomic write and pretty-print option
- CLI flag support hook for demo scripts: `--export traces.json`
- Unit tests validating bundle schema, agent ordering, and redaction of secrets
- Sphinx/docstring cross-reference to `docs/traceability.md`

Depends on tasks 001, 004, 012.

## Acceptance criteria

- [ ] Exported JSON bundle includes all invoked agents for a workflow run with `agent_name`, `started_at`, `duration_ms`, and decision summary fields.
- [ ] `--export` from workflow API writes valid JSON that round-trips through `json.load()`; file includes `trace_bundle_version` and `correlation_id`.
- [ ] No `auth_token`, `MOCK_HEALTH_API_KEY`, or Bearer values appear anywhere in exported bundle (verified by unit test grep/redaction assertions).
- [ ] HumanInterventionGate decisions and learner suggestions appear in dedicated bundle sections when triggered.
- [ ] ≥99% unit test coverage on assembler and export functions; golden-file test compares bundle structure against fixture.

## Out of scope

- Langfuse export or OpenTelemetry trace propagation.
- Nanopublication provenance assertions.
- Long-term audit storage in database or S3.

## Log
### [PA] 2026-07-03 — Grooming
Initial task from /squid-plan on specs/fhir-query-validator-factory.md.