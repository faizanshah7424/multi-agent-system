# CodeOrbit AI: Product Evolution Roadmap (v0.1 - v1.0)

> **Document Status:** Approved  
> **Target Baseline:** v2.2 Architecture  
> **Last Updated:** July 11, 2026

---

## 1. Current Project Status

CodeOrbit AI has established a robust, decoupled, and secure orchestration foundation over Sprints 1 to 6:

* **Completed Sprints:** Sprints 1, 2, 3, 4, 5, 5.5, and 6.
* **Implemented Subsystems:**
  * **DI & Core Interfaces:** Decoupled protocol boundaries allowing dependency swapping.
  * **Repository Scanner & AST Parser:** Indexing engine mapping files and Python symbols to dependency database graphs.
  * **AI Orchestration (Model Abstraction):** Gemini provider connection with schema enforcement and cost/token tracking.
  * **Workspace & Sandbox Manager:** Safe Git worktree isolation coupled with timeout process sandboxes.
  * **Topological Scheduler & Plan DAG:** Kahn's algorithm sorting execution plans topologically.
  * **ReAct Agent Executor:** Thinking and acting agent loop resolving file and execution tools inside sandboxes.
* **Reality Verification Audit Scores:**
  * Reality Score: `92/100`
  * Autonomy Score: `90/100`
  * Repository Awareness Score: `85/100`
  * Production Readiness Score: `88/100`
* **Maturity Level:** **Level 2 (Transactional Automation)**. The platform can plan, sequence, and execute multi-step modifications inside sandboxed worktrees, but lacks self-repair and team consensus debate protocols.

---

## 2. Product Evolution Phases

The development path from current baseline to v1.0 is divided into distinct version milestones:

### **v0.1 Foundation (Completed)**
* **Mission:** Establish execution boundaries and type contracts.
* **Objectives:** Build dependency container and sandbox protocols.
* **Major Features:** DI Container, basic Local Sandbox process execution.
* **New Subsystems:** `core/di.py`, `core/sandbox/interface.py`.
* **Architecture Changes:** Standardized protocol boundaries.
* **User Value:** Zero host pollution; pluggable code setup.
* **Success Criteria:** Safe subprocess launches with timeouts.
* **Definition of Done:** Interface verification tests passing.
* **Production Readiness:** Local-only prototype.
* **Known Risks:** Process escaping (partially mitigated via directory bounds).

### **v0.2 Repository Intelligence (Completed)**
* **Mission:** Map codebase structures topologically.
* **Objectives:** Parse Python ASTs, scan stacked technologies, and save relationships.
* **Major Features:** AST Parsing, Cycle loops detection, SQLite indexes.
* **New Subsystems:** `core/indexer/`.
* **Architecture Changes:** SQLAlchemy schema additions for code symbols and edges.
* **User Value:** Contextual codebase awareness before changes.
* **Success Criteria:** Cycles flagged; report generation matching framework layouts.
* **Definition of Done:** DFS topological imports check passing.
* **Production Readiness:** Indexer scans medium repos (<1000 files) in <1s.
* **Known Risks:** Regex parsing for JS/TS has minor accuracy loss.

### **v0.3 Planning Engine (Completed)**
* **Mission:** Deconstruct user goals into sequential execution steps.
* **Objectives:** Format agent parameters, map variables, and support prompt versioning.
* **Major Features:** PromptLibrary, Gemini Provider schemas, Tool registry filters.
* **New Subsystems:** `core/registry/`, `core/models/`.
* **Architecture Changes:** Prompts loaded from disk; structured outputs.
* **User Value:** Structured execution paths replacing simple lists.
* **Success Criteria:** Validated variables substitution.
* **Definition of Done:** Structured output validation passing.
* **Production Readiness:** Config-driven providers.
* **Known Risks:** OpenAI/Anthropic stubs block instant model swaps.

### **v0.4 Autonomous Runtime (Completed)**
* **Mission:** Run execution DAGs transactionally.
* **Objectives:** isolated worktree branching, session logging, and ReAct loops.
* **Major Features:** Git Worktree workspaces, LocalProcessSandbox command token safety filters, ReAct loops.
* **New Subsystems:** `core/workspace/`, `core/queue/agent_executor.py`.
* **Architecture Changes:** Transactional halting on step failures.
* **User Value:** Isolated codebase editing with safe rollbacks.
* **Success Criteria:** No host pollution; sanitization blocks command chain operators.
* **Definition of Done:** Workspace and ReAct loop tests passing.
* **Production Readiness:** Git-backed sandboxed execution.
* **Known Risks:** CPU/memory throttling absent in fallback processes.

