# CodeOrbit AI v0.5: Final Product Review & Architecture Audit

> **Audit Date:** July 11, 2026  
> **Status:** Approved  
> **Target Version:** Version 0.5 (Human Collaboration baseline)

---

## Part 1 — End-to-End Workflow Evaluation

Evaluating the E2E workflow on the goal: *"Build a Hospital Management System."*

### 1. Understand the Request & Inspect Repository
* **Current Status:** Fully Operational. The indexer scans the codebase and imports Python symbol files into an SQLite database.
* **Missing Pieces:** Lacks a multi-file dependency map parser for JavaScript/TypeScript, limiting indexing to Python-centric components.
* **Required Improvements:** Add AST scrapers for TypeScript and config file parsers (package.json, pyproject.toml).

### 2. Build Specifications & Generate Architecture
* **Current Status:** Partially Operational. PromptLibrary provides templates for generating specifications, but they are not dynamically injected with parsed repository symbol contexts.
* **Missing Pieces:** Active linking between AST symbol databases and the Planning prompt templates.
* **Required Improvements:** Pass classes, types, and cycle structures as context inputs to LLM planning prompts.

### 3. Create Execution Plans
* **Current Status:** Fully Operational. Kahn's algorithm sorts DAG steps.
* **Missing Pieces:** Lacks dynamic path re-planning when steps fail (currently execution simply halts and cancels downstream).
* **Required Improvements:** Implement plan repair loops to allow step insertion or dependency updates at runtime.

### 4. Modify Repository Safely & Run Tests
* **Current Status:** Fully Operational. Git worktree sessions isolate changes, and lints/tests are executed in sandboxes with token filters.
* **Missing Pieces:** Sandbox execution runs with `shell=True` on Windows (vulnerability risk) and lacks CPU/Memory throttling limits.
* **Required Improvements:** Run subprocesses with direct parameter tuples rather than shell command lines.

### 5. Repair Failures (Self-Healing)
* **Current Status:** Not Yet Implemented (Planned for v0.6).
* **Missing Pieces:** Lacks logs diagnostic parser and agent loop code repair.
* **Required Improvements:** Build compilation and test stdout traceback interpreters.

### 6. Ask for Approvals & Produce Production-Ready Code
* **Current Status:** Fully Operational. HITL pauses on dangerous keywords and resumes execution safely on user approval.
* **Missing Pieces:** Unified diff formatting and PR reports are stubbed.
* **Required Improvements:** Implement diff generation using `git diff` inside the worktree directory.

---

## Part 2 — Product Capability Scores

