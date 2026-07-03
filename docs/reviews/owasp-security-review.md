# OWASP Security Review

This file records **OWASP Top 10** and **Agentic Skills (AST)** security scans in **reverse chronological order** (newest entry first). Reviews use the `python-owasp-reviewer` skill workflow: architecture mapping, taint analysis, dependency audit, automated SAST, and severity-grouped findings.

Also see: [Traceability](../traceability.md) · [Configuration](../configuration.md) · [Spec compliance review](./spec-implementation-compliance-review.md)

---

## Pass 2 — 2026-06-30 post-hardening (`/python-owasp-reviewer`)

| Field | Value |
|-------|-------|
| **Review timestamp** | `2026-06-30T09:30:00+05:30` (IST) / `2026-06-30T04:00:00Z` (UTC) |
| **Reviewer** | Grok `/python-owasp-reviewer` (SAST + manual taint review) |
| **Baseline** | Pass 1 findings; remediation in commit `41280a7` |
| **Scope** | `src/agentic_layer/`, `scripts/`, `fhir_validator_agent/`, `pyproject.toml`, `.env.example`, `.github/workflows/security.yml`, `tests/unit/test_security_hardening.py` |
| **Out of scope** | `node_modules/`, `examples/notebooks/`, third-party site content |
| **Automated tools** | Bandit 1.9.4 (`src` + `scripts`, `-ll`); pattern grep; `pip-audit .` on pinned runtime deps |

### Executive summary

This is a **follow-up review after OWASP hardening** (commit `41280a7`). Pass 1 medium findings are **addressed with opt-in production controls** that preserve default demo behavior. `QueryExecutionAgent` now blocks absolute `query_url` values, enforces netloc matching, and disables redirect following. Human-gate operator auth, per-request workflow isolation, server-side `user_id` resolution, log redaction, pinned dependencies, CI security scanning, and an ADK Web threat model are all in place behind environment flags documented in `.env.example`.

With **production flags enabled** (`FHIR_WORKFLOW_ISOLATE_STATE`, `FHIR_TRUST_CLIENT_USER_ID=false`, `FHIR_HUMAN_GATE_REQUIRE_AUTH`, `FHIR_VERBOSE_LOGGING=false`), risk posture is **suitable for guarded networked deployment** behind an API gateway. With **default demo flags** (all security env vars unset/false), three Pass 1 medium-class behaviors remain **intentionally** for local demos and escalation loop tests.

Bandit: **0 High / 0 Medium** at `-ll`. `pip-audit .` on pinned direct runtime deps: **no known vulnerabilities**. Eleven security-hardening unit tests pass.

| Severity | Count | Notes |
|----------|-------|-------|
| High | 0 | — |
| Medium | 0 | When production env flags are set |
| Medium (residual, demo default) | 3 | Auth off, singletons, trusted `user_id` — by design |
| Low | 5 | Unchanged Bandit low findings |

---

### Pass 1 remediation status

| Pass 1 finding | Status | Implementation |
|----------------|--------|----------------|
| A10 SSRF / unvalidated outbound HTTP | **Resolved** | `utils/url_safety.py` + `follow_redirects=False` in `query_execution.py:53` |
| A01 Human gate review bypass | **Mitigated (opt-in)** | `auth/operator.py`; `FHIR_HUMAN_GATE_REQUIRE_AUTH` + `FHIR_HUMAN_GATE_OPERATOR_TOKEN` |
| A01/A04 Spoofable `user_id` | **Mitigated (opt-in)** | `auth/identity.py`; `FHIR_TRUST_CLIENT_USER_ID=false` derives `token:{sha256}` |
| A04 Shared singleton state | **Mitigated (opt-in)** | `WorkflowAgents` bundle; `FHIR_WORKFLOW_ISOLATE_STATE=true` |
| A06 Unpinned dependencies | **Resolved** | Exact pins in `pyproject.toml`; `.github/workflows/security.yml` |
| A02 Sensitive data in logs | **Mitigated (opt-in)** | `utils/logging_safe.py`; `FHIR_VERBOSE_LOGGING=false` |
| A02 Partial API key in demos | **Resolved** | `demo_loops_mockhealth.py` prints `(set)` only |
| A05 Env-driven cache invalidation | **Open (Low)** | Unchanged — acceptable for host-controlled deployment config |
| A07 Unbound runtime bearer token | **Open (Low)** | Unchanged — acceptable for CLI/ADK demos; gateway should bind in prod |
| A09 Audit context breadth | **Improved** | Human-gate audit redacted when verbose logging off |
| B603 Subprocess in ADK demos | **Open (Low)** | Fixed args; scenario allowlist pattern in `_demo_utils.py` |
| P3 ADK Web threat model | **Resolved** | Documented in `fhir_validator_agent/agent.py` |

