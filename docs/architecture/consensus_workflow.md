# CodeOrbit AI — Swarm Consensus Workflow

This document details the multi-agent arbitration and consensus checks that govern code modifications.

---

## 🗳️ Swarm Consensus Agreement Loop

CodeOrbit AI enforces a secure peer-review cycle before writing changes to the protected main code branch.

```mermaid
graph TD
    Proposal[Developer Agent submits diff] --> TechLead{Tech Lead Agent}
    TechLead -->|Dispatches Review| Reviewer[Reviewer Agent]
    TechLead -->|Dispatches Structure| Architect[Architect Agent]
    
    subgraph Audit Checks [Code Quality & Structure Audits]
        Reviewer -->|1. Runs AST Syntax Audit| RevStatus{Passed?}
        Reviewer -->|2. Runs Confinement Boundary Check| RevStatus
        Architect -->|3. Verifies Design Compliance| ArchStatus{Passed?}
    end
    
    RevStatus -->|No: request edits| Proposal
    ArchStatus -->|No: request edits| Proposal
    
    RevStatus -->|Yes| Vote[Tech Lead votes]
    ArchStatus -->|Yes| Vote
    
    Vote -->|Arbitrates Agreement: 3/3 APPROVED| Merge[Git Workspace Merge]
    Vote -->|Disagreements or warnings| Proposal
```

---

## 🛡️ Swarm Roles

* **Developer Agent**: Formulates files modifications, applies code changes, and fixes sandbox failures.
* **Reviewer Agent**: Audits raw Git diffs, checking code readability, styling formatting, and security syntax injection boundaries.
* **Architect Agent**: Confirms changes align with the target subsystems boundaries and database layouts.
* **Tech Lead Agent**: Resolves discrepancies, gathers Swarm votes, and commits approvals.
