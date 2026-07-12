# CodeOrbit AI v2.2: Sprint 6 Architecture Notes

These notes capture architectural design decisions, safety parameters, and subsystem interfaces implemented for Sprint 6.

---

## 1. ReAct Loop State Management
* **State Scope:** The ReAct history is scoped entirely inside the runtime execution context. Agent decisions are recorded sequentially inside memory buffers, ensuring that the model's history stays bounded by token limits.
* **Format Guarantees:** Decoupled ReAct loops utilize Pydantic model validation (`AgentDecision`). This guarantees that LLM responses can be parsed into exact execution structures (`thought`, `action`, `command`, `file_path`, `content`, `final_answer`) deterministically, failing fast if the model deviates from schema rules.

---

## 2. Sandbox Safety Boundaries
* **Command Verification:** `LocalProcessSandbox` acts as host process wrapper. To prevent untrusted command executions from escaping sandbox directories, `LocalProcessSandbox` applies an active token check:
  * Block standalone shell chaining operators: `;`, `&`, `&&`, `|`, `||`, `>`, `<`, `>>`.
  * Block subexpression evaluations anywhere in the token: `` ` `` and `"$("`.
* **Resource Bounds:** The local process sandbox isolates directory paths. Subprocesses are run inside the task's worktree (`workspace_path`), keeping mainline Git history decoupled.

---

## 3. Pluggable Dispatch Routing
* **Decoupling Agent Logic:** The execution runtime resolves the `IAgentExecutor` interface dynamically. This keeps plan scheduling (`IPlanExecutor`) isolated from action loops, allowing developers to extend agent roles without changing topological DAG sorting logic.
* **Variable Binding Resolution:** Prompt variables (defined in template markdown files) are populated dynamically. If a template asks for extra properties, they are mapped from step metadata, preventing variable format validation crashes.
