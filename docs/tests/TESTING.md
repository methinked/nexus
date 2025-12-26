# Testing Environment & Protocols

> **Core Principle:** Documentation is key. Careful planning is vital.

This document describes the testing environment for the Nexus project and the protocols for validating changes.

## 1. Test Environment

### 1.1 Infrastructure
- **Framework**: `pytest`
- **Async Support**: `pytest-asyncio`
- **Coverage**: `pytest-cov`
- **Location**: `/tests` directory
- **Configuration**: Defined in `pyproject.toml` under `[tool.pytest.ini_options]`

### 1.2 Structure
```
tests/
├── core/       # Tests for nexus.core (FastAPI, DB, Utils)
├── agent/      # Tests for nexus.agent (Collectors, Services)
└── cli/        # Tests for nexus.cli (Commands, Formatting)
```

## 2. Test Execution

### 2.1 Running Tests
Execute tests using the virtual environment interpreter:
```bash
# Run all tests
./venv/bin/pytest

# Run tests with coverage report
./venv/bin/pytest --cov=nexus

# Run specific test file
./venv/bin/pytest tests/core/test_utils.py
```

### 2.2 Recording Results
**Requirement:** Significant test runs must be recorded in this `docs/tests/` directory to maintain a historical record of stability and regression testing.

**Format:**
Create a file named `YYYY-MM-DD_feature-name.md` containing:
1.  **Objective**: What is being tested?
2.  **Command**: The exact command executed.
3.  **Result**: Pass/Fail summary.
4.  **Output**: Snippet of the test output or coverage report.
5.  **Notes**: Observations, bugs found, or fixed.

## 3. Planning & Documentation Rules

1.  **Document First**: Before writing code, document the plan.
2.  **Update Context**: Keep `CONTEXT.md` and `README.md` synchronized with reality.
3.  **Save Results**: Always save test results in `docs/tests/`.
4.  **No Assumptions**: If a test fails, investigation is mandatory. Do not skip.
