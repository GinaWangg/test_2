---
description: "Python coding conventions for this repository"
applyTo: "**/*.py"
---

# Python Coding Conventions

## Principles
- Emphasize **readability**, **maintainability**, and **clarity over cleverness**.
- Follow **PEP 8** and use **type hints** everywhere.
- Write testable code; avoid hidden side effects.

## Naming
- Classes → `PascalCase`
- Functions/variables → `snake_case`
- Constants → `UPPER_SNAKE_CASE`
- Prefix internal or private methods with `_`

## Functions & Classes
- Keep functions **short and single-purpose**.
- If a script, module, or class has one main action, define a **`run()`** function (or method) as its clear entry point.
- Prefer guard clauses to deep nesting.
- Split large classes into cohesive, focused components.

## Docstrings and Coding Style
- All **public functions** require concise docstrings (PEP 257).
- Include purpose, parameters, return type, and expected exceptions.
- Explain *why* when behavior is non-obvious.
- Keep line length ≤ **79 characters** (or ≤ 88 if defined by formatter).

## Error Handling
- Catch **specific exceptions**; never use bare `except:`.
- Fail fast with clear, descriptive messages.
- Raise `ValueError` or `TypeError` as appropriate.
- Re-raise exceptions instead of hiding them silently.

## Testing
- Use **pytest** for all tests.
- Every public function must have at least one test.
- Cover:
  - Normal and boundary cases
  - Invalid inputs or failure paths
- Use **parametrized tests** to reduce repetition.
- Tests must be deterministic.

## Tooling
- Code must pass:
  - **black** – formatting  
  - **flake8** – linting  
  - **isort** – import order  
  - **mypy** – type checking  
  - **pytest** – testing
- Configuration lives in `pyproject.toml`.