---

### Findings summary (Pass 2)

| Severity | OWASP / AST | Title | Location | Notes |
|----------|-------------|-------|----------|-------|
| Medium (residual) | A01 | Human gate auth disabled by default | `auth/operator.py:16` | Set `FHIR_HUMAN_GATE_REQUIRE_AUTH=true` before ADK Web / networked exposure |
| Medium (residual) | A04 | Singleton workflow agents by default | `workflow_engine.py:70-79` | Set `FHIR_WORKFLOW_ISOLATE_STATE=true` for multi-tenant workers |
| Medium (residual) | A01 / A04 | Client `user_id` trusted by default | `auth/identity.py:17` | Set `FHIR_TRUST_CLIENT_USER_ID=false` in production |
| Low | A05 | Cache invalidation controlled by env vars only | `cache_agent.py:35-39` | Host-level control; no runtime admin API |
| Low | A07 | Runtime `auth_token` accepted without identity binding | `workflow_state.py:18`, `settings.py:135-136` | Map to authenticated principal at API gateway |
| Low | A09 | Full query text in audit when verbose logging on | `human_gate.py:87` | Default verbose=true for demos; disable in prod |
| Low | A10 | CacheAgent metadata fetch follows redirects | `cache_agent.py:110` | URL is server-registry controlled, not user `query_url` — lower risk |
| Low | B603 / AST03 | `subprocess` in ADK demo scripts | `scripts/demo_adk_cli.py`, `scripts/demo_adk_web.py` | Fixed command lists; no `shell=True` |
| Low | A06 | Optional dependency extras use open ranges | `pyproject.toml:17-28` | `adk-cli`, `observability` extras unpinned — audit separately if installed |

**None identified** at High severity.

---

### Detailed findings (residual / open)

#### [A01] — Human gate auth off in default configuration (Medium — residual)

- **Location:** `src/agentic_layer/auth/operator.py:14-32`
- **Flaw:** `verify_human_gate_operator()` is a no-op unless `FHIR_HUMAN_GATE_REQUIRE_AUTH=true`. Demos and tests call `submit_review_decision()` without `operator_token`.
- **Exploitation:** Only relevant when ADK Web or workflow APIs are network-exposed without the production flag set.
- **Remediation:** Already implemented — enable before deployment:

```bash
FHIR_HUMAN_GATE_REQUIRE_AUTH=true
FHIR_HUMAN_GATE_OPERATOR_TOKEN=<unguessable-secret>
```

Verified by `tests/unit/test_security_hardening.py` (`test_human_gate_auth_required_*`).

---

#### [A04] — Singleton agents in default configuration (Medium — residual)

- **Location:** `src/agentic_layer/graph/workflow_engine.py:68-79`
- **Flaw:** `get_workflow_agents(isolate=False)` shares pattern history, pause maps, and cache across requests unless isolation is enabled.
- **Exploitation:** Multi-tenant ADK Web worker without `FHIR_WORKFLOW_ISOLATE_STATE=true` leaks cross-user escalation state.
- **Remediation:** Already implemented:

```bash
FHIR_WORKFLOW_ISOLATE_STATE=true
# or per-request: { "isolate_state": true, ... }
```

Verified by `test_isolated_workflows_do_not_share_pattern_history`.

---

#### [A01 / A04] — Trusted client `user_id` in default configuration (Medium — residual)

- **Location:** `src/agentic_layer/auth/identity.py:14-36`
- **Flaw:** `FHIR_TRUST_CLIENT_USER_ID` defaults to `true`; callers can supply arbitrary `user_id` for pattern history and pause checks.
- **Remediation:** Already implemented for production:

