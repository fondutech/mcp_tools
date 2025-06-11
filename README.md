# MCP Knowledge Vault Search Tool

This tool provides an MCP (Model Context Protocol) server that allows you to search your personal knowledge vault using hybrid semantic and keyword matching. The server connects to the Fondu Knowledge Vault API to retrieve relevant information from your personal knowledge base.

## Features

- **Hybrid Search**: Combines semantic vector search with keyword matching
- **Reranking**: Uses reranking models to prioritize the most relevant results
- **Flexible Authentication**: Multiple authentication methods with priority-based resolution
- **Production Ready**: Comprehensive error handling and logging
- **MCP Compatible**: Works with Claude Desktop and other MCP clients
- **SSE Transport**: Server-Sent Events for real-time communication

## Prerequisites

- Python 3.8+
- Access to Fondu Knowledge Vault API
- Valid authentication token

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd mcp_tools
```

2. Set up virtual environment and install dependencies:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Authentication Setup

The server supports multiple authentication methods with the following priority order:

### 1. Explicit Parameter (Highest Priority)
Pass the token directly when calling the tool.

### 2. Environment Variables
Set one of these environment variables:
```bash
export FONDU_AUTH_TOKEN="your-token-here"
# or
export FONDU_API_TOKEN="your-token-here"
```

### 3. Configuration Files
Create a config file at one of these locations:
- `~/.fondu/config.yaml` (recommended)
- `~/.config/fondu/config.yaml`
- `config.yaml` (in project directory)

Example config file:
```yaml
fondu:
  auth_token: "your-token-here"
  base_url: "https://api.youfondu.com"

server:
  host: "127.0.0.1"
  port: 8080
  debug: true
```

### 4. Token Files
Save your token in one of these files:
- `~/.fondu/token`
- `~/.config/fondu/token`
- `.fondu_token`

## Starting the MCP Server

### Method 1: Direct Python (Recommended)
```bash
source .venv/bin/activate
python mcp_fondu_search_user_context/server.py --host 127.0.0.1 --port 8080
```

### Method 2: Using the run script
```bash
./run.sh
```

The server will start on `http://127.0.0.1:8080` with the following endpoints:
- `/` - Homepage
- `/health` - Health check
- `/sse` - Server-Sent Events endpoint for MCP
- `/messages/` - Message handling endpoint

## Claude Desktop Configuration

To use with Claude Desktop, add this to your `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "knowledge_vault": {
      "command": "python",
      "args": ["/absolute/path/to/mcp_tools/mcp_fondu_search_user_context/server.py"],
      "env": {
        "FONDU_AUTH_TOKEN": "your-auth-token-here"
      }
    }
  }
}
```

Alternative using the run script:
```json
{
  "mcpServers": {
    "knowledge_vault": {
      "command": "/absolute/path/to/mcp_tools/run.sh",
      "env": {
        "FONDU_AUTH_TOKEN": "your-auth-token-here"
      }
    }
  }
}
```

## Available Tools

### gather_relevant_user_knowledge

Search your knowledge vault using hybrid semantic and keyword matching.

**Parameters:**
- `query` (string, required): Natural language query for semantic search and reranking
- `auth_token` (string, optional): Authentication token (if not set via env/config)
- `keywords` (string, optional): Specific terms to prioritize in keyword matching
- `top_k` (integer, optional): Number of results to return (default: 10)

**Returns:**
A formatted string containing the most relevant results from your knowledge vault, including source information and metadata when available.

**Example Response:**
```
Found 3 relevant results in your knowledge vault:

1. Quantum computing uses quantum mechanical phenomena like superposition and entanglement to perform calculations...
Source: quantum_computing_notes.md
Metadata: {'tags': ['physics', 'computing'], 'date': '2024-01-15'}

2. The fundamental principle behind quantum algorithms is the ability to exist in multiple states simultaneously...
Source: research_papers/quantum_algorithms.pdf
Metadata: {'author': 'Dr. Smith', 'year': 2023}
```

## Testing

### Server Health Test
```bash
curl http://127.0.0.1:8080/health
```

