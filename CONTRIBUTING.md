# Contributing to PDF Chart Extraction

Thank you for your interest in improving this project! This document provides guidelines for contributing.

## How to Contribute

1. **Fork the repository** and create a feature branch from `main`.
2. **Install development dependencies**: `pip install -e ".[dev]"`
3. **Install pre-commit hooks**: `pre-commit install`
4. **Make your changes**, add tests, and update documentation as needed.
5. **Run the test suite**: `pytest`
6. **Run linting and type checks**: `ruff check . && ruff format . && mypy src`
7. **Submit a pull request** with a clear description of the changes.

## Development Setup

```bash
git clone https://github.com/James-Leong/pdf-chart-extraction.git
cd pdf-chart-extraction
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## Code Style

- Follow PEP 8 conventions
- Use type hints for public APIs
- Keep functions focused and well-documented
- Add tests for new functionality

## Reporting Issues

When reporting bugs, please include:

- A clear description of the problem
- Steps to reproduce
- Sample PDF or minimal reproduction case (if possible)
- Expected vs actual output
- Python version and operating system

## Feature Requests

Feature requests are welcome! Please open an issue describing:

- The use case
- The proposed behavior
- Any relevant examples or references

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
