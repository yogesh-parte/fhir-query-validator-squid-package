# Spec: QueryExecution Agent

**Status:** Ready for Implementation  
**Version:** 0.3  
**Last Updated:** 2026-07-02  
**Owner:** Yogesh  
**Related ADRs:** ADR-001  
**Related Specs:** `query-validation-spec.md`, `cache-agent-spec.md`

## 1. Overview

The **QueryExecution Agent** is responsible for safely executing validated FHIR search queries against the target server and returning structured results (or appropriate errors).

It only activates when `mode = validate_and_execute` **and** the `QueryValidator Agent` has confirmed the query is valid against the cached `CapabilityStatement`.

## 2. Goals

- Execute only pre-validated queries to minimize risk and wasted calls.
- Return clean, consistent result structures (Bundle or OperationOutcome).
- Handle common execution errors gracefully (network, auth, server errors, empty results).
- Maintain full traceability of the execution step.
- Support both public and authenticated servers.
- Provide timing and metadata useful for observability and learning.

## 3. Inputs

| Input          | Type   | Description                                      | Required |
|----------------|--------|--------------------------------------------------|----------|
| query_url      | string | Full validated FHIR search URL                   | Yes      |
| server_key     | string | Logical server identifier                        | Yes      |
| auth_token     | string | Bearer / API key (if required)                   | No       |
| user_id        | string | For audit / pattern tracking                     | No       |

## 4. Outputs

```json
{
  "executed": true,
  "server_used": "hapi",
  "query_url": "...",
  "status_code": 200,
  "result_type": "Bundle" | "OperationOutcome",
  "resource_count": 12,
  "results": { ... },           // FHIR Bundle or OperationOutcome
  "duration_ms": 187,
  "audit": {
    "executed_at": "2026-07-02T18:22:15Z",
    "cache_hit": true
  }
}
```

If execution fails:
```json
{
  "executed": false,
  "error_type": "network" | "auth" | "server_error" | "empty_result",
  "error_message": "...",
  "status_code": 500,
  ...
}
```

## 5. Core Behavior

1. Receive validated `query_url` + `server_key` from the workflow orchestrator.
2. Resolve authentication and base URL.
3. Perform HTTP GET on the `query_url` using `httpx`.
4. Parse response:
   - 200 + Bundle → return structured results + count.
   - OperationOutcome or error status → structured error.
5. Record execution metadata (duration, status, cache status from previous step).
6. Return output to the main workflow for final response assembly.

**Safety Rules**:
- Never execute a query that has not passed validation in the current request.
- Respect server rate limits if headers are present (future enhancement).
- Do not follow redirects by default (configurable).

## 6. Feedback Loops

- On execution error or empty result → feed back to `QueryValidator Agent` and `Rule Agent` for pattern detection.
- Success path contributes to positive reinforcement (future learning improvements).
- Execution metadata is included in the overall audit trail.

## 7. Edge Cases & Error Handling

- Network timeout / connection error → structured `network_error`.
- Authentication failure on execution (even if validation passed) → `auth_error`.
- Server returns 4xx/5xx → capture `OperationOutcome` if present.
- Very large result sets → return metadata + link (or truncated with warning).
- Empty search results → still considered successful execution (`resource_count: 0`).

## 8. Acceptance Criteria

- Only executes queries that have passed `QueryValidator` in the same flow.
- Correctly handles 200 Bundle responses and common error responses.
- Returns consistent output contract in both success and failure cases.
- All executions are fully traceable (included in audit trail).
- Works with public servers and `mock.health`.
- Unit tests cover success, network errors, auth errors, and empty results.
- Integration tests execute real queries against at least two public test servers.

## 9. Open Questions

- Should we support `_count` and paging parameters in v1 execution?
- Preferred strategy for very large result sets (streaming vs. full load)?
- Should execution results be cached (short TTL) for identical queries?

---
