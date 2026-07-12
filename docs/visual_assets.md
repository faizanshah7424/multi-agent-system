# CodeOrbit AI — Visual Assets Documentation

This document logs the visual assets, branding elements, and screenshot placeholders used across CodeOrbit AI's websites, repositories, and presentation decks.

---

## 🎨 Branding Logo

![CodeOrbit AI Logo](assets/logo.jpg)
*CodeOrbit AI Brand Logo — Modern, sleek dark mode aesthetic with orbital tracks illustrating agent coordination.*

---

## 📸 Visual Assets & Layout Mockups

### 1. Developer CLI (`docs/assets/cli_preview.png`)
* **Purpose**: Illustrates the unified CLI execution traces and diagnostics.
* **Layout Design**: A dark carbon-style terminal panel showing output for `python codeorbit.py doctor` and `python codeorbit.py run`.
* **Sub-components**: CP1252-safe ASCII tags, health reports, task logs.

### 2. Mission Control Dashboard (`docs/assets/dashboard_preview.png`)
* **Purpose**: Displays the Next.js Web Admin console.
* **Layout Design**: Three-column dashboard showing the real-time task queue (pending, running, success), CPU/Memory container resources profile charts, and streaming websocket logs.
* **Sub-components**: Worker heartbeats table, execution time latency breakdowns.

### 3. DAG task planner (`docs/assets/planning_preview.png`)
* **Purpose**: Visualizes the Directed Acyclic Graph (DAG) task decomposition.
* **Layout Design**: An interactive network node graph representing task steps sorted topologically.
* **Diagram representation**:
```mermaid
graph LR
    Start([Task Instruction]) --> Plan[Planner Agent]
    Plan --> Step1[Step 1: Code Scan]
    Plan --> Step2[Step 2: AST Injection Check]
    Step1 --> Step3[Step 3: Modify Routes]
    Step2 --> Step3
    Step3 --> Step4[Step 4: Pytest Runs]
    Step4 --> End([Consensus Voting])
```

### 4. Consensus Decision Loop (`docs/assets/consensus_preview.png`)
* **Purpose**: Illustrates the multi-agent consensus validation.
* **Layout Design**: A circular debate loop diagram showing reviews and audits.
* **Diagram representation**:
```mermaid
graph TD
    Dev[Developer Agent] -->|Submits Code Diff| TechLead[Tech Lead Agent]
    TechLead -->|Requests Audit| Reviewer[Reviewer Agent]
    Reviewer -->|Validates AST Syntax| Architect[Architect Agent]
    Architect -->|Verifies Structure| TechLead
    TechLead -->|Arbitrates Vote: 3/3 APPROVED| Merge[Git Workspace Merge]
```

### 5. AST & Docker Container Sandbox (`docs/assets/sandbox_preview.png`)
* **Purpose**: Illustrates local AST parser boundaries and Docker container isolation.
* **Layout Design**: A dual-shield container illustration representing security policies.
* **Diagram representation**:
```mermaid
graph TD
    Code[Submitted Code] --> AST{AST Check Engine}
    AST -->|Banned Import: sys/os| Block[RCE Blocked]
    AST -->|Safe AST Tree| Docker[Docker Container Sandbox]
    Docker -->|Restricted limits: 512MB RAM, 1 CPU| Exec[Safe Run]
```

### 6. Engineering Memory Engine (`docs/assets/memory_preview.png`)
* **Purpose**: Illustrates vector experience retrieval and semantic compaction.
* **Layout Design**: Vector space coordinates mapping cosine-similarity search matches.

### 7. Concurrency Benchmark Suite (`docs/assets/benchmark_preview.png`)
* **Purpose**: Logs high-throughput WAL performance statistics.
* **Layout Design**: Bar charts showing task creations (859/sec) and database claim transaction rates.

### 8. Closed-Loop Self-Healing (`docs/assets/self_healing_preview.png`)
* **Purpose**: Illustrates the error-reflection repair loop.
* **Layout Design**: Flow diagram showing test stack traces fed back into the LLM context.
* **Diagram representation**:
```mermaid
graph LR
    Code[Developer Code] --> Test[Pytest Execution]
    Test -->|Fail: Import Error| Repair[Self-Repair Agent]
    Repair -->|Applies Correction| Code
```
