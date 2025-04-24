#!/usr/bin/env bash
echo "===== Activating virtual environment ====="
source venv/bin/activate

echo "===== Starting the mcp Server Application ====="
# Use PORT from environment or default to 8080
export PORT=${PORT:-8080}
echo "Starting server on port $PORT"
exec python3 mcp_fondu_knowledge_search.py