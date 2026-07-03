# Spec: CacheAgent

**Status:** Ready for Implementation  
**Version:** 0.4  
**Last Updated:** 2026-07-02  
**Owner:** Yogesh  
**Related ADRs:** ADR-001 (CapabilityStatement handling strategy)  
**Related Specs:** `query-validation-spec.md`, `query-execution-spec.md`

## 1. Overview

The **CacheAgent** is responsible for fetching, caching, and intelligently invalidating FHIR server `CapabilityStatement` documents. It acts as the always-on entry point for metadata freshness and is the foundation for all subsequent query validation and execution.

It must support ETag/304 Not Modified responses, TTL-based expiration, and per-server authentication while producing a clean, auditable output that downstream agents can trust.

## 2. Goals

- Eliminate redundant `CapabilityStatement` fetches on every request.
- Respect HTTP caching semantics (ETag, Last-Modified, 304 responses).
- Provide fast, consistent access to parsed `CapabilityStatement` data for validation logic.
- Support both public and authenticated servers (including mock.health).
- Maintain full traceability of cache hits, misses, and invalidations.
- Enable graceful degradation when a server’s metadata is temporarily unavailable.

## 3. Inputs

| Input          | Type   | Description                                      | Required |
|----------------|--------|--------------------------------------------------|----------|
| server_key     | string | Logical server identifier (e.g. `hapi`, `mockhealth`) | Yes      |
| auth_token     | string | Bearer token or API key (if required)            | No       |
| force_refresh  | bool   | Bypass cache and force fresh fetch               | No       |

## 4. Outputs

```json
{
  "server_key": "hapi",
  "capability_statement": { ... },   // parsed JSON
  "fetched_at": "2026-07-02T18:15:00Z",
  "cache_status": "hit" | "miss" | "refreshed" | "304",
  "etag": "W/\"abc123\"",
  "ttl_expires_at": "2026-07-02T20:15:00Z",
  "audit": {
    "source": "live" | "cache",
    "http_status": 200 | 304,
    "duration_ms": 124
  }
}
```

## 5. Core Behavior

1. Resolve `server_key` to base URL and authentication method (via central configuration).
2. Check local cache (in-memory + optional persistent layer).
3. If `force_refresh` or cache miss/expired:
   - Perform HTTP GET to `{base_url}/metadata` with `If-None-Match` header when ETag exists.
   - Handle 304 responses by refreshing TTL only.
   - Store new document + ETag + timestamp.
4. Parse and validate the `CapabilityStatement` structure.
5. Return the structured output with clear `cache_status`.
6. Log all operations with correlation ID for traceability.

**Caching Strategy**:
- Default TTL: 15 minutes (configurable per server).
- Invalidate on 304 or explicit `force_refresh`.
- Support for `Cache-Control` headers from the server when present.
- Thread-safe / async-safe implementation.

## 6. Feedback Loops

- Triggered on every validation request (always-on agent).
- On cache miss or TTL expiry → automatic refresh loop.
- On 304 response → lightweight TTL refresh loop (no full re-parse).
- Exposes cache metrics for potential future monitoring agent.

## 7. Edge Cases & Error Handling

- Server returns 401/403 on metadata endpoint → surface clear auth error.
- Invalid or non-FHIR `CapabilityStatement` → raise structured validation error.
- Network timeout or transient failure → return last known good cached version (with warning) + schedule retry.
- ETag changes frequently → avoid cache thrashing.

## 8. Acceptance Criteria

- Returns correct `cache_status` values in all scenarios (hit / miss / refreshed / 304).
- Correctly handles ETag and 304 responses (verified against HAPI and Firely).
- Supports authenticated servers (mock.health) without leaking credentials.
- Produces consistent, parseable output even on cache hits.
- All cache operations are traceable via the `audit` block.
- Graceful fallback to last-known-good on transient server errors.
- Unit tests achieve ≥99% coverage on CacheAgent logic.
- Integration tests run successfully against at least 3 public test servers.

## 9. Open Questions

- Should we add a persistent cache backend (Redis / file-based) in v1 or keep in-memory only?
- Preferred strategy for very large `CapabilityStatement` documents (lazy parsing of search parameters only)?
- Should cache invalidation events be published to a central event bus for other agents?

---
