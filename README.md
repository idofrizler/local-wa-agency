# WhatsApp Multi-Scenario Group Monitor

A flexible WhatsApp group monitoring system that uses AI agents to analyze messages and extract structured insights based on configurable scenarios.

## Features

- **Multi-Scenario Support**: Define custom scenarios for different types of WhatsApp groups
- **Dynamic Model Generation**: Pydantic models created automatically from JSON schemas
- **Flexible Configuration**: JSON-based scenario definitions
- **AI-Powered Analysis**: Uses local LLMs through Ollama for intelligent message parsing
- **Structured Output**: JSON or pretty-printed results for easy integration

## Overview

This is a generic framework for monitoring WhatsApp groups with AI-powered message analysis. Define your own scenarios with custom prompts and structured outputs - the framework handles the rest.

## Setup

1. Create and activate the virtualenv:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install Python dependencies:

```bash
pip install -r requirements.txt
```

3. Download the Playwright browsers (required before running the scanner):

```bash
playwright install
```

This step is intentionally separate from pip so Playwright can download the appropriate browser binaries for the host platform.

4. Configure your scenarios in `config/scenarios.json` (see Configuration section below)

## Running

### Generic Multi-Scenario Monitor

Use `main.py` to scan any configured scenarios and output structured JSON:

```bash
# Scan all configured groups with JSON output
python main.py --scrolls 5

# Pretty-printed output
python main.py --scrolls 5 --output pretty

# Scan specific groups only
python main.py --scrolls 5 --groups "Group 1" "Group 2"
```

**Output**: Structured JSON with message context and AI analysis for all scenarios.


## Configuration

Scenarios are defined in individual JSON files in the `scenarios/` directory (at project root). Each scenario file includes:

- **prompt**: Instructions for the AI agent
- **groups**: List of WhatsApp group names to monitor
- **response_schema**: JSON schema defining the structured output
- **confidence_field**: Field name for confidence classification (default: "confidence")
- **reasoning_field**: Field name for reasoning explanation (default: "reasoning")

### Adding a New Scenario

1. Create a new JSON file in `scenarios/` (e.g., `my_scenario.json`):

```json
{
  "prompt": "Your agent instructions here...",
  "groups": ["Group Name 1", "Group Name 2"],
  "confidence_field": "confidence",
  "reasoning_field": "reasoning",
  "response_schema": {
    "type": "object",
    "properties": {
      "field1": {
        "type": "string",
        "description": "Description of field1"
      },
      "confidence": {
        "type": "string",
        "enum": ["HIGH", "MEDIUM", "LOW"],
        "description": "Confidence level"
      },
      "reasoning": {
        "type": "string",
        "description": "Explanation of the analysis"
      }
    },
    "required": ["field1", "confidence", "reasoning"]
  }
}
```

2. Run the application - the Pydantic model will be created dynamically from your schema!

### JSON Schema Types

- `string`: Python `str`
- `boolean`: Python `bool`
- `integer`: Python `int`
- `number`: Python `float`
- `array`: Python `list`
- `object`: Python `dict`

For enum/literal types, use:
```json
{
  "type": "string",
  "enum": ["VALUE1", "VALUE2", "VALUE3"]
}
```

## Architecture

```
├── scenarios/                   # Scenario definition JSON files (root level)
│   ├── *.json                  # Your scenario configurations
│   └── scenario.json.template  # Template for new scenarios
├── src/                         # Core framework
│   ├── config.py               # Config loader + dynamic model creation
│   ├── agent.py                # AI agent wrapper (per scenario)
│   └── whatsapp_scanner.py     # WhatsApp Web automation
└── main.py                      # Generic entry point (all scenarios)
```

The `main.py` entry point is scenario-agnostic - it works with any scenario configuration, outputting structured JSON or pretty-printed text for easy integration with other tools.

## How It Works

1. **Configuration Loading**: `src/config.py` reads all `*.json` files from `scenarios/` and creates Pydantic models dynamically from JSON schemas
2. **Group Resolution**: Each WhatsApp group is mapped to its configured scenario
3. **Message Scanning**: Playwright automates WhatsApp Web to extract messages
4. **AI Analysis**: Each message is analyzed by the scenario's agent with scenario-specific prompts
5. **Structured Output**: Agent returns Pydantic model instances with typed fields
6. **Output**: Results outputted as JSON or pretty-printed text

## Requirements

- Python 3.11+
- Ollama running locally with a compatible model
- WhatsApp account (QR code login on first run)

## Environment Variables

Create a `.env` file:

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gpt-oss:20b
