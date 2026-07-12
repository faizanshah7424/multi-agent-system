# CodeOrbit AI — Engineering Memory Presenter Demonstration Guide

This guide details a 3-minute walk-through illustrating how CodeOrbit AI queries its semantic experience database and compacts history.

---

## ⏱️ Timeline & Agenda
* **00:00 - 00:45**: Explaining long-term memory vs short-term context window.
* **00:45 - 01:45**: Querying the memory index via CLI.
* **01:45 - 03:00**: Showing experience RAG compaction.

---

## 🎙️ Demonstration Steps & Script

### 1. The Experience Ledger Concept
* **Action**: Reference [docs/architecture/repository_intelligence.md](file:///E:/multi-agent-system/docs/architecture/repository_intelligence.md).
* **Talking Points**: "Standard agents forget past edits immediately. CodeOrbit AI logs success patterns, database lock resolution fixes, and styling conventions inside a local SQLite-based vector index."

---

### 2. Live CLI Memory Queries
* **Action**: Execute the memory search CLI command:
  ```bash
  python codeorbit.py memory "SQLite WAL transaction locks" --limit 2
  ```
* **Talking Points**: "Developers can query long-term memory index directly from the CLI. This retrieves matching fixes sorted by cosine similarity."

---

### 3. Context Compaction RAG
* **Action**: Explain how memory is injected into prompt generation.
* **Talking Points**: "When executing new tasks, CodeOrbit AI queries the memory index, compacts matching experiences, and injects them as historical examples. This improves prompt accuracy and reduces API token costs."
