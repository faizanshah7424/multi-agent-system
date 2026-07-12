# CodeOrbit AI — CLI Presenter Demonstration Guide

This guide outlines a 3-minute walk-through of CodeOrbit AI's CLI diagnostics and setup verification capabilities.

---

## ⏱️ Timeline & Agenda
* **00:00 - 00:30**: Introduction to CLI command structure.
* **00:30 - 01:15**: Environment verification check.
* **01:15 - 02:00**: Doctor diagnostics scan.
* **02:00 - 03:00**: Live demo simulation run.

---

## 🎙️ Demonstration Steps & Script

### 1. Unified Commands Structure
* **Action**: Run `python codeorbit.py --help` to show available subcommands.
* **Talking Points**: "CodeOrbit AI provides a single entry point `codeorbit.py` for developers to verify prerequisite configurations, monitor container sandboxes, query memory indexes, and dispatch tasks."

---

### 2. Environment Verification (Install Command)
* **Action**: Run the setup installer checklist:
  ```bash
  python codeorbit.py install
  ```
* **Talking Points**: "The installer checks for critical dependencies—Python version, Git, Node, npm, SQLite, active databases, workspace permissions, and optional container/API keys. It ensures the workspace is immediately ready to run."
* **Visuals**: Displays `Ready to build with CodeOrbit AI` success tag.

---

### 3. Subsystem Health Diagnostics (Doctor Command)
* **Action**: Execute platform doctor checks:
  ```bash
  python codeorbit.py doctor
  ```
* **Talking Points**: "The doctor checks verify config file schema validation, disk space thresholds, SQLite connection, and API variables, assuring healthy environment settings before runs."

---

### 4. Interactive Simulation Walkthrough (Demo Command)
* **Action**: Execute the E2E demo run:
  ```bash
  python codeorbit.py demo
  ```
* **Talking Points**: "For users without set up API keys or Docker, this walkthrough outlines our complete agent flow—scanning dependencies, planning topologically sorted task graphs, voting consensus, container executions, self-healing code errors, review validation, and merging changes."
