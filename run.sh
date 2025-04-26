#!/usr/bin/env bash
set -e

# Parse command line arguments
GIT_REPO=""
GIT_REV=""
CONFIG_FILE=""

while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    --git-repo=*)
    GIT_REPO="${key#*=}"
    shift
    ;;
    --git-rev=*)
    GIT_REV="${key#*=}"
    shift
    ;;
    --config-file=*)
    CONFIG_FILE="${key#*=}"
    shift
    ;;
    *)
    # Unknown option
    shift
    ;;
  esac
done

# If this is running in a deployment context, ensure the config file exists
if [ -n "$CONFIG_FILE" ]; then
  if [ ! -f "$CONFIG_FILE" ]; then
    # Try to locate the file in the current directory structure
    FOUND_CONFIG=$(find . -name "$CONFIG_FILE" -type f | head -n 1)
    if [ -n "$FOUND_CONFIG" ]; then
      echo "Found config file at: $FOUND_CONFIG"
      CONFIG_FILE="$FOUND_CONFIG"
    else
      echo "Error: Config file $CONFIG_FILE not found"
      exit 1
    fi
  fi
fi

echo "===== Activating virtual environment ====="
# Check if venv exists
if [ -d "venv" ]; then
  source venv/bin/activate
else
  echo "No virtual environment found. Creating one..."
  python3 -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
fi

echo "===== Starting the MCP Server Application ====="
# Use PORT from environment or default to 8080
export PORT=${PORT:-8080}
echo "Starting server on port $PORT"
exec python -m mcp_fondu_search_user_context.run