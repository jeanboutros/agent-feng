# Agent Feng

AI application built with **pydantic-ai** and **MCP (Model Context Protocol) servers**, with optional **FastAPI** exposure.

## Project Purpose

Agent Feng is an async AI agent application designed to:
- Integrate with AI providers via pydantic-ai for structured, type-safe AI interactions
- Connect to MCP servers for extended tool capabilities
- Optionally expose functionality via FastAPI endpoints

## Architecture Overview

This project follows **Clean Architecture** with strict layer separation:

```
src/agent_feng/
├── __main__.py           # Composition root (entry point)
├── domain/               # Business logic, entities, value objects
├── application/          # Use cases, application services
├── infrastructure/       # Adapters, external integrations (MCP, AI providers)
└── interfaces/           # CLI, FastAPI routes, external contracts
```

### Layer Dependencies

- **Domain** → No external dependencies
- **Application** → Domain only
- **Infrastructure** → Application, Domain
- **Interfaces** → Application, Domain

## Prerequisites

- Python ≥ 3.14
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

## Configuration

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Configure environment variables in `.env`:
   ```bash
   LOG_LEVEL=INFO          # DEBUG, INFO, WARNING, ERROR, CRITICAL
   ENVIRONMENT=development # development, staging, production
   ```

3. Application configuration is in `config/config.yaml`

## How to Run

### macOS

```bash
# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"

# Run the application
python -m agent_feng
```

### Linux

```bash
# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"

# Run the application
python -m agent_feng
```

### Docker

```bash
# Build the image
docker build -t agent-feng .

# Run the container
docker run --rm \
  -e LOG_LEVEL=INFO \
  -e ENVIRONMENT=production \
  agent-feng
```

## Running Tests

```bash
# Install dev dependencies
uv pip install -e ".[dev]"

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_main.py
```

## Residual Risk

### Known Failure Modes

| Failure Mode | Residue | Mitigation |
|--------------|---------|------------|
| Missing .env file | Application uses defaults (INFO/development) | Documented defaults, .env.example provided |
| Invalid LOG_LEVEL | Falls back to INFO | Validation at startup |
| MCP server unavailable | Agent operates without MCP tools | Graceful degradation (planned) |

### Trade-offs and Limitations

- **Async-only**: All I/O operations are async; sync wrappers exist only at entry points
- **Python 3.14+**: Modern Python features required, limiting compatibility
- **Configuration via files**: No runtime configuration changes

### Expected Degradation Behaviour

1. **Missing AI provider credentials**: Application logs error and exits
2. **MCP server timeout**: Continues without MCP tools, logs warning
3. **Invalid configuration**: Fails fast at startup with clear error message

## License

MIT