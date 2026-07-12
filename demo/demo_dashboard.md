# CodeOrbit AI — Dashboard Presenter Demonstration Guide

This guide details a 4-minute walk-through of CodeOrbit AI's Next.js 15 Mission Control Web Dashboard.

---

## ⏱️ Timeline & Agenda
* **00:00 - 01:00**: Launching the backend API server and dashboard.
* **01:00 - 02:00**: Navigating the live task queue and streaming logs.
* **02:00 - 03:00**: Analyzing agent latencies and transaction statistics.
* **03:00 - 04:00**: Inspecting worker heartbeats and sandbox allocations.

---

## 🎙️ Demonstration Steps & Script

### 1. Launching Dashboard
* **Action**: Launch the API backend (`python main.py`) and Next.js frontend (`npm run dev` in dashboard folder). Navigate to `http://localhost:3000`.
* **Talking Points**: "Our web dashboard connects dynamically to the SQLite WAL database and task worker queue to provide real-time operational visibility into active swarms."

---

### 2. Task Queue Monitoring
* **Action**: Click on a queued task row. Expand the streaming log panel.
* **Talking Points**: "The task monitor displays jobs sorted by state: pending, running, completed, or failed. Clicking any item opens a terminal window displaying real-time stdout and agent thought trace files."

---

### 3. Subsystem Metrics
* **Action**: Scroll to the Performance Charts section.
* **Talking Points**: "We track execution latency broken down by stage. This highlights how much time the swarm spends on planning, code writing, sandbox compiling, or consensus agreements."

---

### 4. Cluster Heartbeats & Sandbox Quotas
* **Action**: Navigate to the Active Workers & Sandbox Profiler.
* **Talking Points**: "The worker panel displays active CPU and memory profiles. We can monitor active Docker containers, verifying that memory allocations stay strictly within resource quotas."
