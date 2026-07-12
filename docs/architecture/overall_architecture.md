# CodeOrbit AI — Overall Architecture Spec

This document details the service-oriented, transactionally isolated components of **CodeOrbit AI**.

---

## 🏗️ Structural Topography

CodeOrbit AI isolates orchestration logic, sandbox tasks, and intelligence layers to achieve transactional safety during autonomous runs.

```mermaid
graph TD
    User([Developer / API Client]) -->|HTTP / REST API| Gateway[FastAPI API Gateway]
    Gateway <-->|Read / Write State| DB[(SQLite WAL DB)]
    
    subgraph Core Orchestration [Core Engine]
        Worker[WorkerRuntime Process] <-->|Poll Tasks & Update| DB
        Worker -->|Executes| Engine[WorkflowEngine]
        Engine -->|Schedules Steps| Scheduler[DAG Scheduler]
        Engine <-->|Workspace State| SessionMgr[Workspace Session Mgr]
    end
    
    subgraph Workspace Isolation [Sandbox Environment]
        Engine -->|Create Sandbox| SandboxMgr[Sandbox Manager]
        SandboxMgr -->|Spawns| Container[Docker Sandbox Container]
        Engine -->|Isolate Code Branch| VFS[VFS / Git Workspace Mgr]
        VFS -->|Read / Write Diffs| Container
    end
    
    subgraph Repo Intelligence [Code Intel & Memory]
        Engine -->|Query Symbols| Indexer[CodeIndexer Engine]
        Indexer -->|AST Parser| SourceFiles[Source Code Workspace]
        Engine -->|Hybrid Search / Learn| Memory[Engineering Memory Engine]
        Memory <-->|Vector Store| VectorDB[(Local Vector DB)]
    end

    subgraph Agent Swarm [Swarm Core]
        Engine -->|Model Request| Abstraction[Model Abstraction Layer]
        Engine -->|Register / Bind Tools| ToolReg[Tool & Skill Registry]
    end
```

---

## 🔗 Subsystem Responsibilities

1. **API Gateway**: Provides REST controllers to queue tasks, fetch real-time session logs, and view worker metrics.
2. **SQLite WAL Database**: Persists task states queue with row-level transaction boundaries.
3. **Core Orchestration**: Dispatches steps, handles lock allocations, and tracks latency metrics.
4. **Workspace Sandbox**: Ephemeral Docker and AST executors preventing host machine pollution.
5. **Repo Intelligence**: Compiles structural AST relations and experience RAG compaction.
