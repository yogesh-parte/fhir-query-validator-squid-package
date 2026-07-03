# Configuration Guide

This document describes how to configure the FHIR Query Validator Factory for different environments and servers, including public test servers and authenticated/protected servers.

## 1. Overview

The system is designed to be **configuration-driven**. You can switch between different FHIR servers (public or protected) without changing code by using environment variables or configuration files.

Configuration is primarily handled through:
- `.env.local` (recommended for local development — **git-ignored**, holds API keys)
- `.env` (optional non-secret defaults — also git-ignored)
- Environment variables (recommended for deployment / CI secret managers)

At startup, `python-dotenv` loads `.env.local` then `.env` automatically (see `src/agentic_layer/config/settings.py`).

## 2. Environment Variables

| Variable                        | Description                                                                 | Example                              | Required |
|--------------------------------|-----------------------------------------------------------------------------|--------------------------------------|----------|
| `FHIR_DEFAULT_SERVER_KEY`      | Default server key to use when none is specified                            | `hapi`                               | Yes      |
| `FHIR_SERVER_BASE`             | Base URL of the FHIR server (can be overridden by `server_key`)             | `https://hapi.fhir.org/baseR4`       | Yes      |
| `FHIR_METADATA_URL`            | URL to fetch the CapabilityStatement (usually `{base}/metadata`)            | `https://hapi.fhir.org/baseR4/metadata` | No     |
| `FHIR_USE_AUTH`                | Whether to use authentication (`true` / `false`)                            | `false`                              | Yes      |
| `FHIR_AUTH_TYPE`               | Authentication type (`bearer` or `oauth2`)                                  | `bearer`                             | No       |
| `FHIR_AUTH_TOKEN`              | Static Bearer token (for simple cases)                                      | `eyJhbGciOi...`                      | No       |
| `OAUTH_CLIENT_ID`              | Client ID for OAuth2 client credentials flow                                | `my-client-id`                       | No       |
| `OAUTH_CLIENT_SECRET`          | Client secret for OAuth2                                                    | `my-secret`                          | No       |
| `OAUTH_TOKEN_URL`              | Token endpoint URL for OAuth2                                               | `https://auth.example.com/token`     | No       |
| `OAUTH_SCOPE`                  | OAuth2 scope (optional)                                                     | `fhir.read`                          | No       |
| `MOCK_HEALTH_API_KEY`          | Bearer API key for mock.health (`server_key: mockhealth`)                   | `sk_live_...`                        | No*      |

\* Required when using `server_key=mockhealth`. Store only in `.env.local` or a secret manager — never in git.

## 3. Supported Public Test Servers

The following servers are supported out of the box via `server_key`:

| server_key   | Server Name       | Base URL                                      | Auth Required | Notes |
|--------------|-------------------|-----------------------------------------------|---------------|-------|
| `hapi`       | HAPI FHIR         | https://hapi.fhir.org/baseR4                  | No            | Default |
| `firely`     | Firely            | https://server.fire.ly/R4                     | No            | - |
| `spark`      | Spark             | https://spark.fhir.org/r4                     | No            | - |
| `wildfhir`   | WildFHIR          | https://wildfhir4.wildfhir.org/r4             | No            | - |

### Authenticated sandbox servers

| server_key   | Server Name       | Base URL                         | Auth Required | Secret env var          | Notes |
|--------------|-------------------|----------------------------------|---------------|-------------------------|-------|
| `mockhealth` | mock.health       | https://api.mock.health/fhir     | Yes (Bearer)  | `MOCK_HEALTH_API_KEY`   | [Docs](https://mock.health/docs) |

You can add more servers by extending the configuration in `settings.py`.

## 3.1 mock.health API key setup

mock.health uses a **Bearer API key** for server-to-server access. Manage it securely:

```bash
# 1. Copy the example file (safe to commit)
cp .env.example .env.local

# 2. Edit .env.local — add your key from https://mock.health/docs
# MOCK_HEALTH_API_KEY=sk_live_your_key_here
```

**Do not:**
- Commit `.env.local` or paste keys into source code, notebooks, or specs
- Store keys in `env.mockhealth` or other tracked files

**Do:**
- Use `.env.local` locally (git-ignored via `.gitignore`)
- Use CI/CD secret stores in pipelines (e.g. `MOCK_HEALTH_API_KEY` as a GitHub Actions secret)
- Pass `auth_token` at runtime only for ephemeral tests (overrides env)

```python
result = run_validation_workflow({
    "query_url": "Patient?gender=male",
    "server_key": "mockhealth",
    "mode": "validate_and_execute",
})
```

If `MOCK_HEALTH_API_KEY` is missing, the workflow returns a clear authentication error without calling the server.

## 4. Authentication Workflow

### Public Servers (No Auth)
- Set `FHIR_USE_AUTH=false`
- No additional credentials needed

### Authenticated Servers

#### Option A: Static Bearer Token
```env
FHIR_USE_AUTH=true
FHIR_AUTH_TYPE=bearer
FHIR_AUTH_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Option B: OAuth2 Client Credentials Flow
```env
FHIR_USE_AUTH=true
FHIR_AUTH_TYPE=oauth2
OAUTH_CLIENT_ID=your-client-id
OAUTH_CLIENT_SECRET=your-client-secret
OAUTH_TOKEN_URL=https://auth.example.com/oauth2/token
OAUTH_SCOPE=fhir.read
```

The system will automatically obtain and refresh access tokens when needed.

## 5. Example `.env.local` File

```env
# Default server
FHIR_DEFAULT_SERVER_KEY=hapi
FHIR_SERVER_BASE=https://hapi.fhir.org/baseR4
FHIR_USE_AUTH=false

# mock.health authenticated sandbox (https://mock.health/docs)
# MOCK_HEALTH_API_KEY=sk_live_your_key_here

# Generic protected server (optional)
# FHIR_USE_AUTH=true
# FHIR_AUTH_TYPE=bearer
# FHIR_AUTH_TOKEN=your-bearer-token
```

## 6. Switching Servers at Runtime

You can override the default server by passing `server_key` in the request:

```python
result = validator.validate(
    query_url="Patient?gender=male",
    server_key="firely"
)
```

## 7. Security Considerations

- Never commit real credentials or tokens to version control.
- Use `.env.local` (git-ignored via `.gitignore`) for local API keys such as `MOCK_HEALTH_API_KEY`.
- Copy from `.env.example` only — the example file contains placeholders, not real secrets.
- For production and CI, inject secrets via environment variables or secret managers (GitHub Actions secrets, Google Secret Manager, AWS Secrets Manager, HashiCorp Vault).
- Rotate API keys immediately if they appear in git history, logs, or chat.
- When using OAuth2, prefer short-lived tokens and implement proper token refresh logic.

## 8. Related Files

- [`.env.example`](../.env.example) — safe template (committed)
- [`docs/public-test-servers.md`](public-test-servers.md) — server catalog including mock.health
- [`src/agentic_layer/config/settings.py`](../src/agentic_layer/config/settings.py) — server registry

Refer to the original `yogesh-parte/fhirqueryvalidator` repository for the baseline implementation patterns.
