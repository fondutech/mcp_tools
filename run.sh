#!/usr/bin/env bash
echo "===== Activating virtual environment ====="
source venv/bin/activate

echo "===== Starting the mcp Server Application ====="
exec python3 mcp_fondu_knowledge_search.py