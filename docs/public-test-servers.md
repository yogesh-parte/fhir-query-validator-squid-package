# Public and Authenticated FHIR Test Servers

This document lists FHIR servers supported by the query validator factory via `server_key`.

## Public servers (no API key)

| `server_key` | Name | Base URL | Auth |
|--------------|------|----------|------|
| `hapi` | HAPI FHIR | https://hapi.fhir.org/baseR4 | None |
| `firely` | Firely | https://server.fire.ly/R4 | None |
| `spark` | Spark | https://spark.fhir.org/r4 | None |
| `wildfhir` | WildFHIR | https://wildfhir4.wildfhir.org/r4 | None |

## Authenticated servers

### mock.health (`mockhealth`)

Synthetic FHIR R4 sandbox with US Core 6.1 resources. Useful for testing authenticated flows against realistic clinical data.

| Field | Value |
|-------|-------|
| `server_key` | `mockhealth` |
| Base URL | `https://api.mock.health/fhir` |
| Metadata | `https://api.mock.health/fhir/metadata` |
| Authentication | Bearer API key |
| Secret env var | `MOCK_HEALTH_API_KEY` |
| Documentation | https://mock.health/docs |

#### Setup (secure — no secrets in git)

1. Sign up at [mock.health](https://mock.health/docs) and copy your API key.
2. Copy the example env file:

   ```bash
   cp .env.example .env.local
   ```

3. Add your key to `.env.local` (this file is **git-ignored**):

   ```env
   MOCK_HEALTH_API_KEY=sk_live_your_key_here
   ```

4. Run with `server_key="mockhealth"`:

   ```python
   from src.agentic_layer.graph.validation_workflow import run_validation_workflow

   result = run_validation_workflow({
       "query_url": "Patient?name=Smith",
       "server_key": "mockhealth",
       "mode": "validate_and_execute",
   })
   ```

#### Security notes

- **Never** commit `.env.local`, `env.mockhealth`, or any file containing a live API key.
- Rotate the key at mock.health if it was ever exposed in version control or chat logs.
- In CI/CD, inject `MOCK_HEALTH_API_KEY` from your secret manager (GitHub Actions secrets, Google Secret Manager, etc.) — not from repo files.

## Adding more servers

Extend `BASE_SERVERS` in [`src/agentic_layer/config/settings.py`](../src/agentic_layer/config/settings.py) (exported as `DEFAULT_SERVERS` for backward compatibility). For authenticated servers, set `requires_auth: True` and `auth_token_env` to a dedicated environment variable name. The registry is immutable at runtime; a `protected` server is overlaid only when `FHIR_USE_AUTH=true` and `FHIR_SERVER_BASE` is set.