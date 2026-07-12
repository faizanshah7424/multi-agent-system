# CodeOrbit AI — Sandbox Isolation & Execution Boundaries

This document details the sandboxing safety check boundaries applied to code executions.

---

## 🛡️ Double-Shield Sandbox Topology

All code executions pass through two separate validation boundaries: static AST syntax filters and containerized sandboxes.

```mermaid
graph TD
    CodeInput[Generated Code changes] --> ASTChecker{1. AST Parser engine}
    
    subgraph AST [Static Checks Filter]
        ASTChecker -->|Blocks reflection: __subclasses__| Block[Code execution REJECTED]
        ASTChecker -->|Blocks system imports: os/sys/subprocess| Block
    end
    
    ASTChecker -->|Safe AST Tree| Docker{2. Container Sandbox}
    
    subgraph Sandbox [Isolation Run]
        Docker -->|Docker active| ContainerRun[Run in Ephemeral Container]
        Docker -->|Docker offline| LocalRun[Run in local venv subprocess]
        ContainerRun --> Constraints[RAM: 512MB<br/>CPU: 1.0 Core<br/>Network: Isolated<br/>Timeout: 30s]
        LocalRun --> Constraints
    end
    
    Constraints --> Outcome[Return execution logs & exit code]
```

---

## 🔒 Security Policies

1. **Path Confinement**: Path components verification confirms all file read/write actions are fully confined inside the configured `WORKSPACE_DIR` boundary.
2. **Resource Quotas**: Hard quotas are enforced inside container runtimes to prevent Denials of Service (DoS) due to CPU looping or RAM leakage.
3. **Log Redaction**: Outgoing stdout, stderr, and variables log files are filtered via regex keys scrubbers to sanitize API key structures or passwords before saving.
