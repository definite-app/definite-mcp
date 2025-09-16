# Definite API MCP Server

A Model Context Protocol (MCP) server that provides access to the Definite API for running SQL and Cube queries.

## Features

- **SQL Query Tool**: Execute SQL queries on database integrations
- **Cube Query Tool**: Execute Cube queries using JSON format
- **Optional Integration ID**: Both tools support optional integration_id parameter (uses backend default if not provided)

## Setup

1. **Install dependencies**:
   ```bash
   uv add "mcp>=1.2.0" httpx python-dotenv
   ```

2. **Set up environment**:
   Create a `.env` file with your Definite API configuration:
   ```
   DEFINITE_API_KEY=your_api_key_here
   DEFINITE_API_BASE_URL=https://staging.api.definite.app/v1
   ```

   **Environment Options:**
   - For **production**: `DEFINITE_API_BASE_URL=https://api.definite.app/v1` (default)
   - For **staging**: `DEFINITE_API_BASE_URL=https://staging.api.definite.app/v1`

3. **Test the server**:
   ```bash
   uv run python test_mcp.py
   ```

## Claude Desktop Configuration

Add this configuration to your Claude Desktop settings (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "definite-api": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/mritchie712/blackbird/def-mcp/definite-mcp",
        "run",
        "python",
        "definite_mcp.py"
      ]
    }
  }
}
```

## Claude Code CLI Configuration

For **Claude Code CLI** users, you can add this MCP server using the command line:

### Method 1: Basic CLI Setup
```bash
# Add the Definite API MCP server
claude mcp add definite-api -- uv --directory /Users/mritchie712/blackbird/def-mcp/definite-mcp run python definite_mcp.py
```

### Method 2: With Environment Variables
```bash
# Add with explicit environment variables
claude mcp add definite-api \
  --env DEFINITE_API_KEY=your_api_key_here \
  --env DEFINITE_API_BASE_URL=https://staging.api.definite.app/v1 \
  -- uv --directory /Users/mritchie712/blackbird/def-mcp/definite-mcp run python definite_mcp.py
```

### Method 3: Different Scopes
```bash
# Project-scoped (shared with team)
claude mcp add definite-api --scope project -- uv --directory /path/to/definite-mcp run python definite_mcp.py

# User-scoped (available across all projects)
claude mcp add definite-api --scope user -- uv --directory /path/to/definite-mcp run python definite_mcp.py
```

### MCP Management Commands
```bash
# List all configured MCP servers
claude mcp list

# Check server status
claude mcp get definite-api

# Remove the server
claude mcp remove definite-api
```

### Verification
After adding the MCP server, you can verify it's working by running `/mcp` in Claude Code - you should see "definite-api" listed as "connected".

**Important**: Replace `/Users/mritchie712/blackbird/def-mcp/definite-mcp` with the absolute path to your project directory.

## Usage

### SQL Queries

Execute SQL queries on your database integrations:

```python
# With default integration
await run_sql_query("SELECT * FROM users LIMIT 10")

# With specific integration
await run_sql_query("SELECT * FROM users LIMIT 10", "your_integration_id")
```

### Cube Queries

Execute Cube queries using JSON format:

```python
cube_query = {
    "dimensions": [],
    "filters": [],
    "measures": ["hubspot_deals.win_rate"],
    "timeDimensions": [{
        "dimension": "hubspot_deals.close_date",
        "granularity": "month"
    }],
    "order": [],
    "limit": 2000
}

# With default integration
await run_cube_query(cube_query)

# With specific integration
await run_cube_query(cube_query, "your_integration_id")
```

## Tools Available

1. **`run_sql_query`**
   - Parameters: `sql` (required), `integration_id` (optional)
   - Executes SQL queries on database integrations

2. **`run_cube_query`**
   - Parameters: `cube_query` (required dict), `integration_id` (optional)
   - Executes Cube queries with support for dimensions, filters, measures, and time dimensions

## Troubleshooting

- **Invalid Authorization Header**: Check that your API key is correct and properly set in the `.env` file
- **Connection Issues**: Verify that you have internet access and the Definite API is accessible
- **Integration ID**: If queries fail, try providing a specific `integration_id` parameter

## API Key Setup

Your API key can be found in the bottom left user menu of your Definite dashboard. Your `integration_id` can be found on your integration's page URL.

## Environment Configuration

The MCP server supports configurable API base URLs through environment variables:

- `DEFINITE_API_KEY`: Your API key from the Definite dashboard (required)
- `DEFINITE_API_BASE_URL`: The API base URL (optional, defaults to production)

**Examples:**
```bash
# Production (default)
DEFINITE_API_BASE_URL=https://api.definite.app/v1

# Staging
DEFINITE_API_BASE_URL=https://staging.api.definite.app/v1
```

## Test Results

✅ **Staging API is working!** Both SQL and Cube queries are successfully executing against `https://staging.api.definite.app/v1`.