```bash
FHIR_TRUST_CLIENT_USER_ID=false
```

Identity derived as `token:{sha256_prefix}` when `auth_token` present.

---

#### [A10] — CacheAgent redirect following (Low)

- **Location:** `src/agentic_layer/agents/cache_agent.py:110`
- **Flaw:** `httpx.Client` for `/metadata` does not set `follow_redirects=False`.
- **Assessment:** `base_url` comes from the server registry (`settings.py`), not user `query_url`. Risk is substantially lower than Pass 1 execution-path finding. Optional hardening: add `follow_redirects=False` for consistency.

---

### Agentic / AST supplemental notes (Pass 2)

| AST | Pass 1 | Pass 2 |
|-----|--------|--------|
| AST03 Over-privileged | Workflow forwards caller bearer tokens | Unchanged; gateway + `FHIR_TRUST_CLIENT_USER_ID=false` recommended |
| AST05 External instructions | `.env.local` loading | Unchanged; git-ignored |
| AST06 Weak isolation | Same-process singletons | **Improved** — `WorkflowAgents` + isolate flag |
| AST09 No governance | Audit log only | Unchanged; threat model now in `agent.py` |

---

### Positive observations (Pass 2)

- **SSRF class mitigated** — `build_fhir_target_url()` rejects `://`, validates netloc, execution uses `follow_redirects=False`.
- **Defense in depth via env flags** — production hardening documented in `.env.example` without breaking demos.
- **CI security pipeline** — `.github/workflows/security.yml` runs Bandit (`-ll`) and `pip-audit .`.
- **Pinned runtime deps** — `httpx==0.28.1`, `authlib==1.7.2`, `google-adk==2.3.0`, `pydantic==2.13.4`, `python-dotenv==1.2.2`.
- **Automated regression tests** — `tests/unit/test_security_hardening.py` (11 tests) covers URL rejection, operator auth, identity resolution, isolation.
- **No SQL / injection surface** — grep clean for `eval`, `exec`, `os.system`, `pickle`, `yaml.load`, `shell=True`.
- **Bandit** — 0 High / 0 Medium at `-ll`; 5 Low (subprocess demos + env var name heuristic).

---

### Dependency audit (`pip-audit`)

`pip-audit .` against pinned `pyproject.toml` runtime dependencies (isolated install): **No known vulnerabilities found**.

Optional extras (`adk-cli`, `observability`, `dev`) still use `>=` ranges — run `pip-audit` separately when those extras are installed in deployment images.

---

### Recommended next steps (Pass 2)

| Priority | Action |
|----------|--------|
| P1 | Enable production env flags in any networked ADK Web / API deployment (see `.env.example`) |
| P2 | Add `follow_redirects=False` to `CacheAgent._fetch_from_server` for consistency |
| P2 | Commit a `uv.lock` / `requirements.lock` for fully reproducible transitive resolution |
| P3 | Pin optional `adk-cli` and `observability` extras or document them as dev-only |
| P3 | Add integration test that runs `make security` in CI (workflow already added) |

---

### Retest criteria (Pass 2)

- [x] `query_url` with `://` rejected at execution boundary (`test_query_execution_rejects_absolute_query_url`)
- [x] `submit_review_decision` raises `HumanGateAuthError` without operator credentials when auth enabled
- [x] Isolated workflow runs do not share pattern history on same worker (`FHIR_WORKFLOW_ISOLATE_STATE=true`)
- [x] `bandit -r src scripts -ll` → 0 Medium+ ; `pip-audit .` clean on pinned runtime deps
- [x] No secret substrings in demo script output (`demo_loops_mockhealth.py` → `(set)`)

---

## Pass 1 — 2026-06-30 (`/python-owasp-reviewer`)

| Field | Value |
|-------|-------|
| **Review timestamp** | `2026-06-30T09:15:00+05:30` (IST) / `2026-06-30T03:45:00Z` (UTC) |
| **Reviewer** | Grok `/python-owasp-reviewer` (SAST + manual taint review) |
| **Scope** | `src/agentic_layer/`, `scripts/`, `fhir_validator_agent/`, `pyproject.toml`, `.env.example`, `.gitignore` |
| **Out of scope** | `node_modules/`, `examples/notebooks/` (not scanned line-by-line), third-party site content |
| **Automated tools** | Bandit 1.9.4 on `src` + `scripts`; pattern grep; `pip-audit` on local environment |

