---
id: 003-auth-provider
feature: fhir-validator
status: done
---

# Auth Provider (Bearer + mock.health)

## Scope

Implement `src/agentic_layer/auth/` to resolve authentication headers for FHIR HTTP calls, with first-class support for public servers (no auth) and `mock.health` via `MOCK_HEALTH_API_KEY`.

**Deliverables:**
- `auth/provider.py` — `AuthProvider` protocol and `BearerAuthProvider` implementation
- `auth/mockhealth.py` — `MockHealthAuthProvider` reading `MOCK_HEALTH_API_KEY` from settings; never logs or returns raw key values
- `auth/factory.py` — `get_auth_provider(server_key, auth_token_override=None)` selecting the correct provider from `ServerConfig`
- Header builder: `Authorization: Bearer <token>` for protected servers; empty headers for public servers
- Runtime `auth_token` parameter overrides env-based token when provided (ephemeral tests)
- Unit tests covering public server (no header), mock.health (env key), override token, and missing-key error paths
- Redaction helper ensuring tokens never appear in exception messages or debug strings

Reference `docs/configuration.md` §3.1 and `docs/spec/query-validation-spec.md` §5.

## Acceptance criteria

- [ ] Public servers (`hapi`, `firely`, etc.) produce no `Authorization` header; `mockhealth` produces `Bearer` header from `MOCK_HEALTH_API_KEY` when set.
- [ ] Missing `MOCK_HEALTH_API_KEY` for `mockhealth` returns a structured `AuthError` with actionable setup instructions (copy `.env.example` → `.env.local`).
- [ ] Runtime `auth_token` override takes precedence over env var; override value is never logged or included in audit trail payloads.
- [ ] `get_auth_provider` is the single entry point used by CacheAgent and QueryExecution (no duplicated auth logic elsewhere).
- [ ] Unit tests achieve ≥99% coverage on `src/agentic_layer/auth/` with assertions that error messages contain no secret substrings.

## Out of scope

- OAuth2 client-credentials token refresh and SMART on FHIR PKCE flows.
- Human-gate operator authentication (`FHIR_HUMAN_GATE_REQUIRE_AUTH`) — deferred to task 011/018.
- mTLS or certificate-based authentication.

## Log
### [PA] 2026-07-03 — Grooming
Initial task from /squid-plan on specs/fhir-query-validator-factory.md.