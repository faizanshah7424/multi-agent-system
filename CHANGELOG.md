# Changelog

All notable changes to **CodeOrbit AI** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.3.0-beta.1] - 2026-07-12

### Added
* **Community Standard Documents**: Created `SUPPORT.md` and `VERSION` files. Improved `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, and `SECURITY.md` for professional open-source presentation.
* **GitHub Templates**: Added structured `.github/PULL_REQUEST_TEMPLATE.md` and issue templates under `.github/ISSUE_TEMPLATE/` (`bug_report.md`, `feature_request.md`, `question.md`).
* **Dynamic Versioning Subsystem**: Integrated project-wide dynamic versioning reading directly from the root `VERSION` file for both CLI diagnostics and FastAPI endpoints.
* **Release Preparation Checklist & Audits**: Generated a comprehensive release checklist and documentation audits to prepare for the public beta.

### Changed
* **CLI & API Metadata Alignment**: Standardized project name, logos, and badges to reflect **CodeOrbit AI** consistently across all onboarding docs.

---

## [1.3.0-RC1] - 2026-07-11

### Added
* **Onboarding & Installation CLI**: Added `codeorbit install` to run automatic env checkers.
* **Official Demo Projects**: Configured 6 production-grade sample project structures under the `examples/` directory.
* **E2E Validation Pipeline**: Integrated command-line showrunner `codeorbit run examples/ecommerce` demonstrating the entire multi-agent cycle.
* **Diagnostics Dashboard Telemetries**: Visualized CPU core sandbox limitations, active protected files, and EME conventions.

### Changed
* **ASCII Tag Formatting**: Upgraded doctor check markers to cross-platform CP1252-safe ASCII tags.

---

## [1.2.0] - 2026-06-26

### Added
* **Docker Support**: Containerized all services including FastAPI backend ([Dockerfile](file:///E:/multi-agent-system/Dockerfile)), Next.js dashboard ([dashboard/Dockerfile](file:///E:/multi-agent-system/dashboard/Dockerfile)), and the task worker.
* **CI/CD Automation**: Created GitHub Actions workflow ([.github/workflows/ci.yml](file:///E:/multi-agent-system/.github/workflows/ci.yml)) running format checks (Black), lint checks (Ruff), security scans (Bandit), and the full Pytest test suite.
* **Load Testing Suite**: Implemented concurrent stress testing in [load_test.py](file:///E:/multi-agent-system/scripts/load_test.py) to assess database throughput and worker execution.

### Changed
* **FastAPI Lifespan Migration**: Replaced deprecated `@app.on_event` startup and shutdown events with modern context-managed lifespan hooks in [app.py](file:///E:/multi-agent-system/api/app.py).
* **Timezone-Safe Datetime Calculations**: Migrated all timezone-deprecated code (e.g. `datetime.utcnow()`) to modern, timezone-safe UTC naive datetimes in [database.py](file:///E:/multi-agent-system/core/database.py) and across all core services.
* **Clean Worker Shutdowns**: Replaced `sys.exit(0)` calls in worker threads with safe returns to eliminate Pytest threading unhandled exception warnings in [worker.py](file:///E:/multi-agent-system/core/worker.py).

### Fixed
* Resolved over **630 Deprecation and Threading warnings** during unit and integration test runs, reducing active warnings to only 2 third-party alerts.

---

## [1.1.0] - 2026-06-25

### Added
* **Security Hardening**:
  - Implemented strict path confinement in [base.py](file:///E:/multi-agent-system/tools/base.py) with absolute path resolution and directory component matching to prevent path traversals and symlink attacks.
  - Re-engineered the static analysis engine in [python_executor.py](file:///E:/multi-agent-system/tools/python_executor.py) using Python AST parsing to block low-level module imports, execution builtins, and double-underscore attributes.
  - Implemented safe process streams using `Popen` with output size limits to prevent pipe deadlocks and Out-Of-Memory crashes.
  - Enforced API payload size limits (10MB) and rate-limiter pruning to prevent memory exhaustion in [app.py](file:///E:/multi-agent-system/api/app.py).
  - Added BOLA authorization checks in [routes.py](file:///E:/multi-agent-system/api/routes.py) matching task ownership.
  - Created a custom credential-redacting formatter in [logging.py](file:///E:/multi-agent-system/core/logging.py) to scrub keys and bearer tokens from logs.
  - Standardized memory key validators and serialized size limits in [memory.py](file:///E:/multi-agent-system/core/memory.py).
* **Security Test Coverage**: Added comprehensive test cases in [test_security_hardening.py](file:///E:/multi-agent-system/tests/test_security_hardening.py) verifying all security guardrails.

---

## [1.0.0] - 2026-06-10

### Added
* **Core Agent Registry**: Dynamic registration and configuration of agent roles, prompts, and tools.
* **Asynchronous Queue Engine**: Task queuing system supporting high concurrency with SQLite WAL mode.
* **Worker Execution Pool**: Concurrent worker model leveraging transactional sqlite claims (`BEGIN IMMEDIATE`).
* **Next.js Web Dashboard**: Admin web portal for real-time monitoring, metrics charting, and task dispatching.
