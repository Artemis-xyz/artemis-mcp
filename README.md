## artemis-mcp

```
     _    ____ _____ _____ __  __ ___ ____    __  __  ____ ____
    / \  |  _ \_   _| ____|  \/  |_ _/ ___|  |  \/  |/ ___|  _ \
   / _ \ | |_) || | |  _| | |\/| || |\___ \  | |\/| | |   | |_) |
  / ___ \|  _ < | | | |___| |  | || | ___) | | |  | | |___|  __/
 /_/   \_\_| \_\|_| |_____|_|  |_|___|____/  |_|  |_|\____|_|
```

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/getting-started/installation/#installation-methods). On MacOS, you can install it using Homebrew: `brew install uv`.
- Claude Desktop
- Artemis API Key
- Artemis Snowflake Login

## Installation

### Automated Using OpenTools (Easier)

Install [OpenTools](https://opentools.com/docs/quickstart) prerequisites.

Then run:

```bash
npx opentools@latest i artemis
```

### Manual Setup (More Work)

- Install uv

Copy `sample_claude_desktop_config.json` to your `claude_desktop_config.json` file:

- On MacOS: `~/Library/Application\ Support/Claude/claude_desktop_config.json`
- On Windows: `%APPDATA%/Claude/claude_desktop_config.json`

Fill out the relevant fields in `claude_desktop_config.json`:

- `<UV_PATH>` - Path to uv executable (run `where python` on MacOS)
- `<PATH_TO_ARTEMIS_MCP_REPO>` - Path to local clone of the Artemis MCP repo
- `<ARTEMIS_API_KEY>` - Your Artemis API Key

- Restart Claude Desktop
- Artemis MCP Tools should now be available!

## Available Tools

The Artemis MCP server provides the following tools:

### API Tools
- `validate-artemis-api-key`: Creates and validates connection to Artemis API
- `get-artemis-data`: Retrieves data from Artemis API for given crypto token symbols and metrics
- `get-artemis-supported-metrics-for-symbol`: Retrieves supported metrics for a given crypto token symbol

### Formula Generation Tools
- `generate-art-formula`: Generates an ART formula for retrieving crypto prices, fees, revenue, and other time-series data
- `generate-artinfo-formula`: Generates an ARTINFO formula for asset classifications, available metrics, market cap rankings, and metadata
