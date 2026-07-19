# Architecture Decision Record (ADR-008): Prompt Builder & Retrieval Integration

## Status
Approved

## Context
CodeOrbit AI agent execution needs to consume relevant codebase snippets (from dynamic query retrievals) while avoiding prompt bloat and context window overflows. We need a system that:
- Prioritizes retrieved code chunks logically.
- Enforces strict token allocations on active prompts.
- Wraps context dynamically to isolate LLM reasoning from third-party instructions.
- Connects the Context Budget, Tokenizer, Caching, and Retrieval subsystems into the Agent Runtime loop.

## Decision
We implement a unified Prompt Integration pipeline in Sprint 1, Batch 4:
1. **PromptBuilder Service**: A stateless component solely responsible for compiling prompt sections in a strict order:
   - System Instructions
   - Conversation History
   - Retrieved Source Context
   - Current User Request
   - Tool Outputs
   - Execution Constraints
2. **Dynamic Prioritization**: Retrieved code chunks are sorted and filtered by exact symbol matching, file matching, and retrieval scoring, dropping lowest-ranked items first when the allocated chunk budget is exceeded.
3. **Prompt Injection Separation**: Wraps all retrieved codebase context chunks inside custom `<source_context>` tags with file metadata and hashes.
4. **Dependency Injection Setup**: Registers both `PromptBuilder` and `RetrievalPipeline` in `bootstrap_di()` for decoupled constructor injection.
5. **Agent ReAct Loop Refactor**: Updates `AgentExecutor.execute_step()` to dynamically query the index, allocate budgets, and format the prompt before each LLM turn.

## Alternatives Considered
- **Direct Appends**: Storing code blocks raw in message history. Rejected due to token bloat and lack of isolation boundaries.
- **Truncating System/Request blocks**: Slicing system or request text. Rejected because system instructions and user requests must never be truncated.

## Consequences
- **Predictable Context**: The LLM receives highly structured context blocks aligned to budget boundaries.
- **Observability**: Logging monitors the exact allocation of the context window.
- **Clean Architecture**: Decouples formatting logic (`PromptBuilder`) and database queries (`RetrievalPipeline`) from the core agent execution runtime (`AgentExecutor`).
