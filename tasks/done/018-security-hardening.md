---
id: 018-security-hardening
feature: fhir-validator
status: done
---

# Security Hardening (Bandit, pip-audit, OWASP Doc)

## Scope

Establish security scanning in CI, implement opt-in production hardening controls, and produce OWASP-style security review documentation per `AGENTS.md` and Phase 5 patterns.

**Deliverables:**
- CI: ensure `make security` runs Bandit (`-ll` on `src`, `fhir_validator_agent`, `scripts`) and `pip-audit .` with zero High/Medium findings and no known vulnerable deps
- `.github/workflows/ci.yml` or dedicated `security.yml` — security job on push/PR (may parallelize with lint-and-test)
- `docs/reviews/owasp-security-review.md` — threat model, control matrix, Pass 1 findings, remediation status, retest criteria (adapt from Phase 5 template)
- Opt-in hardening flags via settings: `FHIR_HUMAN_GATE_REQUIRE_AUTH`, `FHIR_WORKFLOW_ISOLATE_STATE`, `FHIR_TRUST_CLIENT_USER_ID`, `FHIR_VERBOSE_LOGGING`, `FHIR_ENFORCE_HTTPS`
- `src/agentic_layer/utils/logging_safe.py` — redact tokens/keys from log output when verbose logging disabled
- `tests/unit/test_security_hardening.py` — SSRF blocks, secret redaction, human-gate auth flag behavior
- Pin runtime dependencies in `pyproject.toml` / `uv.lock` for reproducible `pip-audit` results
- Update `.env.example` with security-related variables (no real secrets)

Depends on tasks 004, 011, 012.

## Acceptance criteria

- [ ] `uv run bandit -r src fhir_validator_agent scripts -ll` reports 0 High and 0 Medium severity issues in CI.
- [ ] `uv run pip-audit .` reports no known vulnerabilities on pinned runtime dependencies.
- [ ] `docs/reviews/owasp-security-review.md` documents threat model, SSRF controls (`url_safety`), secret handling, human-gate auth, and log redaction with Pass 1 complete status.
- [ ] `test_security_hardening.py` verifies absolute/private URLs are blocked, secrets are redacted from logs, and production flags alter behavior without breaking default demo mode.
- [ ] `.env.example` documents all security env vars; `.gitignore` confirms `.env.local` is ignored; no secrets in git-tracked files (verified by grep test or pre-commit doc).

## Out of scope

- Full SMART on FHIR OAuth2 PKCE implementation.
- Penetration testing or third-party security audit engagement.
- SOC2/HIPAA compliance certification documentation.

## Log
### [PA] 2026-07-03 — Grooming
Initial task from /squid-plan on specs/fhir-query-validator-factory.md.