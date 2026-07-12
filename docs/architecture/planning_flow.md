# CodeOrbit AI — Task Planning & DAG Scheduling Flow

This document details how high-level user instructions are compiled into execution task schedules.

---

## 📋 Task Decomposition Flow

CodeOrbit AI decomposes instructions into a topological task graph verified to prevent cycle loops before execution starts.

```mermaid
sequenceDiagram
    autonumber
    actor Developer as Dev / API Client
    participant Planner as Planner Agent
    participant Validator as Cycle Check Engine
    participant Scheduler as DAG Scheduler
    participant Queue as SQLite Task Queue

    Developer->>Planner: Submit task request ("Fix hospital vitals validation")
    Planner->>Planner: Scan symbol index & identify target files
    Planner->>Planner: Decompose task into sequential subtask steps
    Planner-->>Validator: Submit planned execution graph
    
    rect rgb(240, 240, 255)
        Note over Validator: Run Depth-First Search (DFS)<br/>to trace dependency routes
        alt Cycle Detected
            Validator-->>Planner: Reject plan with cycle route details
            Planner->>Planner: Re-compile and adjust dependencies
        else Cycle-Free
            Validator-->>Scheduler: Approve planned graph
        end
    end

    Scheduler->>Scheduler: Sort task steps topologically
    Scheduler->>Queue: Commit task steps to SQLite with status PENDING
    Queue-->>Developer: Return allocated task ID
```

---

## 📐 Graph Execution Rules

1. **Deterministic Order**: Step execution strictly follows the topological sort order.
2. **Failure Propagation**: If any parent step fails, all downstream successor steps are suspended (status `BLOCKED`) to preserve codebase consistency.
3. **Recovery Boundaries**: Task steps can be re-run from the point of failure after applying manual or automated fixes.
