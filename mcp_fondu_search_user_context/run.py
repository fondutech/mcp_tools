"""
Entry point for the MCP Knowledge Search application.
"""
import sys
import os
import logging
import uvicorn

# Add the parent directory to the Python path so we can import the main script
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the app from the main script
from mcp_fondu_search_user_context.server import app, mcp

def main():
    """Run the MCP server."""
    
    # Set up logging for AWS App Runner
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stdout  # App Runner captures stdout
    )
    
    try:
        port = int(os.environ.get("PORT", 8080))
        host = "0.0.0.0"  # Listen on all available interfaces
        logging.info(f"Starting server on {host}:{port}")
        uvicorn.run(app, host=host, port=port, log_level="info")
    except Exception as e:
        logging.error(f"Failed to start server: {str(e)}", exc_info=True)
        sys.exit(1)

# This allows gunicorn to import app from mcp_tools.run
if __name__ == "__main__":
    # if len(sys.argv) <= 1:
    #     # Run with stdio transport for Claude Desktop
    #     mcp.run(transport='stdio')
    # else:
    main() 