* **Planning:** `90/100` (Strong Kahn's DAG topological scheduler).
* **Repository Understanding:** `82/100` (Excellent AST indexing; needs TS/JS parsing).
* **Architecture Design:** `65/100` (Prompt-driven; lacks dynamic system model injection).
* **Code Generation:** `88/100` (ReAct agent model loops enforce schema validation).
* **Repository Modification:** `92/100` (Safe Git worktree isolations).
* **Workspace Isolation:** `95/100` (SQLite tracking of sessions prevents conflicts).
* **Sandbox Security:** `85/100` (Rigorous token filters; lacks memory bounds).
* **Testing:** `90/100` (Comprehensive test coverage).
* **Self-Healing:** `0/100` (Not yet implemented).
* **Human Collaboration:** `90/100` (WebSocket event broker and resumable orchestrator active).
* **Engineering Memory:** `0/100` (Not yet implemented).
* **Observability:** `88/100` (WebSocket events stream task and agent loop states).
* **Plugin System:** `0/100` (Not yet implemented).
* **Multi-Agent Collaboration:** `10/100` (Agent profile stubs are registered, but debate is missing).
* **Developer Experience:** `80/100` (Clean pause state controls; lacks visual UI panel).
* **Production Readiness:** `75/100` (Reliable but requires sandbox resource caps).
* **Overall Product Maturity:** **`Level 2 (Transactional Automation)`**

---

## Part 3 — Biggest Weaknesses (Ranked)

1. **[CRITICAL] Sandbox Process Escapes (Windows):** Legacy shell executions run without CPU/Memory limits. A runaway python script can freeze host systems.
2. **[HIGH] Hardcoded ReAct Tool Dispatching:** Agent executor uses string matching for `read_file`/`write_file` rather than resolving dynamic tools from the `IToolRegistry`.
3. **[HIGH] Lack of Dynamic Re-Planning:** If a step fails, the planner cannot adjust downstream tasks on-the-fly.
4. **[MEDIUM] AST Parser Language Bounds:** Code crawler is constrained to Python imports.
5. **[MEDIUM] In-Memory WebSocket Callbacks:** event broker executes callbacks locally; scales poorly without message queues.
6. **[MEDIUM] Missing Diff Reporter:** HITL pauses successfully but does not generate unified PR diff reports automatically.
7. **[LOW] OpenAI/Anthropic Provider Stubs:** Hardcoded Gemini bindings in standard flows.
8. **[LOW] Task Queue Memory Scoping:** Task queuing relies on in-memory threads.
9. **[LOW] DB Lock Latency:** High SQLite write rates block database threads (partially offset by WAL).
10. **[LOW] Prompt Hardcoding:** Profile schemas assume fixed template names.

---

## Part 4 — Technical Debt Log

* **Architectural Debt:** Hardcoded tool execution inside `AgentExecutor.execute_step`. Bypasses `IToolRegistry` lookup.
* **Duplicated Logic:** File reading/writing exists both in AgentExecutor and WorkspaceManager.
* **Weak Abstractions:** The `ISandbox` interface does not mandate resource throttling parameters.
* **Refactoring Priorities:**
  1. Bind Agent actions directly to `IToolRegistry` classes.
  2. Implement direct parameter tuple command execution to remove `shell=True`.

---

## Part 5 — Constitution Compliance

* **Mission:** **Partially Compliant**. Safe repository modification exists, but E2E generation-to-verification lacks self-repair.
* **Vision:** **Partially Compliant**. Platform executes transactions but lacks multi-agent collaborative debate.
* **Repository Awareness:** **Partially Compliant**. Scans files and imports but lacks class relationship mapping.
* **Deterministic Verification:** **Partially Compliant**. Tests run in sandboxes but compiler logs are not audited.
* **Human-in-the-Loop:** **Fully Compliant**. Sensitive actions pause; execution state persists.
* **Maintainability & Extensibility:** **Fully Compliant**. High DI container decoupling.
* **Security:** **Partially Compliant**. Token checks block basic command chaining, but lacks resource bounds.
* **Observability:** **Fully Compliant**. Event broker streams steps and reasoning loops.
* **Testing & Documentation:** **Fully Compliant**. 146 tests passed; architecture and roadmaps mapped.

---

## Part 6 — Readiness Decision

**Recommendation: Option B (Pause development and first eliminate technical debt).**

*Justification:* Before introducing Self-Healing compilers (v0.6) or Swarm agents (v0.8), we must secure the execution environment. Running agent-generated code without memory/CPU bounds or direct parameter escaping (removing `shell=True`) exposes developer environments to stability risks. Refactoring the sandboxes and tool registries now guarantees a secure foundation for self-healing loops.

---

## Part 7 — Version 0.6 Design Blueprint (Self-Healing Engineering)

### 1. Objectives
* Automate the detection and repair of syntax, import, and test compilation failures inside the sandbox.
* Limit repair iteration loops to prevent execution resource exhaustion.

### 2. Success Criteria
* The agent automatically fixes a compilation break and completes the execution task successfully.
* Broken imports in Python scripts are resolved without human interaction.

### 3. Architecture Changes & New Components
```
                    +-----------------------------+
                    |  EngineeringExecutionRuntime|
                    +--------------+--------------+
                                   |
                                   v
                    +--------------+--------------+
                    |      SelfHealingEngine      |
                    +--------------+--------------+
                                   |
                     +-------------+-------------+
                     |                           |
                     v                           v
        +------------+-----------+  +------------+-----------+
        |   LinterLogParser      |  |    TestLogParser       |
        +------------------------+  +------------------------+
```

* **SelfHealingEngine:** Coordinates repair loops. If a sandbox command returns an error code, it routes stdout/stderr to compiler/test parsers.
* **LinterLogParser / TestLogParser:** Extract specific file names, line numbers, and error descriptions from traceback logs.

### 4. Subsystem Interfaces
```python
class ISelfHealingEngine(Protocol):
    def repair_failure(self, task_id: str, step: PlanStep, error_log: str, sandbox: ISandbox) -> bool:
        """
        Parses logs, prompts the agent to correct the target files, and re-executes tests.
        """
        ...
```

### 5. Risks & Mitigation
* **Risk:** Infinite repair loops consuming LLM tokens.
* **Mitigation:** Enforce a hard cap of 3 repair iterations per step.
* **Risk:** The agent attempts to fix a test by deleting/disabling the test file itself.
* **Mitigation:** Enforce file path constraints: files inside `tests/` directories cannot be modified by the developer agent during self-healing loops.
