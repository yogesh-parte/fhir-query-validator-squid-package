---
id: 002-config-server-registry
feature: fhir-validator
status: done
---

# Settings and Multi-Server Registry

## Scope

Extend `src/agentic_layer/config/` with a typed `pydantic-settings` layer and a multi-server registry so agents resolve `server_key` → base URL, metadata URL, auth requirements, and per-server TTL without hardcoded URLs.

**Deliverables:**
- `config/settings.py` — expanded `Settings` with `FHIR_DEFAULT_SERVER_KEY`, escalation thresholds (`LEARNER_THRESHOLD_FAILURES=3`, `LEARNER_WINDOW_MINUTES=10`, `HUMAN_THRESHOLD_FAILURES=5`, `HUMAN_WINDOW_MINUTES=15`), cache TTL defaults, logging flags
- `config/server_registry.py` — `ServerConfig` dataclass/Pydantic model and `get_server_config(server_key)` lookup
- Default registry entries: `hapi`, `firely`, `spark`, `wildfhir` (public), `mockhealth` (authenticated, `MOCK_HEALTH_API_KEY`)
- Load order: `.env.local` → `.env` → environment variables (never commit secrets)
- Clear `ConfigurationError` for unknown `server_key` or missing required secrets
- Unit tests in `tests/unit/agentic_layer/config/` with env-var overrides via `monkeypatch`
- Update `.env.example` with all new variables (placeholders only)

Align with `docs/configuration.md`, `docs/public-test-servers.md`, and ADR-002.

## Acceptance criteria

- [ ] `get_server_config("hapi")` returns `https://hapi.fhir.org/baseR4` with `auth_required=False`; all four public servers and `mockhealth` resolve correctly.
- [ ] Unknown `server_key` raises a structured error with a list of supported keys; missing `MOCK_HEALTH_API_KEY` when resolving `mockhealth` yields a clear auth configuration error (no network call).
- [ ] Escalation thresholds and cache TTL are configurable via environment variables without code changes; defaults match `docs/spec/rule-and-learner-spec.md`.
- [ ] Settings singleton loads from `.env.local` first; unit tests verify override precedence and `extra="ignore"` for unknown env vars.
- [ ] ≥99% unit test coverage on `config/settings.py` and `config/server_registry.py`.

## Out of scope

- OAuth2 token acquisition flows (Bearer/static API key only for v1).
- Dynamic server registration at runtime or admin UI for server management.
- Redis or distributed configuration backends.

## Log
### [PA] 2026-07-03 — Grooming
Initial task from /squid-plan on specs/fhir-query-validator-factory.md.