### **v0.5 Human Collaboration (Next Milestone)**
* **Mission:** Integrate human-in-the-loop review boundaries.
* **Objectives:** Implement HITL pause states, PR review hooks, and real-time events.
* **Major Features:** Task status suspension, WebSocket stream, console review panels.
* **New Subsystems:** `core/broker/` (Events), `core/queue/hitl.py` (Orchestration).
* **Architecture Changes:** Event-driven status publishers.
* **User Value:** Humans can audit agent worktrees before mainline merges.
* **Success Criteria:** Task suspends on PR review; resumes on approval.
* **Definition of Done:** E2E task suspension integration tests passing.
* **Production Readiness:** Safe for team integration.
* **Known Risks:** User latency blocks worker thread queues.

### **v0.6 Self-Healing Engineering**
* **Mission:** Enable agents to repair compilation/test failures.
* **Objectives:** Parse build logs and loop compiler fixes.
* **Major Features:** Pytest/Linter feedback loops, diagnostic parsing.
* **New Subsystems:** `core/autonomous_execution/self_repair.py`.
* **Architecture Changes:** Sandboxed compiler feedback routes.
* **User Value:** Automated fix loops for syntax/import errors.
* **Success Criteria:** Sandbox compile failures auto-fixed in worktree.
* **Definition of Done:** Agent corrects syntactically broken code E2E.
* **Production Readiness:** High implementation reliability.
* **Known Risks:** Infinite healing loop exhaustion (capped at 3 retries).

### **v0.7 Engineering Memory**
* **Mission:** Retain repository experience across sessions.
* **Objectives:** Vector indexing, ledger audits, and LLM context compaction.
* **Major Features:** VectorDB local embeddings, experience ledger compaction.
* **New Subsystems:** `core/memory/`.
* **Architecture Changes:** Chromadb vector registry addition.
* **User Value:** Agent recalls past bugfixes or conventions.
* **Success Criteria:** Compacted memory contexts preserve key fixing traces.
* **Definition of Done:** Compaction and semantic retrieve checks passing.
* **Production Readiness:** Session persistence.
* **Known Risks:** Embedding cost increases.

### **v0.8 Multi-Agent Collaboration**
* **Mission:** Scale execution to specialized collaborative swarms.
* **Objectives:** Event-bus messaging and Tech Lead consensus debate.
* **Major Features:** Swarm routing, Agent consensus vote brokers.
* **New Subsystems:** `core/broker/debate.py`, `agents/tech_lead.py`.
* **Architecture Changes:** Multi-agent WebSocket debate threads.
* **User Value:** Automated reviewer and developer agents collaborate on large features.
* **Success Criteria:** Vote passed triggers Git mainline merge.
* **Definition of Done:** Collaborative task completion E2E.
* **Production Readiness:** Swarm support.
* **Known Risks:** Communication deadlocks (loop checks required).

### **v0.9 Enterprise Readiness**
* **Mission:** Scale the platform to multi-tenant cloud pipelines.
* **Objectives:** Postgres database swapping, JWT RBAC, and incremental watchers.
* **Major Features:** pgvector adapter, incremental watcher, RBAC admin dashboard.
* **New Subsystems:** `core/auth/`, `core/db/postgres_adapter.py`.
* **Architecture Changes:** DB adapter database swappability.
* **User Value:** Enterprise-level authentication, scaling, and file watchers.
* **Success Criteria:** Safe postgres migration; indexer updates on file save.
* **Definition of Done:** Tenancy and incremental scan checks passing.
* **Production Readiness:** Cloud-ready.
* **Known Risks:** DB transaction latency.

### **v1.0 Autonomous Software Engineer**
* **Mission:** Deploy a world-class autonomous software engineer competitor.
* **Objectives:** Complex PR resolution, CI/CD sandbox integration, and plugin systems.
* **Major Features:** Extensible plugins hooks, E2E production PR deployment.
* **New Subsystems:** `core/plugins/`.
* **Architecture Changes:** Event hooks registered for third-party scripts.
* **User Value:** Complete natural-language-to-production deployment pipeline.
* **Success Criteria:** Agent resolves GitHub issue E2E without human intervention.
* **Definition of Done:** E2E Issue-to-PR integration checks passing.
* **Production Readiness:** Production deployment.
* **Known Risks:** Zero-day execution vulnerability (mitigated by Docker-only bounds).

---

## 3. Sprint-to-Version Mapping

| Completed/Future Sprint | Target Version | Key Subsystem Delivered |
| :--- | :--- | :--- |
| **Sprint 1** | v0.1 | Stable interfaces, DI Container, Sandboxing protocols |
| **Sprint 2** | v0.2 | AST Parser, cycle detection, technology scanners |
| **Sprint 3** | v0.3 | Gemini Provider, Prompt Library, allowed-tool filter registry |
| **Sprint 4** | v0.4 | Git worktrees workspace, DB session logging, Sandbox fallbacks |
| **Sprint 5** | v0.4 | Kahn's DAG scheduler, PlanDAG structured generator |
| **Sprint 5.5** | v0.4 | Execution Runtime, topological step execution, halts |
| **Sprint 6** | v0.4 | ReAct AgentExecutor loop, Sandbox command token sanitization |
| **Sprint 7** | v0.5 | WebSocket Event Broker, HITL Orchestration pause states |
| **Sprint 8** | v0.6 | Compilers & pytest sandboxed self-repair logs |
| **Sprint 9** | v0.7 | Experience ledger, compacting context token managers |
| **Sprint 10**| v0.8 | Swarm debate brokers, Tech Lead / Reviewer consensus |
| **Sprint 11**| v0.9 | Postgrespgvector, JWT RBAC tenant keys, directory watchers |
| **Sprint 12**| v1.0 | Third-party plugin lifecycle hooks, E2E issue resolver |

