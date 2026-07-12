# CodeOrbit AI — Swarm Consensus Presenter Demonstration Guide

This guide details a 3-minute walk-through illustrating how multiple specialized agents audit and approve code changes before merging.

---

## ⏱️ Timeline & Agenda
* **00:00 - 01:00**: Swarm roles definitions (Planner, Developer, Reviewer, Architect, Tech Lead).
* **01:00 - 02:00**: Audit checking validations (AST checks, confinements).
* **02:00 - 03:00**: Consensus voting and merge arbitration.

---

## 🎙️ Demonstration Steps & Script

### 1. Swarm Roles Deconstruction
* **Action**: Reference [docs/architecture/consensus_workflow.md](file:///E:/multi-agent-system/docs/architecture/consensus_workflow.md).
* **Talking Points**: "Rather than a single LLM stream, CodeOrbit AI coordinates specialized agent roles. A Planner sorts steps, a Developer writes patches, a Reviewer audits formatting, and an Architect validates target system dependencies."

---

### 2. Peer Review Audits
* **Action**: Run `python codeorbit.py demo` and focus on Step 6.
* Talk Point: "The Reviewer Agent reviews git diffs. It scans the code for security injection attempts, absolute path confinements to prevent traversal escapes, and code style compliance."

---

### 3. Consensus Voting & Merge
* **Action**: Focus on Step 7 in the demo trace.
* **Talking Points**: "Once audits pass, the Tech Lead collects votes. If consensus is reached (e.g. 3/3 approvals), the branch is merged into the protected main branch. Workspace worktree sessions are then cleaned up automatically."
