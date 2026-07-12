# CodeOrbit AI — Self-Healing Presenter Demonstration Guide

This guide details a 3-minute walk-through illustrating how CodeOrbit AI automatically heals compilation and unit test failures.

---

## ⏱️ Timeline & Agenda
* **00:00 - 00:45**: Explaining sandbox execution and test interception.
* **00:45 - 01:45**: Simulating a compilation error (NameError / ImportError).
* **01:45 - 03:00**: Triggering the automated repair patches loop.

---

## 🎙️ Demonstration Steps & Script

### 1. Ephemeral Sandbox Execution
* **Action**: Reference [docs/architecture/self_healing_pipeline.md](file:///E:/multi-agent-system/docs/architecture/self_healing_pipeline.md) or execute the demo simulator.
* **Talking Points**: "Standard AI helpers copy code suggestions with zero validations. CodeOrbit AI executes test suites inside restricted sandboxes, capturing logs and stack traces if code fails."

---

### 2. Error Interception & Context Injection
* **Action**: Point out Step 5 in `python codeorbit.py demo`.
* **Talking Points**: "If pytest returns a non-zero exit code, our Self-Repair Engine parses the line numbers and error logs, formatting them back into the Developer Agent's context window. The agent behaves like a human engineer, inspecting the stack trace to locate the issue."

---

### 3. Verification & Guardrails
* **Action**: Emphasize how the second test execution passes.
* **Talking Points**: "On the next iteration, the agent applies a corrected code patch. Once the tests pass successfully, the code is forwarded for peer review. To protect API budgets, the healing loop enforces a hard cap of 3 repair attempts."
