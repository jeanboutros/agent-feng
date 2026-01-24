# Agent Feng

AI application built with **pydantic-ai** and **MCP (Model Context Protocol) servers**, with optional **FastAPI** exposure.

---

> [!NOTE]  
> Please note that this project is in a very early stage of development and is a 
> hobby project that I am building in my spare time. 
> If you want to pitch in you are more than welcome and if you something that
> doesn't look right please let me know.

## Vision

Agent Feng is an autonomous, self-improving market intelligence system. Its purpose is to monitor, analyse, and predict market movements across multiple asset classes by coordinating specialised AI agents that continuously learn from their successes and failures.

### Core Philosophy

**Self-Critical Learning**: The system does not blindly accumulate knowledge. It maintains a feedback loop where predictions are validated against actual market outcomes. False positives trigger instruction refinement, while correct inferences reinforce and strengthen the underlying reasoning patterns. Over time, the agents become more accurate and contextually aware.

**Historical Context**: Market behaviour is rarely unprecedented. Agent Feng maintains a researched corpus of historical events and their cascading effects—financial crises, geopolitical shifts, supply chain disruptions, policy changes—enabling agents to recognise patterns and analogies that inform current analysis.

### Agent Architecture

The system employs a hierarchical multi-agent design:

| Agent Type | Role | Examples |
|------------|------|----------|
| **Principal Agents** | Domain specialists with deep expertise | Stocks, Indexes, Oil & Gas, Commodities, Crypto, Forex |
| **Worker Agents** | Data acquisition from diverse sources | News scrapers, Twitter/X monitors, Reddit sentiment, SEC filings, earnings transcripts |
| **Contextual Agents** | External factor specialists | Seasonality, weather patterns, holidays, geopolitical events, marketing campaigns |

Principal agents orchestrate worker agents to gather intelligence, then synthesise insights with contextual agents to produce nuanced, multi-factor analysis.

### External Factors

Market movements are influenced by forces beyond pure financial data:

- **Seasonality** — Retail cycles, agricultural harvests, energy demand patterns
- **Weather** — Commodity prices, logistics disruptions, insurance events
- **Holidays** — Trading volume changes, consumer spending shifts
- **World Events** — Elections, conflicts, treaties, pandemics
- **Marketing Campaigns** — Product launches, brand sentiment, viral moments

Specialised contextual agents monitor these factors and provide signals to principal agents.

### Extensibility via MCP

As the system evolves, new **Model Context Protocol (MCP) servers** will be integrated to expand capabilities:

- Real-time market data feeds
- Alternative data sources (satellite imagery, shipping data, social sentiment)
- Execution and alerting interfaces
- Knowledge graph and memory persistence

The architecture is designed for continuous expansion without disrupting existing agent workflows.

---

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