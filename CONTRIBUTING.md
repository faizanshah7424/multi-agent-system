# Contributing to Multi-Agent AI Platform

Thank you for showing interest in contributing to the Multi-Agent AI Platform! We welcome contributions that improve code quality, enhance documentation, add test coverage, or optimize execution performance.

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

## How Can I Contribute?

### 1. Reporting Bugs
- Search existing issues to see if the bug has already been reported.
- If not, create a new issue. Include details on how to reproduce the bug, the expected behavior, and logs/screenshots.

### 2. Suggesting Enhancements
- Open a discussion issue describing the feature, why it is useful, and potential implementation details.

### 3. Submitting Pull Requests
- Fork the repository.
- Create a feature branch (`git checkout -b feature/amazing-feature`).
- Write clean, formatted code.
- Ensure all tests pass (`pytest`).
- Run code quality tools (`ruff check .` and `black --check .`).
- Commit changes using semantic messages (`git commit -m 'feat: add agent role description'`).
- Push to the branch and open a Pull Request targeting `main`.

## Coding Standards

- **Python**: Follow PEP 8 guidelines. Format code using `black` and lint with `ruff`.
- **Typing**: Use static type hints for all function signatures.
- **Tests**: Add unit/integration tests under the `tests/` directory for any new logic.
- **Security**: Never commit secrets or API keys. Ensure code passes `bandit` security checks.
