# Integration Tests

## Mock workflow tests

`test_full_workflow.py` exercises the full validation pipeline with mocked HTTP.
These run in CI as part of `make test` (offline gate).

## Live network tests

Files `test_*_live.py` hit real public FHIR servers (HAPI, Firely, Spark) and
optionally mock.health. They are marked `@pytest.mark.integration` and skip
gracefully when a server is unreachable.

```bash
# Live tests only (requires network)
make test-integration

# mock.health tests (requires MOCK_HEALTH_API_KEY in .env.local)
uv run pytest tests/integration -m mockhealth -q
```

Live integration runs in a separate CI job (`integration-live`) with
`continue-on-error: true` because public servers can be flaky.