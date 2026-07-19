# Architecture Decision Record (ADR-007): Context Management Architecture

## Status
Approved

## Context
CodeOrbit AI agents frequently read repository source code to make decisions, execute tests, and implement new features. Currently, the `FileReaderTool` reads entire files directly into LLM prompts. In large repositories, this results in:
- Rapid context window saturation and token exhaustions.
- High API inference latency and increased costs.
- Hallucinations due to prompt bloating.

We require a system that dynamically allocates context budgets, partitions file content into semantic chunks, and isolates retrieved context from executable agent instructions.

## Decision
We implement a multi-tiered Context Management System in Sprint 1 consisting of the following architectural blocks:
1. **ITokenizer Capability Abstraction**: General interface defining token boundaries, output scopes, and specific model capabilities (multimodal, tool calling, reasoning) for OpenAI (tiktoken) and Gemini (SentencePiece fallback).
2. **Stateless ContextBudgetManager**: Reusable component that accepts an allocation strategy and dynamically calculates token budgets for System, History, File Focus, Chunks, and Scratchpads.
3. **Budget Strategy Pattern**: Abstracted via `IBudgetStrategy` to allow hot-swapping different layout algorithms (e.g. `BalancedBudgetStrategy`) without altering the budget manager logic.
4. **Configurable Prompt Injection Isolation**: Configurable wrapper tags (defaulting to `<source_context>`) wrapping all retrieved code chunks to isolate instructions from codebase context.
5. **SQLite WAL Database Configurator**: Centralized connection hook class (`DatabaseConfigurator`) enforcing WAL (Write-Ahead Logging) and busy timeout settings on SQLite caches to support parallel multi-agent read/write locks.
6. **Lazy Tokenizer Registry**: Registry class that instantiates tokenizer instances lazily on demand.

## Alternatives Considered
- **Stateless Prompt Truncation**: Dropping messages arbitrarily. Rejected because it breaks context flow and destroys instruction stability.
- **Client-side tiktoken fallback only**: Rejected because Gemini and Claude models have different token ratios and maximum output tokens.
- **PgVector Global SaaS Registry**: Considered but deferred to future sprints. Local SQLite databases are lightweight and perfectly suited for workspace-scoped agent sessions.

## Consequences
- **Immutable Budgets**: Context allocations are frozen, protecting the agent runtime from concurrent mutation errors.
- **Observability**: Exposes Observability/Telemetry variables for tracking compression ratios and window allocation percentage.
- **Extensibility**: Future Tree-sitter parsers and Redis caches can plug directly into the defined interfaces.