### Executive summary

The codebase is a **demonstration agentic FHIR validator**, not a traditional FastAPI/Django web app. There is **no SQL layer** and **no classic command-injection surface** in `src/`. Bandit reported **0 High / 0 Medium** issues in application code.

Primary risks are **productionization gaps**: user-controlled `query_url` drives outbound HTTP (SSRF/credential-relay class), **human-gate review APIs lack caller authentication**, and **module-level singletons** can leak cross-user state if the workflow is exposed as a multi-tenant service. Dependency pins are loose in `pyproject.toml`; the local dev environment has transitive CVEs unrelated to core runtime deps.

**Risk posture:** acceptable for **local demos**; **not production-ready** without hardening below.

| Severity | Count |
|----------|-------|
| High | 0 |
| Medium | 5 |
| Low | 5 |

---

### Findings summary

| Severity | OWASP / AST | Title | Location | Exploitation |
|----------|-------------|-------|----------|--------------|
| Medium | A10 | Outbound HTTP driven by user `query_url` with default redirect following | `src/agentic_layer/agents/query_execution.py:30-42` | Crafted query paths or server redirects could reach unintended paths; bearer token forwarded on outbound request |
| Medium | A01 | Human review resolution without reviewer authentication | `src/agentic_layer/agents/human_gate.py:101-133` | Anyone with `review_id` can call `submit_review_decision` and unpause users |
| Medium | A01 / A04 | Client-supplied `user_id` trusted for pause/escalation | `workflow_engine.py`, `query_validator.py` | Spoof `user_id` to pollute another user's pattern history or evade pause |
| Medium | A04 | Module singletons retain cross-request state | `src/agentic_layer/graph/workflow_engine.py:25-33` | Concurrent users share cache, pattern history, pause maps unless reset per request |
| Medium | A06 | Dependencies use open lower bounds | `pyproject.toml:8-14` | `httpx>=0.27` etc. allow silent breaking/vulnerable upgrades |
| Low | A02 | Query URLs and FHIR targets logged to stdout | `query_execution.py:32`, `query_validator.py:41` | Sensitive search parameters may appear in logs |
| Low | A02 | Demo scripts partially mask API keys | `scripts/demo_loops_mockhealth.py` | Prefix/suffix of `MOCK_HEALTH_API_KEY` printed to terminal |
| Low | A05 | Cache invalidation controlled by env vars only | `cache_agent.py:35-39` | Compromised host env can force metadata refetch storms |
| Low | A07 | Runtime `auth_token` accepted without binding to identity | `workflow_state.py:18`, `settings.py:135-136` | Caller can supply arbitrary bearer tokens for outbound FHIR calls |
| Low | A09 | Audit records may store full validation context | `human_gate.py:87`, `audit_log.py:37-60` | PHI/query text persisted when audit persistence enabled |
| Low | B603 / AST03 | `subprocess` in ADK demo scripts | `scripts/demo_adk_cli.py`, `scripts/demo_adk_web.py` | Low risk today (fixed args); review if CLI args become user-controlled |

---

### Detailed findings

#### [A10] — SSRF / unvalidated outbound HTTP (Medium)

- **Location:** `src/agentic_layer/agents/query_execution.py:30-42`
- **Flaw:** `target_url = f"{server.base_url}/{query_url.lstrip('/')}"` concatenates caller-controlled `query_url` into an `httpx.get()` without blocking absolute URLs, path normalization, or redirect policy. `httpx.Client` follows redirects by default.
- **Exploitation:** Attacker supplies `query_url` with path tricks (`../metadata`, unexpected resource paths) or relies on a malicious/compromised FHIR server redirect to exfiltrate the forwarded `Authorization` header. Validation reduces but does not eliminate path-level surprises (validation checks CapabilityStatement params, not full URL shape).
- **Remediation:**

