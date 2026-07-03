# Phase 2: Architecture & Decision Making

**Phase Duration:** ~60-75 minutes  
**Focus:** High-level system design and key architectural decisions  
**Status:** Completed

## 1. Objectives of This Phase

- Translate the requirements from Phase 1 into a concrete system architecture.
- Define the roles and responsibilities of specialist agents.
- Design explicit feedback loops and human-in-the-loop mechanisms.
- Make foundational technology decisions (Google ADK + agents-cli).
- Create visual and documented architecture that can guide implementation.

## 2. Key Decisions Made

### 2.1 Technology Stack Decision
- **Primary Orchestration Framework**: Google Agent Development Kit (ADK) + `agents-cli`
- **Rationale**:
  - Strong support for graph-based workflows and multi-agent collaboration.
  - Built-in scaffolding, evaluation, and deployment capabilities via `agents-cli`.
  - Good alignment with enterprise needs while still allowing a lighter Gemini API path.
- **Dual-Path Strategy**:
  - Enterprise path: Full Google ADK + Cloud Run / Agent Engine deployment.
  - Lighter path: Direct Gemini API usage for faster experimentation or non-GCP environments.

### 2.2 Architectural Style
- **Specialist Agents over Monolithic Agents**
  - Each agent has a narrow, well-defined responsibility.
  - This improves maintainability, testability, and aligns with Software Factory principles.

- **Explicit Feedback Loops**
  - Cache invalidation loop
  - Validation → Execution loop
  - Pattern detection → Learning / Human escalation loop
  - Human review gates at critical points

- **Human-Centric Planning Layer**
  - All major architectural and planning decisions remain human-driven.
  - Agents are used primarily for execution and repetitive tasks.

## 3. High-Level Architecture

The system is divided into two main layers:

### Layer 1: Human-Centric Planning Layer (Upstream)
- Ideation, Requirements, Glossary, Phased Planning, ADRs
- Architecture validation and approval
- This layer is **not automated**

### Layer 2: Agentic Orchestration Layer (Google ADK Graph Workflow)
Specialist agents orchestrated as a graph with conditional routing.

**Core Specialist Agents:**

| Agent                          | Responsibility                                                                 | Triggered By                  |
|--------------------------------|--------------------------------------------------------------------------------|-------------------------------|
| **CacheAgent**                 | Fetch, cache, and invalidate CapabilityStatement (hybrid TTL + ETag)           | Start of request              |
| **CapabilityInterpreter Agent**| Dynamically interpret CapabilityStatement to support generalized validation    | After CacheAgent              |
| **QueryValidator Agent**       | Validate query + detect repeated invalid patterns from same user               | After Interpreter             |
| **QueryExecution Agent**       | Execute the FHIR search query if validation passes                             | Only if valid + mode = execute|
| **Rule Agent**                 | Evaluate patterns and decide escalation (Learner vs Human)                     | On pattern detection          |
| **Search Learner Agent**       | Explain errors and suggest improvements to the user                            | Triggered by Rule Agent       |
| **Human Intervention Gate**    | Pause automation and require human review when needed                          | Triggered by Rule Agent       |

## 4. Feedback Loops Designed

1. **Cache Invalidation Loop** — TTL + conditional requests (ETag / Last-Modified)
2. **Validation → Execution Loop** — Only execute after successful validation
3. **Pattern Detection → Learning Loop** — Repeated failures trigger learner or human
4. **Human Escalation Loop** — Critical or persistent issues require human decision

## 5. Multi-Server & Authentication Support

- Configuration-driven server selection via `server_key`
- Support for public test servers (HAPI, Firely, Spark, WildFHIR)
- Support for authenticated servers using Bearer tokens or OAuth2
- Configuration centralized in `docs/configuration.md` and `.env`

## 6. Artifacts Produced in This Phase

- `docs/architecture.md` (with Mermaid diagram)
- `docs/adr/001-adk-agents-cli-multi-agent-loop.md`
- Updated specifications in `docs/spec/` (including authentication support)
- Specialist agent responsibility matrix
- High-level graph workflow design (stub created in `src/agentic_layer/graph/validation_workflow.py`)

## 7. Alignment with Software Factory Principles

| Principle                    | How It Is Addressed in Architecture |
|-----------------------------|-------------------------------------|
| Planning as highest leverage | Human-centric planning layer is upstream and mandatory |
| Specialist agents           | Clear separation of responsibilities |
| Explicit feedback loops     | Multiple loops designed (cache, execution, learning, human) |
| Human oversight             | Human Intervention Gate at critical points |
| Modularity                  | Agent-based design + configuration-driven behavior |
| Traceability                | ADRs, specs, and planned logging/observability |

## 8. Open Questions / Risks Identified

- Token management and refresh strategy for OAuth2-protected servers
- Exact thresholds for pattern detection and escalation
- Performance targets for validation (especially with dynamic interpretation)
- Observability and tracing strategy across the graph workflow

## 9. Outcomes & Next Steps

**Outcomes:**
- Clear, documented architecture ready for implementation
- Technology decisions finalized
- Feedback loops and human gates explicitly designed

**Next Steps:**
- Move to **Phase 3**: Use `agents-cli` to scaffold and begin implementing core agents (CacheAgent, CapabilityInterpreter, basic QueryValidator).
- Flesh out detailed implementation plans in `planning/phase-3-scaffolding-core-agents.md`

---

**Phase 2 Completed Successfully**