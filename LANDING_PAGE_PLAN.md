# Landing Page Plan — CodeOrbit AI Public Website

This document outlines the layout, design system, copywriting, and component definitions for CodeOrbit AI's upcoming public launch website.

---

## 🎨 Brand Design System

* **Primary Background**: Sleek Dark Slate (`#0B0F19`)
* **Accents**: Neon Orchid Purple (`#A855F7`) & Electric Cyan (`#06B6D4`)
* **Typography**: Modern Sans-Serif (Outfit / Inter)
* **Visual Style**: Glassmorphic card backdrops, subtle digital grid overlays, and neon micro-glow borders.

---

## 📐 Section Layout Plan

### 1. Hero Section (Header)
* **Goal**: Capture interest within 3 seconds.
* **Layout**: Centered typography with an interactive animated terminal mockup on the right.
* **Copy**:
  - *Headline*: "The Autonomous Multi-Agent AI Software Engineer."
  - *Sub-headline*: "CodeOrbit AI indexes your repository, creates topology-sorted plans, executes code modifications in container sandboxes, and self-heals bugs autonomously."
* **CTA Buttons**: "Get Started Free" (Primary Cyan) & "Run Interactive Demo" (Secondary Purple outlines).

---

### 2. Live Interactive Demo
* **Goal**: Show immediate proof of value.
* **Layout**: A mock terminal console player that lets visitors click "Play Demo" to watch a simulated trace of the `python codeorbit.py demo` output.
* **Trace content**:
  - Scanning repository classes.
  - Planning execution DAG.
  - Swarm voting consensus.
  - Sandbox execution and self-healing.
  - Merged confirmation.

---

### 3. Key Capabilities & Swarm Roles
* **Goal**: Outline feature advantages.
* **Layout**: 3-column grid of glassmorphic cards.
* **Features Listed**:
  - **Dual-Shield Sandbox**: Static AST checks and Docker resource limits (512MB RAM, 1 Core).
  - **Directed Acyclic Graphs (DAG)**: Decomposes objectives into topologically sorted steps validated to prevent loops.
  - **Engineering Memory (EME)**: Cosmetic compaction RAG that pulls historical experience solutions.
  - **SQLite WAL Concurrency**: Peaked task queue throughput at 850+ task operations per second.

---

### 4. Interactive Swarm Visualizer
* **Goal**: Educate users on multi-agent collaboration.
* **Layout**: An interactive flowchart where users can hover over agent roles (Tech Lead, Developer, Reviewer, Architect) to see how they collaborate in a consensus cycle.

---

### 5. Sandboxed Runtime & Security Guardrails
* **Goal**: Address concerns about security.
* **Layout**: Widescreen panel displaying AST injection blocks (filtering `sys`, `os`, reflection overrides) and workspace path confinement boundaries.

---

### 6. Installation & Setup
* **Goal**: Provide a quick setup flow.
* **Layout**: Two-tab block: Python local install & Docker container run.
* **Code snippet**:
  ```bash
  git clone https://github.com/faizanshah7424/multi-agent-system.git
  cd multi-agent-system
  python codeorbit.py install
  python codeorbit.py demo
  ```

---

### 7. Performance Benchmarks
* **Goal**: Back up claims with developer-centric data.
* **Layout**: Clean bar charts displaying WAL transaction throughputs and task execution latencies.

---

### 8. Release Roadmap
* **Goal**: Show product velocity.
* **Layout**: Vertical timeline from version v0.1 up to v1.3.0-beta.1 (Current) and the path to v2.0.

---

### 9. Call to Action (CTA Footer)
* **Goal**: Conclude user journey with conversions.
* **Layout**: Widescreen card with neon purple gradients.
* **Copy**: "Deploy your first autonomous developer swarm today."
* **Buttons**: "Read onboarding Guide" & "Fork on GitHub".
