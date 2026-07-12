# CodeOrbit AI v2.2: Self-Healing Repair Attempts Log

This log outlines the structural constraints applied to the repair loop to prevent resource leaks and guarantee deterministic progress.

---

## 1. Retry Attempt Limit (Hard Cap)
To prevent infinite reasoning loops and token exhaustion, the `SelfHealingEngine` applies a strict limit:
* **Maximum Iterations:** **`3`**
* If the workspace fails to compile or validate after the 3rd attempt, execution terminates and returns `False` immediately.

---

## 2. Iteration Workflow
1. **Diagnosis:** Read standard output tracebacks, match expressions, and classify failure category.
2. **Safety Gates Check:** Intercept modifications to test files or delete operations.
3. **Execution Routing:** Dispatch the evidence-driven instructions to `AgentExecutor`.
4. **Validation Check:** Execute Ruff and Pytest inside the sandbox.
5. **Loop Termination:** Succeed on validation pass (exit code 0); retry if failing and within limit bounds.
