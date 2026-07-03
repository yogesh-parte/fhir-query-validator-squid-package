# Phase 3: Scaffolding + Core Agents

**Phase Duration (Estimated):** 3–4 hours  
**Focus:** Project bootstrapping and implementation of foundational agents  
**Status:** Complete

## 1. Objectives

- Bootstrap the Google ADK project using `agents-cli`
- Implement the core specialist agents required for basic generalized validation flow
- Establish configuration management and multi-server support
- Create the initial ADK graph workflow connecting the core agents
- Set up basic testing and observability foundations

## 2. Scope of This Phase

**In Scope:**
- Project scaffolding with `agents-cli`
- `CacheAgent` implementation (hybrid invalidation)
- `CapabilityInterpreter Agent` (dynamic interpretation of CapabilityStatement)
- Basic `QueryValidator Agent` (generalized validation without full pattern detection)
- Initial graph workflow wiring
- Configuration loader supporting `.env` and public test servers
- Basic logging and tracing setup

**Out of Scope (moved to Phase 4):**
- QueryExecution Agent
- Pattern detection logic
- Rule Agent + Search Learner Agent
- Human Intervention Gate
- Full feedback loops

## 3. Planned Activities

### 3.1 Project Scaffolding
- Use `agents-cli` to initialize the ADK project structure
- Organize code under `src/agentic_layer/`
- Set up basic project structure aligned with `docs/architecture.md`

### 3.2 Implement Core Agents

#### CacheAgent
- Implement hybrid invalidation strategy (TTL + ETag/Last-Modified)
- Support both public and authenticated servers
- Add proper caching backend (in-memory for now, with hooks for Redis later)
- Add logging for cache hits, misses, and refreshes

#### CapabilityInterpreter Agent
- Parse and interpret CapabilityStatement dynamically
- Extract supported resources, search parameters, modifiers, and comparators
- Return structured data that can be used by QueryValidator

#### QueryValidator Agent (Basic Version)
- Validate query against interpreted CapabilityStatement
- Support `server_key` based server selection
- Return structured validation result (`valid`, `errors`, `warnings`)
- Prepare hooks for future pattern detection

### 3.3 Graph Workflow Setup
- Create initial ADK graph workflow in `src/agentic_layer/graph/validation_workflow.py`
- Wire the three core agents: Cache → Interpreter → Validator
- Add basic conditional routing

### 3.4 Configuration & Multi-Server Support
- Implement configuration loader based on `docs/configuration.md`
- Support switching between public test servers via `server_key`
- Handle optional authentication headers

### 3.5 Testing & Observability Foundations
- Set up basic unit test structure
- Add structured logging for agent decisions
- Create simple demo script to test the core flow

## 4. Key Deliverables

| Deliverable                              | Location                                      | Priority |
|------------------------------------------|-----------------------------------------------|----------|
| ADK project scaffold                     | `src/agentic_layer/`                          | High     |
| `CacheAgent` implementation              | `src/agentic_layer/agents/cache_agent.py`     | High     |
| `CapabilityInterpreter Agent`            | `src/agentic_layer/agents/capability_interpreter.py` | High |
| Basic `QueryValidator Agent`             | `src/agentic_layer/agents/query_validator.py` | High     |
| Initial graph workflow                   | `src/agentic_layer/graph/validation_workflow.py` | High  |
| Configuration loader                     | `src/agentic_layer/config/`                   | Medium   |
| Basic demo script                        | `scripts/run_demo.py`                         | Medium   |
| Updated Phase 3 planning notes           | This file                                     | Low      |

## 5. Dependencies

- Completed Phase 2 artefacts (`docs/architecture.md`, specs, ADR)
- `docs/spec/cache-agent-spec.md`
- `docs/spec/query-validation-spec.md` (basic version)
- `docs/configuration.md`
- Google ADK + `agents-cli` installed

## 6. Risks & Mitigations

| Risk                                      | Mitigation |
|-------------------------------------------|----------|
| ADK graph workflow learning curve         | Start simple, use existing stub as reference |
| Dynamic CapabilityStatement interpretation is complex | Begin with core fields first, iterate later |
| Authentication handling adds complexity   | Defer full OAuth2 to Phase 4; support Bearer token first |
| Keeping implementation aligned with specs | Use specs as acceptance criteria during code review |

## 7. Success Criteria

- [ ] Project successfully scaffolded with `agents-cli`
- [ ] `CacheAgent` can fetch and cache CapabilityStatement from public servers
- [ ] `CapabilityInterpreter Agent` can extract key information from CapabilityStatement
- [ ] Basic `QueryValidator Agent` can validate simple queries against interpreted data
- [ ] End-to-end flow works for at least one public test server (e.g., HAPI)
- [ ] Configuration supports switching between servers via `server_key`

## 8. Alignment with Software Factory

- Strong focus on **modularity** through specialist agents
- **Spec-driven implementation** — every agent should be implemented against its specification
- Preparation for explicit **feedback loops** in Phase 4
- Maintains separation between planning (human) and execution (agents)

## 9. Next Phase Preview

After successful completion of Phase 3, move to **Phase 4: Loop Engineering & Advanced Agents**, where we will add:
- QueryExecution Agent
- Pattern detection logic
- Rule Agent + Search Learner Agent
- Human Intervention Gate
- Full feedback loop wiring

---

**Phase 3 Planning Complete**  
Ready to begin implementation once Phase 2 artefacts are reviewed and approved.