# CodeOrbit AI — System Architecture Specifications

This directory houses the detailed structural specifications and diagrams for the subsystems of **CodeOrbit AI**.

---

## 🗂️ Architecture Document Catalog

Explore the engineering specifications of each subsystem:

1. **Overall System Topography**: [overall_architecture.md](overall_architecture.md)  
   *Overview of FastAPI endpoints, SQLite transaction queues, Worker processes, and sandboxing Managers.*

2. **Task Decomposition & Scheduling**: [planning_flow.md](planning_flow.md)  
   *Topological sorting of execution graphs and cycle-validation mechanisms.*

3. **Consensus Arbitration & Reviews**: [consensus_workflow.md](consensus_workflow.md)  
   *Swarm consensus cycles, Tech Lead arbitration, and agent voting pipelines.*

4. **Self-Healing & Error Reparations**: [self_healing_pipeline.md](self_healing_pipeline.md)  
   *Closed-loop test running and automated code repair patch generation.*

5. **Code Intelligence & Memories**: [repository_intelligence.md](repository_intelligence.md)  
   *AST code indexing database nodes and long-term experience vector recall RAG.*

6. **Sandboxing Isolation Boundaries**: [runtime_execution.md](runtime_execution.md)  
   *Double-shield security parameters (AST syntax injection checking and container quotas).*