```python
from urllib.parse import urljoin, urlparse

def _build_target_url(base_url: str, query_url: str) -> str:
    raw = query_url.strip()
    if "://" in raw:
        raise ValueError("Absolute query_url is not allowed")
    joined = urljoin(base_url.rstrip("/") + "/", raw.lstrip("/"))
    parsed = urlparse(joined)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Invalid URL scheme")
    # Optional: assert parsed.netloc matches base_url netloc
    return joined

with httpx.Client(timeout=30.0, follow_redirects=False) as client:
    response = client.get(target_url, headers=headers)
```

---

#### [A01] — Human gate review bypass (Medium)

- **Location:** `src/agentic_layer/agents/human_gate.py:101-133`
- **Flaw:** `submit_review_decision(review_id, reviewer=..., decision=...)` has no authentication or authorization on the caller. `reviewer` is an unverified string.
- **Exploitation:** In a networked deployment, anyone who obtains or guesses a `review_id` (printed in demo notifications) can resume a paused user or approve malicious activity.
- **Remediation:** Gate behind authenticated operator API; verify reviewer role from IdP; use unguessable review tokens; bind reviews to authenticated session.

```python
def submit_review_decision(
    self,
    review_id: str,
    *,
    operator: AuthenticatedOperator,  # from your IdP / API gateway
    decision: str,
    rationale: str,
) -> dict[str, Any]:
    if "human_reviewer" not in operator.roles:
        raise PermissionError("Insufficient privileges")
    ...
```

---

#### [A01 / A04] — Spoofable `user_id` (Medium)

- **Location:** `src/agentic_layer/state/workflow_state.py:17`; `query_validator.py:140-145`; `workflow_engine.py:70-71`
- **Flaw:** `user_id` is an optional client-supplied string used for pattern history, pause checks, and audit attribution without authentication.
- **Exploitation:** Attacker sets `user_id` to a victim identifier to trigger false escalations, pollute pattern stats, or probe pause state.
- **Remediation:** Derive `user_id` from verified JWT/session subject; reject client override unless admin impersonation is explicitly modeled.

---

#### [A04] — Shared singleton state (Medium)

- **Location:** `src/agentic_layer/graph/workflow_engine.py:25-33`
- **Flaw:** `cache_agent`, `validator`, `human_gate`, and `_audit_log` are process-wide singletons. `reset_singletons()` exists for tests/demos but is not invoked per workflow request in production paths.
- **Exploitation:** Multi-tenant HTTP/ADK deployment leaks pattern history, pause state, and cache entries across users on the same worker.
- **Remediation:** Instantiate agents per request or per tenant; or call `reset_singletons()` at request boundaries with tenant-scoped stores (Redis/DB).

---

#### [A06] — Unpinned dependencies (Medium)

- **Location:** `pyproject.toml:8-14`
- **Flaw:** Core deps use `>=` ranges without lockfile committed to repo.
- **Exploitation:** Supply-chain drift on reinstall; harder to reproduce patched builds.
- **Remediation:** Commit `uv.lock` / `requirements.lock`; pin exact versions in CI; run `pip-audit` in pipeline.

```toml
dependencies = [
    "httpx==0.28.1",
    "authlib==1.7.2",
    ...
]
```

---

#### [A02] — Sensitive data in logs (Low)

- **Location:** `query_execution.py:32`; `query_validator.py:41`
- **Flaw:** Full `query_url` and `target_url` printed to stdout (may contain PHI-bearing search parameters).
- **Remediation:** Structured logging with redaction; log resource type + param names only; disable verbose prints in production.

---

#### [A02] — Partial API key display in demos (Low)

- **Location:** `scripts/demo_loops_mockhealth.py` (masked key output)
- **Flaw:** Demo prints first/last characters of `MOCK_HEALTH_API_KEY`.
- **Remediation:** Print only `(set)` or hash fingerprint; never substring live secrets.

---

#### [A05] — Environment-driven cache invalidation (Low)

- **Location:** `src/agentic_layer/agents/cache_agent.py:35-39`
- **Flaw:** `FHIR_CACHE_INVALIDATE` / `FHIR_CACHE_INVALIDATE_KEYS` can flush cache without application-level auth.
- **Remediation:** Restrict to deployment config; require admin API for runtime invalidation.

---

#### [A07] — Unbound runtime bearer token (Low)

