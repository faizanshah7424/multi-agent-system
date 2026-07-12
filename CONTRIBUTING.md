# Contributing to CodeOrbit AI

Thank you for your interest in contributing to **CodeOrbit AI**! As an open-source project ready for public beta, we welcome contributions that improve reliability, repository intelligence, developer experience, test coverage, and documentation.

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

---

## 📖 Table of Contents

1. [How Can I Contribute?](#how-can-i-contribute)
   - [Reporting Bugs](#reporting-bugs)
   - [Suggesting Enhancements](#suggesting-enhancements)
   - [Submitting Pull Requests](#submitting-pull-requests)
2. [Development Setup](#development-setup)
3. [Coding Standards & Tooling](#coding-standards--tooling)
4. [Testing & Validation](#testing--validation)
5. [Pull Request Process](#pull-request-process)

---

## 🛠️ How Can I Contribute?

### Reporting Bugs

Before submitting a bug report:
- Search existing issues to verify that the bug hasn't already been reported.
- If it's a new issue, use the **Bug Report** template.
- Provide a clear, step-by-step description of how to reproduce the issue, along with logs, database states, and system environments.

### Suggesting Enhancements

If you have ideas to improve CodeOrbit AI:
- Open a **Feature Request** issue detailing the proposed changes, the use-case it resolves, and potential implementation directions.
- Keep enhancements aligned with the Core Architecture frozen principles — focus on developer experience and stability.

### Submitting Pull Requests

All code changes are submitted via Pull Requests (PRs). Ensure that:
- You create a clear, documented issue first and link it in the PR.
- Your branch is branched off `main` and named semantically: `feature/your-feature` or `bugfix/your-fix`.
- You fill out the **Pull Request Template** completely.

---

## 💻 Development Setup

To configure a local developer environment:

1. **Fork and Clone the Repository**:
   ```bash
   git clone https://github.com/your-username/multi-agent-system.git
   cd multi-agent-system
   ```

2. **Setup the Virtual Environment**:
   ```bash
   python -m venv venv
   # Windows:
   .\venv\Scripts\activate
   # macOS/Linux:
   source venv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install pytest ruff black bandit
   ```

4. **Verify the Environment**:
   ```bash
   python codeorbit.py install
   python codeorbit.py doctor
   ```

---

## 📐 Coding Standards & Tooling

To maintain a clean and professional codebase, we enforce the following quality checks:

* **Formatting**: We use `black`. Run the formatter before committing:
  ```bash
  black .
  ```
* **Linting**: We use `ruff` for fast Python linting:
  ```bash
  ruff check . --fix
  ```
* **Type Hints**: Static type annotations are required for all public functions, classes, and methods.
* **Security Checks**: Ensure no secrets are committed and run `bandit` to identify security concerns:
  ```bash
  bandit -r core/ api/ tools/
  ```

---

## 🧪 Testing & Validation

CodeOrbit AI enforces a strict test-driven validation criteria. All PRs must maintain or improve current code coverage:

1. **Run Unit and Integration Tests**:
   ```bash
   python -m pytest
   ```
2. **Write New Tests**: Include a test fixture under the `tests/` directory for every new feature or bugfix.
3. **Execution Safety**: Do not modify runtime sandboxing permissions or disable security checks in your submissions.

---

## 🚀 Pull Request Process

1. Link the related Issue in your PR description.
2. Ensure the PR title follows semantic commit guidelines (e.g. `feat: ...`, `fix: ...`, `docs: ...`).
3. Maintain documentation integrity. Update relevant markdown files if your changes affect commands, configurations, or setup steps.
4. Verify that the GitHub Actions CI workflow runs and passes successfully.
5. Once your PR is submitted, at least one maintainer will review your code. Address feedback promptly to finalize approval.

Thank you for helping make CodeOrbit AI the best autonomous developer platform!
