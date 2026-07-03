---
id: 005-cache-agent
feature: fhir-validator
status: done
---

# CacheAgent

## Scope

Implement `src/agentic_layer/agents/cache_agent.py` per `docs/spec/cache-agent-spec.md`: fetch, cache, and invalidate FHIR `CapabilityStatement` documents with ETag/304 support, TTL expiration, and graceful degradation.

**Deliverables:**
- `CacheAgent` class with `fetch(server_key, auth_token=None, force_refresh=False)` → `CacheAgentOutput` (entities from task 001)
- In-memory thread-safe cache keyed by `server_key` + auth scope (ADR-002: no Redis in v1)
- HTTP GET to `{base_url}/metadata` via `httpx` with `If-None-Match` when ETag present; handle 200, 304, 401/403, timeouts
- Default TTL 15 minutes (configurable per server); `cache_status`: `hit` | `miss` | `refreshed` | `304`
- On transient failure: return last-known-good cached document with warning in audit block
- Parse and minimally validate CapabilityStatement JSON structure before caching
- Unit tests with `httpx.MockTransport` covering all cache_status paths; integration tests against HAPI, Firely, Spark (live, marked `@pytest.mark.integration`)

Depends on tasks 001–003.

## Acceptance criteria

- [ ] Returns correct `cache_status` for hit, miss, refreshed, and 304 scenarios; 304 responses refresh TTL without full re-fetch body when ETag unchanged.
- [ ] ETag and `If-None-Match` behavior verified against at least HAPI and Firely in integration tests.
- [ ] Authenticated `mockhealth` metadata fetch works with `MOCK_HEALTH_API_KEY`; credentials never appear in logs, exceptions, or audit output.
- [ ] Transient network failure returns last-known-good cache with `audit.source="cache"` and warning; empty cache on first failure raises structured error.
- [ ] ≥99% unit test coverage on CacheAgent logic; integration tests pass against ≥3 public test servers.

## Out of scope

- Persistent file-based or Redis cache backends.
- Lazy/partial parsing of very large CapabilityStatements (full document cached in v1).
- Publishing cache invalidation events to an event bus.

## Log
### [PA] 2026-07-03 — Grooming
Initial task from /squid-plan on specs/fhir-query-validator-factory.md.