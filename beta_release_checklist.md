# CodeOrbit AI — Public Beta Release Checklist

This checklist defines the required verification gates and checks to complete prior to tag publication for any public beta release.

---

## 🗂️ 1. Community & Documentation Standards
- [ ] **Code of Conduct**: [CODE_OF_CONDUCT.md](file:///E:/multi-agent-system/CODE_OF_CONDUCT.md) contains accurate community contact emails (`community@codeorbit.ai`) and contains no default placeholders.
- [ ] **Contributing Guide**: [CONTRIBUTING.md](file:///E:/multi-agent-system/CONTRIBUTING.md) describes environment setup steps, coding style requirements, lint commands, and PR processes.
- [ ] **Security Policy**: [SECURITY.md](file:///E:/multi-agent-system/SECURITY.md) contains supported version matrices and private reporting channels (`security@codeorbit.ai`).
- [ ] **Support Pathways**: [SUPPORT.md](file:///E:/multi-agent-system/SUPPORT.md) lists SLA timelines, GitHub issues, and discussions.
- [ ] **Changelog History**: [CHANGELOG.md](file:///E:/multi-agent-system/CHANGELOG.md) contains release entries following the Keep a Changelog standard.
- [ ] **Release Notes**: [RELEASE_NOTES.md](file:///E:/multi-agent-system/RELEASE_NOTES.md) covers the release highlights and validation metrics.

## 🤖 2. GitHub Developer Templates
- [ ] **Pull Request Template**: [.github/PULL_REQUEST_TEMPLATE.md](file:///E:/multi-agent-system/.github/PULL_REQUEST_TEMPLATE.md) exists and requests testing configurations and checklist self-audits.
- [ ] **Issue Templates**: Check that issue templates exist in [.github/ISSUE_TEMPLATE/](file:///E:/multi-agent-system/.github/ISSUE_TEMPLATE/):
  - [ ] Bug Report (`bug_report.md`)
  - [ ] Feature Request (`feature_request.md`)
  - [ ] Question / Support Request (`question.md`)

## 📐 3. Repository Versioning & Metadata Sync
- [ ] **VERSION File**: Root [VERSION](file:///E:/multi-agent-system/VERSION) file exists and matches the release version exactly (e.g. `1.3.0-beta.1`).
- [ ] **Diagnostics Version**: VersionManager reads and matches the version:
  ```bash
  python codeorbit.py version
  ```
- [ ] **API Version**: The FastAPI application exposes the identical version string in OpenAPI documentation (`/docs`) and in the health root endpoint (`/`).
- [ ] **Metadata Scan**: No legacy "Multi-Agent AI Platform" naming remains in public-facing documentation.

## 🧪 4. Code Quality & Security Audits
- [ ] **Code Formatting**: Ensure all files are cleanly formatted:
  ```bash
  black --check .
  ```
- [ ] **Code Linting**: Run Python code linting checks with zero warnings or errors:
  ```bash
  ruff check .
  ```
- [ ] **Security Scanning**: Scan for potential security vulnerabilities and hardcoded secrets:
  ```bash
  bandit -r core/ api/ tools/
  ```

## ⚙️ 5. Functional Validation Gates
- [ ] **Automated Test Suite**: Verify that the entire unit and integration test suite passes:
  ```bash
  python -m pytest
  ```
- [ ] **Platform Diagnostics Doctor**: Inspect local database connection health and credentials:
  ```bash
  python codeorbit.py doctor
  ```
- [ ] **System Health Check**: Verify disk space availability and workspace clean state:
  ```bash
  python codeorbit.py health
  ```
- [ ] **Sandbox Reachability**: Confirm that Docker is online and that resource limits are applied:
  ```bash
  python codeorbit.py sandbox
  ```
- [ ] **E2E Showcase Demo**: Run the E2E showcase flow to verify the planner, agents, and consensus execution loops:
  ```bash
  python codeorbit.py run examples/python_cli
  ```
