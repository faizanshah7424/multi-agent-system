# Architecture Decision Record (ADR-009): Tree-sitter Indexing

## Status
Approved

## Context
CodeOrbit AI's prompt context optimization requires precise code symbol extraction. In Sprint 1, we introduced a placeholder regex/AST-based source indexing system. This regex-based approach is brittle, language-specific, and hard to scale. To provide a production-grade indexing engine, we require an AST parser that handles syntax structures natively, supports multiple languages, is resilient to code syntax errors, and performs indexing incrementally.

## Decision
We replace the regex-based symbol parser with a production-grade Tree-sitter parser in Sprint 2, Batch 1:
1. **TreeSitterIndexer Component**: Decoupled service solely responsible for detecting languages, building ASTs, and returning immutable `SourceSymbol` objects.
2. **Grammar Libraries Support**: Natively compiles and resolves Python, JavaScript, TypeScript (TSX/JSX), Go, and Java grammars via standard PEP 561 ABI3 wheels.
3. **Normalized Symbol Schema**: Extends the SQLite symbol index database (`retrieval_code_symbols`) to include `language`, `kind` (class, function, method, interface, struct, enum), `signature`, `parent`, `checksum`, and `updated_at`.
4. **Fast Incremental Indexing**: Workspace indexing scans files, checks hashes, skips unchanged files, drops removed files, and performs a complete indexing pass in $O(\text{changed files})$ time.
5. **Database Indexing**: Adds database indexes targeting `(language, symbol_name)`, `(file_path)`, `(kind)`, and `(checksum)` to reduce query latency to $O(\log n)$.
6. **Stateless Dependency Injection**: Registers `TreeSitterIndexer` in `di_setup.py` and injects it directly into the `RetrievalPipeline` constructor.

## Alternatives Considered
- **Pygments / RegEx Lexing**: Simple but lacks syntax parent/child understanding and scope boundaries.
- **Python-ast package only**: Only works for Python. Treesitter is mandatory for multi-language repositories.

## Consequences
- **Robust Parsers**: Parsing is robust to syntax errors (Tree-sitter generates partial parse trees).
- **No Resource Bloat**: Excludes binary files and respects the workspace limits.
- **Backward Compatibility**: Fully compatible with PromptBuilder, ContextBudget, and AgentExecutor.