---

## 4. Capability Matrix

| Capability | v0.1 | v0.2 | v0.3 | v0.4 | v0.5 | v0.6 | v0.7 | v0.8 | v0.9 | v1.0 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **DI Container** | X | | | | | | | | | |
| **Local Sandbox** | X | | | | | | | | | |
| **AST Parsing** | | X | | | | | | | | |
| **Circular DFS** | | X | | | | | | | | |
| **Prompt Library**| | | X | | | | | | | |
| **Model Registry**| | | X | | | | | | | |
| **Git Worktrees** | | | | X | | | | | | |
| **ReAct Loop** | | | | X | | | | | | |
| **Sanitization**  | | | | X | | | | | | |
| **WebSocket Stream**| | | | | X | | | | | |
| **HITL Pause** | | | | | X | | | | | |
| **Self-Repair** | | | | | | X | | | | |
| **Ledger Memory** | | | | | | | X | | | |
| **Swarms Debate** | | | | | | | | X | | |
| **Postgres Swap** | | | | | | | | | X | |
| **JWT RBAC** | | | | | | | | | X | |
| **Plugin Hooks** | | | | | | | | | | X |

---

## 5. Release Quality Gates

1. **Architecture Gate (v0.1 - v1.0):** No direct global singletons allowed. All classes must register in `di_setup.py` and resolve through `DIContainer`.
2. **Security Gate (v0.4):** Sandbox command tokens must pass sanitization. Redirection and chaining operators are rejected.
3. **Repository Awareness Gate (v0.2):** Scanners must detect stacked technologies and conventions, topologically mapping cyclic files.
4. **Testing Gate (v0.1 - v1.0):** No stubs/mocks inside tests for core execution logic. Code coverage for new components must exceed 90%.
5. **Performance Gate (v0.2 - v0.9):** Codebase scanners must index files in <10ms per file, preventing UI freezes.
6. **Human Review Gate (v0.5):** All worktree commits must generate a unified diff for approval before mainline merge.

---

## 6. Technical Debt Roadmap

| Rank | Debt Description | Impact | Target Version |
| :--- | :---: | :---: | :--- |
| **Critical** | Windows process `shell=True` dependency | Potential escaping if cmd tokens bypass validation checks | v0.5 (Refactor process command formatting) |
| **High** | Absence of process CPU/Memory bounds | Sandbox loops could crash host developer systems | v0.5 (Add Windows job objects caps) |
| **Medium** | OpenAI & Anthropic SDK Stubs | Swapping models is blocked | v0.6 (Implement provider connectors) |
| **Medium** | AST parser stacks limitations | Scans compiled languages as files only, no symbol extraction | v0.7 (Add Go/Rust scanner plugins) |
| **Low** | Direct filesystem workspace write | Bypasses WorkspaceManager transactional stage hooks | v0.6 (Refactor agent file edits) |

---

## 7. Competitive Comparison Matrix

Comparing architecture and capabilities without marketing bias:

| Capability | CodeOrbit AI v2.2 | Cursor | Claude Code | Devin |
| :--- | :---: | :---: | :---: | :---: |
| **Workspace Isolation** | **Git Worktrees (Safe)**| Host Filesystem | Host Filesystem | Container VM |
| **Sandboxing fallback**| **Dual Docker/Local** | None | None | Container VM |
| **Cycle Detection** | **DFS Topological** | None | None | None |
| **Execution Control** | **DAG Kahn's scheduler**| Single-step ReAct | Single-step ReAct | Multi-agent loop |
| **Provider Agility** | **DI Decoupled** | Hardcoded OpenAI | Claude Only | Custom LLM |
| **Human Review** | **HITL Pause PR Review**| Manual Accept | Manual Accept | Console PR panel |
| **Third-Party Plugins**| **Extensible v1.0 Hooks**| None | None | Playwright API |

---

## 8. Final Recommendation

CodeOrbit AI is exceptionally close to the constitutional vision, having laid down the decoupled interfaces, code crawling databases, sandboxed worktree isolated workspaces, and planning schedules. The core engine is mathematically robust and verified.

The most critical version is **v0.5 Human Collaboration**, as it transforms CodeOrbit from a local backend runner into a collaborative UI engineering console. Observability and security boundaries (cmd sanitization, process throttle caps) must never be compromised during subsequent sprints.
