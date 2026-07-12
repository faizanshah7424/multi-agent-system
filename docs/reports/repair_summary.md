# CodeOrbit AI v2.2: Self-Healing Repair Summary

This report summarizes how the `SelfHealingEngine` diagnoses compiler, test, and linter errors to perform evidence-driven code repair.

---

## 1. Classification Methodology
Failures received from sandbox validations are parsed and classified into structured representations:

* **Syntax Errors:** Diagnosed from Python `SyntaxError` tracebacks.
* **Import Errors:** Extracted from Python `ImportError` or `ModuleNotFoundError` outputs.
* **Type Errors:** Parsed from TypeScript compiler outputs (`error TS...`) and Python `TypeError` tracebacks.
* **Lint Errors:** Diagnosed from Ruff outputs or ESLint outputs.
* **Unit Test Failures:** Parsed from Pytest assertions (`AssertionError`).
* **Missing Dependency Errors:** Classified from missing package keywords in python/pip stack logs.

---

## 2. Evidence-Driven Repair Approach
Rather than guessing or rewriting the entire codebase, the engine uses log tracebacks to locate the precise line number, column, and error message. The Developer Agent receives these parameters to edit only the target code block, keeping edits minimal and clean.
