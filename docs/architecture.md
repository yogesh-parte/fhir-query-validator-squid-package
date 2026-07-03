# Architecture

## High-Level Architecture

```mermaid
flowchart TD
    subgraph Human_Centric_Planning["Human-Centric Planning Layer<br/>(Highest Leverage - Ideation → Requirements → ADRs → Validation)"]
        A[Ideation + Requirements Definition] --> B[PRD + Glossary + Phased Roadmap]
        B --> C[Architecture Decision Records + Decision Validation]
        C --> D[Human Architecture Approval Gate]
    end

    subgraph Agentic_Orchestration["Agentic Orchestration Layer<br/>(Shared workflow engine + ADK graph wrapper)"]
        E[Workflow Engine / ADK Graph Entry]
        
        E --> F[CacheAgent]
        E --> G[CapabilityInterpreter Agent]
        E --> H[QueryValidator Agent]
        E --> I[QueryExecution Agent]
        E --> J[Rule Agent]
        E --> K[Search Learner Agent]
    end

    subgraph Feedback_Loops["Explicit Feedback & Improvement Loops"]
        F -.->|Cache miss / TTL expired / 304| F
        H -.->|Invalid query + pattern detected| J
        J -.->|Escalate to human| D
        J -.->|Activate learner| K
        K -.->|Suggestions + pattern logging| H
        I -.->|Execution errors / empty results| H
        E -.->|Human Review Gate| D
    end

    subgraph Dual_Paths["Dual Paths"]
        E --> L[Enterprise Path<br/>Google ADK + Cloud Run / Agent Engine<br/>Full governance + observability]
        E --> M[Lighter Path<br/>Direct Gemini API + minimal orchestration<br/>Fast local / non-GCP use]
    end

    subgraph Output["Generalized FHIR Query Assistant"]
        L --> N[Validate ANY query against CapabilityStatement<br/>+ Execute if valid<br/>+ Learn from repeated errors]
        M --> N
    end

    style Human_Centric_Planning fill:#e3f2fd,stroke:#1976d2
    style Agentic_Orchestration fill:#fff3e0,stroke:#f57c00
    style Feedback_Loops fill:#f3e5f5,stroke:#7b1fa2
    style Dual_Paths fill:#e8f5e9,stroke:#388e3c
    style Output fill:#e0f7fa,stroke:#00838f
```

## Specialist Agents

| Agent                        | Responsibility                                      | Trigger |
|-----------------------------|-----------------------------------------------------|---------|
| CacheAgent                  | CapabilityStatement caching + invalidation          | Always |
| CapabilityInterpreter Agent | Dynamic interpretation of CapabilityStatement       | After Cache |
| QueryValidator Agent        | Validation + pattern detection                      | Core |
| QueryExecution Agent        | Execute FHIR search if valid                        | After validation pass |
| Rule Agent                  | Detect repeat invalid patterns & decide escalation  | On pattern |
| Search Learner Agent        | Explain mistakes & suggest improvements             | Triggered by Rule Agent |
| Human Intervention Gate     | Human review when needed                            | Triggered by Rule Agent |

## Key Design Principles
- Planning is human-centric and upstream
- Specialist agents over monolithic agents
- Explicit feedback loops
- Human gates at critical points
- Dual enterprise / lighter paths
