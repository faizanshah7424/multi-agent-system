# CodeOrbit AI v2.2: Self-Healing Repair Validation

This document captures the validation quality gates applied to verify the correctness of all code repairs.

---

## 1. Quality Gates Checks
Every applied code modification must undergo active validation before being accepted:

* **Linter Quality Gate:** Executes `ruff check .` to assert zero style or syntax violations.
* **Unit Testing Gate:** Runs Pytest inside the sandbox to assert that all existing and new unit tests execute with exit code 0.
* **Type Validation Gate:** Runs type checkers (like TypeScript compiler on web, or mypy/pyright on python stubs) to ensure type contract preservation.

---

## 2. Safety Rules Enforcement
To prevent "shortcuts" or degradation of code quality:
1. **No Lint Suppression:** The engine blocks the injection of `# noqa` or similar comments to bypass errors.
2. **No Test Disabling:** The engine rejects edits to tests or test configurations.
3. **No Code Deletion:** Repairs must fix logic bugs rather than simply removing lines or commenting out code blocks.
