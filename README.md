# azure-pricing-mcp

An [MCP (Model Context Protocol)](https://modelcontextprotocol.io) server that lets LLMs query Azure service pricing using the public [Azure Retail Prices API](https://learn.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices).

No Azure credentials required — the API is free and public.

## Quick Start

Run directly with [`uvx`](https://docs.astral.sh/uv/):

```bash
uvx azure-pricing-mcp
```

Or install and run:

```bash
uv pip install azure-pricing-mcp
azure-pricing-mcp
```

## Tools

| Tool | Description |
|---|---|
| `search_prices` | Search Azure retail prices by service, region, SKU, or product name |
| `estimate_cost` | Estimate monthly cost for a service given quantity and usage hours |
| `compare_regions` | Compare prices for a service/SKU across Azure regions (sorted cheapest first) |
| `list_services` | Discover available Azure services (with optional text search) |
| `list_regions` | List Azure regions (optionally filtered by service) |

All tools support a `currency_code` parameter (default: `USD`). Examples: `EUR`, `BRL`, `GBP`, `JPY`.

## Usage Examples

Once connected to an MCP client (Claude Desktop, Cursor, Claude Code, etc.), you can ask:

- *"What's the price of a D2 v3 VM in East US?"*
- *"Estimate the monthly cost for 5 Standard_LRS storage accounts in West Europe"*
- *"Compare Virtual Machines D4 v3 pricing across all regions"*
- *"List all Azure services related to 'database'"*
- *"What regions offer Azure Cosmos DB?"*

## Configuration

### Using `mcp.json` (VS Code / GitHub Copilot)

Create an `mcp.json` file in your project's `.vscode` folder (`.vscode/mcp.json`) to share the server with your team:

```json
{
  "servers": {
    "azure-pricing": {
      "command": "uvx",
      "args": ["azure-pricing-mcp"]
    }
  }
}
```

Or add it at the user level (`~/.vscode/mcp.json`) to make it available across all projects.

> **Tip:** When opening a project with an `mcp.json`, VS Code will prompt you to start the MCP server automatically.

### Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "azure-pricing": {
      "command": "uvx",
      "args": ["azure-pricing-mcp"]
    }
  }
}
```

### Claude Code

```bash
claude mcp add azure-pricing -- uvx azure-pricing-mcp
```

### Cursor

Add to your Cursor MCP settings (`.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "azure-pricing": {
      "command": "uvx",
      "args": ["azure-pricing-mcp"]
    }
  }
}
```

### Windsurf

Add to your Windsurf MCP config (`~/.windsurf/mcp.json`):

```json
{
  "mcpServers": {
    "azure-pricing": {
      "command": "uvx",
      "args": ["azure-pricing-mcp"]
    }
  }
}
```

## Running with PM2

An `ecosystem.config.js` is included for process management. First make sure dependencies are installed:

```bash
uv sync
```

Then start with PM2:

```bash
pm2 start ecosystem.config.js

# Check status
pm2 status

# View logs
pm2 logs azure-pricing-mcp

# Stop
pm2 stop azure-pricing-mcp

# Restart on system boot
pm2 startup
pm2 save
```

## Development

```bash
# Clone and install
git clone https://github.com/pimentelleo/azure-pricing-mcp.git
cd azure-pricing-mcp
uv sync

# Run locally
uv run azure-pricing-mcp

# Test with MCP Inspector
npx -y @modelcontextprotocol/inspector uv run azure-pricing-mcp
```

## How It Works

This server uses the [Azure Retail Prices REST API](https://learn.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices) to fetch real-time public pricing data for Azure services. Key characteristics:

- **No authentication required** — the API is publicly accessible
- **Real-time data** — prices are updated regularly by Microsoft
- **Public retail prices only** — does not include enterprise agreements or negotiated rates
- **Supports all Azure services** — VMs, Storage, Databases, Networking, AI/ML, and more

## License

MIT
