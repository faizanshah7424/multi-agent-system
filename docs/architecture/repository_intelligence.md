# CodeOrbit AI — Repository Intelligence & Memory Engine

This document details the AST code scanning indexing and long-term experience vector recall system.

---

## 🧠 Code Intelligence & Experience RAG Topology

CodeOrbit AI scans codebase directory syntax to compile code relationships and utilizes semantic experience ledgers to query historical fixes.

```mermaid
graph TD
    Workspace[Source Code Files] --> Scanner[AST Code Indexer]
    Scanner -->|Extracts Class & Method Nodes| Symbols[(Symbol Table SQLite)]
    
    subgraph experience_RAG [Engineering Memory Engine]
        Task[New Task Instruction] --> Query[Query vector embeddings]
        Query --> Match{Matches found?}
        Match -->|Yes| Compaction[Compact past experience fixes into context]
        Match -->|No| Prompt[Generic Agent instructions]
        Compaction --> Prompt
    end
    
    Prompt --> Execution[Autonomous run]
    Execution -->|Save Outcome| Ledger[(Experience vector index)]
```

---

## 🗂️ Symbol Resolution

* **Dependency Paths**: Scans and parses class dependencies, imports, and function arguments into structural entities.
* **Semantic Compactor**: Condenses past task execution transcripts, keeping model tokens usage concise.
* **Vector Index**: Uses local vector storage schemas to perform cosine-similarity retrieval searches.
