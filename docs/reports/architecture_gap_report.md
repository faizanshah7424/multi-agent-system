# CodeOrbit AI v2.2: Architecture Gap Report

Before starting **Sprint 6 (Autonomous Agents)**, the following architectural gaps have been identified and ranked by severity.

---

## 1. Critical Gaps

### Shell Injection Risk in Local Process Sandbox
* **Description:** `LocalProcessSandbox` uses `subprocess.Popen(..., shell=True)` on Windows to resolve system shell scripts.
* **Impact:** If future development agents execute scripts containing unvalidated user commands or raw model-generated parameters, they could compromise the developer's host machine.
* **Mitigation:** Introduce a token validation and character sanitization layer inside `LocalProcessSandbox.execute` to filter out execution chaining (e.g. `&`, `|`, `;`).

---

## 2. High Gaps

### Abstract Agent Execution Stubs
* **Description:** While `IPlanExecutor` correctly schedules steps, there are no concrete agent loops implementing `IAgentExecutor` (Planner, Developer, Reviewer, etc.) active in the codebase.
* **Impact:** The runtime relies on mock executions or basic command fallbacks until Sprint 6 is complete.
* **Mitigation:** Build the ReAct loop framework in Sprint 6 and map specialized agents to the DI Container.

### Absence of Sandbox CPU & Memory Throttling
* **Description:** `LocalProcessSandbox` runs as a basic child process without OS-level process group resource throttles.
* **Impact:** A script with an infinite loop or high memory allocation could crash the host system.
* **Mitigation:** Configure Windows job objects or process priority limits inside `LocalProcessSandbox` to cap memory and CPU usage.

---

## 3. Medium Gaps

### OpenAI & Anthropic Provider Stubs
* **Description:** Concrete provider classes exist but raise `NotImplementedError` upon model initialization.
* **Impact:** Swapping the execution model from Gemini to Claude or GPT-4 is blocked.
* **Mitigation:** Import and wrap the official `openai` and `anthropic` client SDKs inside `providers.py`.

### AST Parsing Language Limitations
* **Description:** Deep symbol indexing works for Python, and regex mapping works for JS/TS. Other common stacks (compiled languages like Go, Rust, C++ or database migrations like Prisma/SQL) are mapped as raw files only.
* **Impact:** Limits AST symbol and call-graph search capabilities in hybrid-technology stack codebases.
* **Mitigation:** Add extensible stack-plugin parsers under the registry system to support extra syntaxes.

---

## 4. Low Gaps

### Telemetry & Heartbeat Connection Gaps
* **Description:** Heartbeats are logged to SQLite, but real-time execution step durations and token expenditures are not broadcast to telemetry listeners in the runtime.
* **Impact:** Limits engineering console dashboard observability during long-running tasks.
* **Mitigation:** Connect task status modifications to real-time WebSocket event brokers.
