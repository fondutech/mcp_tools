"""
Entry point for the MCP Knowledge Search application.
"""
import sys
import os

# Add the parent directory to the Python path so we can import the main script
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the app from the main script
from mcp_fondu_search_user_context.server import app, mcp

def main():
    """Run the MCP server."""
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)

# This allows gunicorn to import app from mcp_tools.run
if __name__ == "__main__":
    # if len(sys.argv) <= 1:
    #     # Run with stdio transport for Claude Desktop
    #     mcp.run(transport='stdio')
    # else:
    main() 