- **Location:** `settings.py:135-136`; workflow `auth_token` field
- **Flaw:** Any caller can pass `auth_token` in workflow state; engine forwards it to FHIR servers.
- **Remediation:** Acceptable for CLI demos; for APIs, map tokens to authenticated principal and disallow arbitrary override.

---

#### [A09] — Audit context breadth (Low)

- **Location:** `human_gate.py:87` (full `review_record` in audit context)
- **Flaw:** Audit entries may contain query URLs and validation payloads.
- **Remediation:** Persist redacted summaries; encrypt audit files at rest; retention policy.

---

#### [B603] — Subprocess in ADK demo scripts (Low)

- **Location:** `scripts/demo_adk_cli.py:63`; `scripts/demo_adk_web.py:87`
- **Flaw:** Bandit flags `subprocess` usage (no `shell=True` — good). Risk rises if arguments become user-controlled.
- **Remediation:** Keep fixed command lists; validate `scenario` keys against allowlist (already pattern in demo utils).

---

### Agentic / AST supplemental notes

| AST | Assessment |
|-----|------------|
| AST03 Over-privileged | Workflow can call arbitrary registered FHIR servers with env/caller-supplied bearer tokens |
| AST05 External instructions | Demo scripts load `.env.local`; docs reference external FHIR URLs (expected) |
| AST06 Weak isolation | ADK graph runs in same process as singleton agents — no sandbox |
| AST09 No governance | Audit log exists but no central skill/agent inventory for deployments |

Reference: [OWASP Agentic Skills Top 10](https://github.com/OWASP/www-project-agentic-skills-top-10)

---

### Positive observations

- **No SQL / ORM** — eliminates classic SQL injection surface in `src/`.
- **No `eval`, `exec`, `os.system`, `pickle`, or `yaml.load`** in application code (Bandit + grep clean).
- **Secrets management** — `.env.local`, `.env`, `env.mockhealth` are **git-ignored**; `.env.example` uses commented placeholders only.
- **Auth forwarding** — Bearer tokens applied consistently on cache + execution HTTP calls via `get_auth_headers()`.
- **Validation gate** — Invalid queries skip execution (`workflow_engine.py:144-152`).
- **Auth-scoped cache keys** — `auth_cache_suffix()` prevents cross-token cache bleed (`auth/provider.py:108-114`).
- **Bandit** — 0 High / 0 Medium in `src/` + `scripts/`; 5 Low (subprocess demos + env var name heuristic).

---

### Dependency audit (`pip-audit`)

Direct `pyproject.toml` dependencies are minimal (`httpx`, `authlib`, `google-adk`, `pydantic`, `python-dotenv`). A full-environment `pip-audit` reported **49 known vulnerabilities in 9 packages** — predominantly **transitive dev/Jupyter/langchain** packages in the local Python install, not declared direct runtime deps of this project.

**Recommendation:** Run `pip-audit` in CI against a **minimal prod extra** install only; avoid auditing the entire Jupyter stack as app risk.

---

### Recommended next steps (prioritized)

| Priority | Action |
|----------|--------|
| P1 | Add URL builder + `follow_redirects=False` (or strict allowlist) in `QueryExecutionAgent` |
| P1 | Authenticate `submit_review_decision` before any networked human-gate deployment |
| P2 | Replace singleton agents with per-request instances or mandatory tenant scoping |
| P2 | Derive `user_id` from verified identity; stop trusting client-supplied IDs in production |
| P2 | Pin dependencies; add `pip-audit` + Bandit to CI |
| P3 | Redact/remove stdout logging of full query URLs in production mode |
| P3 | Stop partial API key display in demo scripts |
| P3 | Document threat model for ADK Web exposure (`fhir_validator_agent/agent.py`) |

### Retest criteria

- [ ] `query_url` with `://` rejected at execution boundary
- [ ] `submit_review_decision` returns 401/403 without operator credentials (when API wrapper added)
- [ ] Two concurrent workflow runs with different `user_id` values do not share pattern history on same worker
- [ ] `bandit -r src -ll` → 0 Medium+ ; `pip-audit` clean on prod lockfile
- [ ] No secret substrings in demo script output

---

*Generated by `/python-owasp-reviewer`. Re-run after major workflow, auth, or deployment changes.*