# Glossary

This glossary defines key terms used across the project documentation, specifications, and code.

## General Terms

| Term                    | Definition |
|-------------------------|----------|
| **Software Factory**    | A structured, repeatable approach to software development that emphasizes planning, specialist agents/teams, explicit feedback loops, modularity, and human oversight — inspired by manufacturing production lines. |
| **Spec-Driven Development** | An approach where detailed specifications (behavior, inputs, outputs, acceptance criteria) are created before implementation to guide development and reduce ambiguity. |
| **Loop Engineering**    | The deliberate design of feedback loops (validation, execution, learning, cache invalidation) to enable self-correction and continuous improvement. |
| **Human-in-the-Loop (HITL)** | Explicit points in an automated system where a human must review, approve, or intervene before proceeding. |

## FHIR & Healthcare Terms

| Term                          | Definition |
|-------------------------------|----------|
| **CapabilityStatement**       | A FHIR resource that describes the capabilities of a FHIR server, including supported resources, search parameters, modifiers, and operations. |
| **Search Parameter**          | A parameter used in FHIR search queries (e.g., `gender`, `birthdate`, `_lastUpdated`). |
| **Modifier**                  | A suffix added to a search parameter (e.g., `:exact`, `:missing`) that changes its behavior. |
| **Comparator**                | Operators used with search parameters (e.g., `gt`, `lt`, `ge`). |

## Agentic & AI Terms

| Term                          | Definition |
|-------------------------------|----------|
| **Specialist Agent**          | An agent designed with a narrow, well-defined responsibility (e.g., CacheAgent, QueryValidator Agent). |
| **Graph Workflow**            | A structured way of orchestrating agents using nodes and edges (supported in Google ADK 2.0 and LangGraph). |
| **Feedback Loop**             | A mechanism where the output of one step influences future behavior (e.g., cache invalidation, pattern-based learning). |
| **Rule Agent**                | An agent responsible for evaluating policies and deciding on escalation paths. |
| **Search Learner Agent**      | An agent that helps users understand errors and suggests improvements based on repeated mistakes. |
| **Meta-Feedback Loop**        | A higher-level loop that improves the system itself based on patterns of failure or success. |

## Technology Stack Terms

| Term                        | Definition |
|-----------------------------|----------|
| **Google ADK**              | Google Agent Development Kit — an open-source framework for building, testing, and deploying AI agents at scale. |
| **agents-cli**              | Official CLI tool for Google ADK that supports scaffolding, evaluation, deployment, and infrastructure setup. |
| **Gemini API**              | Google's LLM inference API (used directly or through ADK). |
| **CacheAgent**              | Specialist agent responsible for fetching, caching, and invalidating `CapabilityStatement` resources. |
| **QueryValidator Agent**    | Specialist agent that validates FHIR search queries against a CapabilityStatement. |
| **QueryExecution Agent**    | Specialist agent that executes valid FHIR search queries against the target server. |

## Project-Specific Terms

| Term                              | Definition |
|-----------------------------------|----------|
| **Generalized Validation**        | Ability to validate any query parameter declared in a CapabilityStatement, rather than only pre-defined ones. |
| **Pattern Detection**             | Logic that identifies repeated invalid queries from the same user. |
| **Human Intervention Gate**       | A controlled point where human review is required before continuing automated processing. |
| **Bilan**                         | A transparent accounting of time and effort invested in planning vs. implementation. |
| **server_key**                    | Logical identifier for a configured FHIR server (e.g. `hapi`, `firely`, `mockhealth`) used to resolve base URL and auth settings. |
| **validate_only**                 | Workflow mode that validates a query against CapabilityStatement without executing it against the FHIR server. |
| **validate_and_execute**          | Workflow mode that validates a query and, if valid, executes it via QueryExecution Agent. |
| **learner escalation**            | Escalation tier triggered when a user accumulates repeated validation failures (default: 3+ in 10 minutes), activating Search Learner Agent. |
| **audit trail**                   | Per-agent chronological record of decisions, inputs, outputs, and timings; exportable as a JSON trace bundle. |
| **cache_status**                  | CacheAgent output indicator: `hit`, `miss`, `refreshed`, or `304` describing how CapabilityStatement metadata was obtained. |
