# Release Notes — CodeOrbit AI v1.3.0-beta.1

We are thrilled to announce the first public beta release (**v1.3.0-beta.1**) of **CodeOrbit AI**! This release marks our transition from a local development environment into a production-ready, open-source multi-agent AI orchestration repository.

This release focuses on repository professionalization, comprehensive onboarding documentation, community standard guidelines, issue and pull request templates, and dynamic system-wide version synchronization.

---

## 🌟 Key Features in v1.3.0-beta.1

### 1. One-Command Setup & Verification Checklist
* **CLI Command**: `python codeorbit.py install`
* **Checks**: Verifies local host system prerequisites including Python (3.11+), Node.js (18+), Git, Docker Engine daemon status, SQLite database permissions, and API key environment variables.

### 2. Sandbox Container Isolation & Security
* Ephemeral container execution environments with restricted resources (512MB RAM, 1 CPU Core, isolated bridge networking).
* Local process verification sandbox utilizing AST syntax parsing to intercept dangerous imports, reflection loops, and system-level overrides.

### 3. Integrated Diagnostics & Doctor Commands
* **CLI Commands**: `python codeorbit.py doctor`, `python codeorbit.py health`, and `python codeorbit.py sandbox`
* Simplifies developer operations by scanning database transactions, verifying write-ahead logging (WAL) connection health, and mapping active sessions.

### 4. Consolidated Telemetry Dashboard
* Observes and controls consensus loops, active execution logs, task queues, and semantic memory conventions in real-time.

### 5. Standardized Community Files & Templates
* Complete integration of `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `SECURITY.md`, and `SUPPORT.md`.
* Automated issue templates for Bug Reports, Feature Requests, and Support Questions, along with a comprehensive Pull Request Checklist template.

---

## 🧪 Verification & Stability Statistics

* **Core Test Suite**: 179 unit, integration, and security test fixtures.
* **Test Success Rate**: 100% passing.
* **Database Concurrency Capacity**: 859 task creations/sec and 108 concurrent queue claims/sec.
* **Security Validation**: AST injection prevention and BOLA access validation verified via custom security suites.

---

## 🚀 Getting Started

To get started with the beta release, refer to the [Quick Start](README.md#-quick-start) section in the README.

For inquiries, support requests, or bug reports, please check [SUPPORT.md](SUPPORT.md) or open a GitHub Issue using one of the templates.
