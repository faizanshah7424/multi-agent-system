# Release Notes — CodeOrbit AI v1.0 Release Candidate (RC1)

We are proud to announce the first Release Candidate (**v1.0-RC1**) of CodeOrbit AI, transforming our autonomous engineering platform into a verified, developer-centric product.

---

## Key Features in RC1

### 1. One-Command Setup & Prerequisite Verifier
* Command: `codeorbit install`
* Verifies host versions, Docker status, active database migrations, workspace write limits, and API keys.

### 2. E2E Showcase Runner
* Command: `codeorbit run examples/ecommerce`
* Demonstrates the multi-agent consensus loop, planning DAG schedules, Ast audit protections, sandbox runs, and Git merges.

### 3. Isolated Sandbox Containers
* Containers enforce CPU limits (1.0 Core), memory quotas (512MB RAM), disabled network policy, and read-only host directory mounts.

### 4. Consolidated Telemetry Dashboard
* Observes and controls consensus debates, active EDR logs, security warnings, task queues, and memory lookups.

---

## Maturity Validation Statistics
* **Core Unit Tests**: 73 passed (100% pass rate)
* **Reality Score**: 94.0%
* **E2E Repair Latency**: 0.84 seconds (average)
