# Makefile — FHIR Query Validator Factory (Squid scaffold)

.PHONY: help install sync lint test security demo demo-loops demo-agent-trace demo-mockhealth spec-check clean

help:
	@echo "Available commands:"
	@echo "  make install           - Install runtime + dev deps via uv"
	@echo "  make sync              - Alias for install"
	@echo "  make lint              - Run ruff check + format check"
	@echo "  make test              - Run unit and integration tests"
	@echo "  make security          - Run Bandit SAST and pip-audit"
	@echo "  make spec-check        - Verify agent specs are present"
	@echo "  make demo-loops        - Feedback loops demo (not yet implemented)"
	@echo "  make demo-agent-trace  - Per-agent trace demo (not yet implemented)"
	@echo "  make demo-mockhealth   - mock.health demo (not yet implemented)"
	@echo "  make clean             - Remove generated files and caches"

install sync:
	uv sync --group dev

lint:
	uv run ruff check src fhir_validator_agent scripts tests

test:
	uv run pytest tests/unit -q --cov=src/agentic_layer --cov=fhir_validator_agent --cov-report=term-missing --cov-fail-under=99

security:
	uv run bandit -r src fhir_validator_agent scripts -ll
	uv run pip-audit .

spec-check:
	@echo "Checking agent specifications..."
	@test -f specs/fhir-query-validator-factory.md
	@test -f docs/spec/cache-agent-spec.md
	@test -f docs/spec/query-validation-spec.md
	@test -f docs/spec/query-execution-spec.md
	@test -f docs/spec/rule-and-learner-spec.md
	@test -f docs/spec/human-intervention-spec.md
	@echo "All required specs present."

demo: demo-loops

demo-loops:
	uv run python scripts/demo_loops.py

demo-agent-trace:
	uv run python scripts/demo_agent_traceability.py

demo-mockhealth:
	uv run python scripts/demo_loops_mockhealth.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache .ruff_cache .coverage htmlcov
	@echo "Cleaned up Python cache files."