### Tool Functionality Test
Create a test script to verify the tool works:
```python
import asyncio
import sys
sys.path.append('mcp_fondu_search_user_context')

from server import gather_relevant_user_knowledge

async def test_tool():
    result = await gather_relevant_user_knowledge(
        query="machine learning algorithms",
        auth_token="your-token-here",
        top_k=5
    )
    print(result)

asyncio.run(test_tool())
```

## Configuration Examples

Example configuration files are provided:
- `config.yaml.example` - Server configuration template
- `claude_desktop_config.json.example` - Claude Desktop setup template

Copy these files and customize with your settings:
```bash
cp config.yaml.example ~/.fondu/config.yaml
# Edit with your auth token and preferences
```

## Error Handling and Logging

The server provides comprehensive error handling:

- **Missing Auth Token**: Clear error message with setup instructions
- **API Errors**: Graceful handling of network issues and API failures  
- **Invalid Tokens**: Proper 403 error handling
- **Debug Logging**: Detailed logs for troubleshooting

Logs are written to:
- Standard error output (visible when running the server)
- `/tmp/error_log.txt` (fallback error logging)

## API Configuration

The server connects to:
- **Production API**: `https://api.youfondu.com/v1/knowledge/search_knowledge_vault`
- **Protocol**: HTTPS with Bearer token authentication
- **Timeout**: 30 seconds for API requests
- **Format**: JSON request/response

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Verify your token is valid and not expired
   - Check token is properly set via environment variable or config file
   - Ensure no extra whitespace in token files

2. **Connection Issues**
   - Verify internet connectivity
   - Check if API endpoint is accessible: `curl -I https://api.youfondu.com`
   - Ensure no firewall blocking outbound HTTPS

3. **MCP Client Issues**
   - Restart Claude Desktop after configuration changes
   - Check that absolute paths are used in configuration
   - Verify Python virtual environment is properly activated

4. **Server Startup Issues**
   - Ensure all dependencies are installed: `pip install -r requirements.txt`
   - Check port 8080 is not already in use
   - Verify Python 3.8+ is being used

### Debug Mode

To enable debug logging, set the environment variable:
```bash
export PYTHONPATH=/path/to/mcp_tools
export DEBUG=1
python mcp_fondu_search_user_context/server.py
```

### Testing Authentication Methods

You can test different authentication methods:
```python
# Test with environment variable
export FONDU_AUTH_TOKEN="your-token"
python test_auth.py

# Test with config file
echo "fondu:\n  auth_token: your-token" > ~/.fondu/config.yaml
python test_auth.py

# Test with token file
echo "your-token" > ~/.fondu/token
python test_auth.py
```

## Development

To contribute or modify the server:

1. **Setup Development Environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Run Tests**
   ```bash
   python test_mcp_server.py
   python test_tool_functionality.py
   ```

3. **Code Structure**
   - `mcp_fondu_search_user_context/server.py` - Main server implementation
   - `requirements.txt` - Python dependencies
   - `run.sh` - Convenience script for starting server
   - `config.yaml.example` - Configuration template
   - `claude_desktop_config.json.example` - Claude Desktop setup template

## Dependencies

Core dependencies:
- `fastapi>=0.109.2` - Web framework
- `uvicorn>=0.27.1` - ASGI server
- `httpx>=0.26.0` - HTTP client
- `mcp>=1.3.0` - Model Context Protocol
- `PyYAML>=6.0` - YAML configuration support

See `requirements.txt` for complete dependency list.

## Deployment

### AWS App Runner

This server is ready for deployment to AWS App Runner. See `DEPLOYMENT.md` for detailed deployment instructions.

**Quick Deploy**:
1. Push code to your Git repository
2. Create App Runner service pointing to your repository
3. Set `FONDU_AUTH_TOKEN` environment variable
4. Deploy!

The server includes:
- ✅ App Runner configuration (`apprunner.yaml`)
- ✅ Docker support (`Dockerfile`)
- ✅ Health check endpoint (`/health`)
- ✅ Environment variable configuration
- ✅ Production-ready logging
- ✅ Auto-scaling support

### Other Cloud Platforms

The server can be deployed to any platform that supports:
- Python 3.8+
- Environment variables
- HTTP/HTTPS traffic on port 8080

Tested platforms:
- AWS App Runner ✅
- Docker containers ✅
- Traditional VPS hosting ✅

## License

[Add your license information here]
