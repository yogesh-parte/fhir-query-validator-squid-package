# Spec: Generalized Query Validation

**Status:** Draft  
**Version:** 0.3  
**Last Updated:** 2026-06-30  
**Owner:** [Your Name]  
**Related ADRs:** ADR-001  

## 1. Overview

This specification defines the expected behavior of the **generalized FHIR Query Validation** capability.

The system should dynamically validate **any** search query against a FHIR server’s `CapabilityStatement` , support multiple public test servers, and handle both public and authenticated servers.

## 2. Goals

* Validate any resource type, search parameter, modifier, and comparator declared in the server’s CapabilityStatement .
* Support multiple public test servers out of the box (HAPI, Firely, Spark, WildFHIR, etc.).
* Support authenticated servers via configuration (OAuth / Bearer token / per-server API keys).
* Support [mock.health](https://mock.health/docs) as a first-class authenticated FHIR sandbox ( server_key: mockhealth ).
* Provide clear, actionable error messages.
* Detect repeated invalid query patterns from the same user.
* Support both validate_only and validate_and_execute modes.

## 3. Inputs

| Input | Type | Description | Required |
| --- | --- | --- | --- |
| query_url | string | Full FHIR search query URL | Yes |
| server_key | string | Logical key for the target server (e.g., hapi , firely , mockhealth ) | Yes |
| user_id (optional) | string | Identifier for pattern tracking and personalization | No |
| mode | enum | validate_only or validate_and_execute | Yes |
| auth_token (optional) | string | Bearer token or OAuth token for authenticated servers | No |

## 4. Supported Servers (Default)

### Public test servers (no authentication)

* **HAPI FHIR** ( hapi ) — https://hapi.fhir.org/baseR4
* **Firely** ( firely ) — https://server.fire.ly/R4
* **Spark** ( spark ) — https://spark.fhir.org/r4
* **WildFHIR** ( wildfhir ) — https://wildfhir4.wildfhir.org/r4

### Authenticated sandbox servers

* **mock.health** ( mockhealth ) — https://api.mock.health/fhir
* **Auth:** Bearer API key (server-to-server)
* **Secret env var:** MOCK_HEALTH_API_KEY (loaded from .env.local , never committed to git)
* **Docs:** [https://mock.health/docs](https://mock.health/docs)
* **CapabilityStatement:** {base_url}/metadata
* **Notes:** Synthetic US Core 6.1 population; supports FHIR R4 search, read, and write (plan-dependent)

Configuration is driven by environment variables loaded from `.env.local` (see `docs/configuration.md` ).

## 5. Authentication & Configuration

* Public servers: No authentication required.
* Protected servers: Support for Bearer token or OAuth2 client credentials flow.
* Per-server API keys: Dedicated environment variables (e.g. MOCK_HEALTH_API_KEY for mockhealth ).
* Configuration is loaded from .env.local / .env via python-dotenv at startup ( src/agentic_layer/config/settings.py ).
* The system should allow switching between servers using a server_key .
* **Secrets must never be committed to version control.** Use .env.local (git-ignored) or a secret manager in deployment.

See related documentation:

* [docs/configuration.md](/yogesh-parte/fhir-query-validator-factory/blob/main/docs/configuration.md)
* [docs/public-test-servers.md](/yogesh-parte/fhir-query-validator-factory/blob/main/docs/public-test-servers.md)

## 6. Outputs

```
{
  "valid": true,
  "server_used": "hapi",
  "errors": [],
  "warnings": [],
  "executed": false,
  "results": null
}
```

## 7. Core Behavior

1) Resolve server_key to actual base URL and auth settings.
2) Fetch (or retrieve from cache) the server’s CapabilityStatement (respecting auth if needed).
3) Dynamically interpret supported resources, search parameters, modifiers, and comparators.
4) Validate the query.
5) If valid and mode = validate_and_execute → execute via QueryExecution Agent.
6) Handle pattern detection and escalation via Rule Agent.

## 8. Edge Cases & Error Handling

* Unknown server_key
* Missing or invalid authentication for protected servers
* CapabilityStatement not accessible due to auth issues
* Repeated invalid queries from the same user

## 9. Acceptance Criteria

* Supports switching between multiple public test servers via configuration
* Can authenticate against protected servers using Bearer token or OAuth
* Supports mock.health ( mockhealth ) with API key from MOCK_HEALTH_API_KEY in .env.local
* Validates any parameter declared in the CapabilityStatement
* Pattern detection and escalation work across different servers
* Clear error messages when authentication fails

## 10. Open Questions

* Preferred OAuth flow for protected servers?
* Should we support multiple auth methods per server?
* mock.health also supports SMART on FHIR OAuth2 + PKCE — should we add a dedicated flow beyond Bearer API keys?
