# Copilot Instructions for Agent Feng

## Project Overview

Agent Feng is an AI application built with **pydantic-ai** and **MCP (Model Context Protocol) servers**, with potential **FastAPI** exposure for external interfaces. The application runs fully **asynchronous**.

---

## Architecture

This project follows **Clean Architecture** with strict layer separation:

```
src/agent_feng/
├── __main__.py           # Composition root (entry point)
├── domain/               # Business logic, entities, value objects
├── application/          # Use cases, application services
├── infrastructure/       # Adapters, external integrations (MCP, AI providers)
└── interfaces/           # CLI, FastAPI routes, external contracts
```

### Layer Rules

- **Domain** has no external dependencies
- **Application** depends only on Domain
- **Infrastructure** implements interfaces defined in Application
- **Interfaces** orchestrate calls to Application services
- Dependencies always point **inward**

---

## Code Standards

### Python Version

- Python ≥ 3.14 (as specified in pyproject.toml)

### Type Hints

- **Mandatory** for all public and internal APIs
- Use `from __future__ import annotations` in all modules

### Docstrings

- **Sphinx-style docstrings** for all modules, classes, and functions
- Include **examples** for all public APIs

### Async

- All I/O-bound operations must be **async**
- Use `asyncio` for concurrency
- Prefer `async def` over sync wrappers

---

## Key Dependencies

| Library       | Purpose                                    |
|---------------|--------------------------------------------|
| `pydantic-ai` | AI agent framework with structured outputs |
| `mcp`         | Model Context Protocol server integration  |
| `fastapi`     | HTTP API exposure (when needed)            |
| `pydantic`    | Data validation and settings management    |

---

## Configuration

- **YAML files** in `config/` for application configuration
- **`.env` file** for environment variables and secrets
- Environment variables: `LOG_LEVEL`, `ENVIRONMENT`

---

## Logging

- Base logger name: `PANPAN`
- Logging configuration is done **only** at the entry point (`__main__.py`)
- All library modules use `logging.getLogger(__name__)` with `NullHandler`

---

## Running the Application

```bash
# Local execution
python -m agent_feng

# Via script
agent-feng
```

---

## Shell Command Execution

**IMPORTANT**: Always activate the local Python virtual environment before executing any shell command.

```bash
# Activate the virtual environment first
source .venv/bin/activate

# Then run commands
python -m agent_feng
pytest -v
uv add <package> 
# or 
uv add --dev <package>
```

When using terminal tools, prefix commands with environment activation or use `uv run` to ensure the correct Python environment is used.

---

## Testing

- **pytest** is mandatory
- Tests mirror the Clean Architecture structure:
  ```
  tests/
  ├── domain/
  ├── application/
  ├── infrastructure/
  └── interfaces/
  ```

---

## Patterns to Use

- **Strategy Pattern** for pluggable AI providers
- **Factory Pattern** for constructing agents and services
- **Dependency Injection** via composition root

## Anti-Patterns to Avoid

- God objects
- Global state outside composition root
- Business logic in CLI or infrastructure layers
- Implicit dependencies

---

## When Generating Code

1. Always add type hints
2. Always add Sphinx docstrings with examples
3. Ensure async where I/O is involved
4. Follow Clean Architecture layer boundaries
5. Use `StrEnum` for state, `TypedDict` for external data structures
