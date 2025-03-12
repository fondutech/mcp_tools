# MCP Knowledge Vault Search Tool

This tool provides an MCP (Machine Control Protocol) server that allows you to search your personal knowledge vault using hybrid semantic and keyword matching.
Quick example modeled off of https://modelcontextprotocol.io/quickstart/server
## Features

- Semantic vector search combined with keyword matching
- Reranking model to prioritize most relevant results
- Simple API for integration with other tools

## Prerequisites

- Python 3.7+
- Required Python packages:
  - httpx
  - mcp (FastMCP)

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd mcp_tools
```

2. Install the required dependencies:
≈
uv venv
source .venv/bin/activate
```

# Install dependencies

```bash
uv add "mcp[cli]" httpx
```

or 

```bash
pip install httpx mcp
```


## Configuration

The tool uses the following default configuration:
- API Host: `http://127.0.0.1:5000`
- Default number of results: 10

You can modify these settings in the `mcp_fondu_knowledge_search.py` file if needed.

## Starting the MCP Server

To start the MCP server, run:

```bash
python mcp_fondu_knowledge_search.py
```

The server will start and listen for requests on the standard input/output (stdio).

## Testing with Claude for Desktop

Claude for Desktop is not yet available on Linux. Linux users can proceed to the Building a client tutorial to build an MCP client that connects to the server we just built.

First, make sure you have Claude for Desktop installed. You can install the latest version [here](https://claude.ai/desktop). If you already have Claude for Desktop, make sure it's updated to the latest version.

We'll need to configure Claude for Desktop for whichever MCP servers you want to use. To do this, open your Claude for Desktop App configuration at `~/Library/Application Support/Claude/claude_desktop_config.json` in a text editor. Make sure to create the file if it doesn't exist.

For example, if you have VS Code installed:

**MacOS/Linux**
```bash
code ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

You'll then add your servers in the `mcpServers` key. The MCP UI elements will only show up in Claude for Desktop if at least one server is properly configured.

In this case, we'll add our knowledge vault server like so:

**MacOS/Linux**
```json
{
    "mcpServers": {
        "knowledge_vault": {
            "command": "/Users/name/.local/bin/uv",
            "args": [
                "--directory",
                "/ABSOLUTE/PATH/TO/PARENT/FOLDER/mcp_tools",
                "run",
                "mcp_fondu_knowledge_search.py"
            ]
        }
    }
}
```

You may need to put the full path to the `uv` executable in the command field. You can get this by running `which uv` on MacOS/Linux.

Make sure you pass in the absolute path to your server.

This tells Claude for Desktop:
- There's an MCP server named "knowledge_vault"
- To launch it by running `uv --directory /ABSOLUTE/PATH/TO/PARENT/FOLDER/mcp_tools run mcp_fondu_knowledge_search.py`
- or run with python

Save the file, and restart Claude for Desktop.

## Available Tools

### gather_relevant_user_knowledge

Search your knowledge vault using hybrid semantic and keyword matching.

**Parameters:**
- `query` (string): Natural language query for semantic search and reranking
- `keywords` (string, optional): Specific terms to prioritize in keyword matching
- `top_k` (integer, optional): Number of results to return (default: 10)

**Returns:**
A formatted string containing the most relevant results from your knowledge vault.

## Error Handling

The server logs errors to:
- Standard error output
- An `error_log.txt` file in the same directory

## Example Usage

This MCP server can be integrated with any client that supports the Machine Control Protocol. Here's a basic example of how to call the tool:

```python
from mcp.client import MCPClient

async def search_knowledge():
    client = MCPClient()
    result = await client.call_tool(
        "gather_relevant_user_knowledge", 
        {"query": "How does quantum computing work?"}
    )
    print(result)
```

## Troubleshooting

If you encounter issues:
1. Check the error log file
2. Verify the Knowledge Vault API is running at the configured endpoint
3. Ensure you have proper network connectivity
