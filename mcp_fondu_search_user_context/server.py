from typing import Any, Dict, List, Optional
import sys
import traceback
import logging
import httpx
import os
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("knowledge_vault")

# Create a FastAPI app
app = FastAPI(title="Knowledge Vault MCP API")

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                   stream=sys.stderr)

print("Starting knowledge_vault MCP server...", file=sys.stderr)

# API configuration
# NEXT_PUBLIC_API_HOST = "http://127.0.0.1:5000"
NEXT_PUBLIC_API_HOST = "https://api.youfondu.com"

USER_AGENT = "personal-vault-app/1.0"

try:
    error_log = open("/tmp/error_log.txt", "a")
except OSError:
    # Fall back to using stderr for logging when file can't be created
    import sys
    error_log = sys.stderr

async def make_fondu_api_request(url: str, method: str = "GET", json_data: dict = None) -> dict[str, Any] | None:
    """Make a request to the API with proper error handling."""
    logging.debug(f"Making {method} request to: {url}")
    headers = {
        # "User-Agent": USER_AGENT,
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    logging.debug(f"Using headers: {headers}")
    async with httpx.AsyncClient() as client:
        try:
            logging.debug(f"Sending HTTP {method} request...")
            if method.upper() == "GET":
                response = await client.get(url, headers=headers, timeout=30.0)
            elif method.upper() == "POST":
                response = await client.post(url, headers=headers, json=json_data, timeout=30.0)
            else:
                logging.error(f"Unsupported HTTP method: {method}")
                return None
                
            logging.debug(f"Received HTTP status code: {response.status_code}")
            response.raise_for_status()
            logging.debug("Successfully parsed JSON response")
            return response.json()
        except Exception as e:
            logging.error(f"Error in API request: {type(e).__name__}: {str(e)}")
            error_log.write(f"ERROR: {str(e)}\n")
            error_log.flush()
            return None


        
@mcp.tool()
async def gather_relevant_user_knowledge(
    query: str,
    # user_id: str,
    keywords: str = "",
    top_k: int = 10
) -> str:
    """Search your knowledge vault using hybrid semantic and keyword matching.
    
    This tool combines semantic vector search with keyword matching to find the most relevant
    information in your personal knowledge vault. It uses a two-stage process:
    1. Generates candidate matches using both semantic understanding and keyword relevance
    2. Applies a reranking model to return the top most relevant results
    
    Args:
        query: Natural language query for semantic search and reranking
        user_id: Your unique user identifier
        keywords: Specific terms to prioritize in keyword matching (optional)
        top_k: Number of results to return (default: 10)
    
    Returns:
        A formatted string containing the most relevant results from your knowledge vault
    """
    # print(f"Tool called with query: {query}, user_id: {user_id}", file=sys.stderr)
    
    try:
        # Prepare the API endpoint URL
        endpoint = f"{NEXT_PUBLIC_API_HOST}/v1/knowledge/search_knowledge_vault"
        
        # Prepare the request payload
        payload = {
            "query": query,
            "keywords": keywords,
            "top_k": top_k
        }
        
        print(f"Calling API endpoint: {endpoint}", file=sys.stderr)
        
        # Make the API request
        response = await make_fondu_api_request(
            url=endpoint,
            method="POST",
            json_data=payload
        )
        
        if response is None:
            return "Error: Failed to get a response from the knowledge vault API."
        
        # Extract results from the response
        results = response.get("results", [])
        count = response.get("count", 0)
        
        print(f"Search completed successfully, found {count} results", file=sys.stderr)
        
        # Format the results into a string
        if count == 0:
            return "No relevant information found in your knowledge vault."
        
        # Return formatted results
        return_text = f"Found {count} relevant results in your knowledge vault:\n\n"
        for i, result in enumerate(results, 1):
            # Handle different possible result formats
            if isinstance(result, dict):
                # Extract relevant fields if result is a dictionary
                text = result.get("text", "")
                source = result.get("source", "")
                metadata = result.get("metadata", {})
                
                return_text += f"{i}. "
                if text:
                    return_text += f"{text}\n"
                if source:
                    return_text += f"Source: {source}\n"
                if metadata:
                    return_text += f"Metadata: {metadata}\n"
            else:
                # If result is a string or other format
                return_text += f"{i}. {result}\n"
            
            return_text += "\n"
        
        return return_text
        
    except Exception as e:
        error_msg = f"Error performing knowledge vault search: {str(e)}\n{traceback.format_exc()}"
        print(error_msg, file=sys.stderr)
        return f"Error performing knowledge vault search: {str(e)}"


@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/api/mcp")
async def handle_mcp_request(request: Request):
    try:
        body = await request.json()
        # Pass the request to MCP for processing
        result = await mcp.process_json_request(body)
        return JSONResponse(content=result)
    except Exception as e:
        logging.error(f"Error handling MCP request: {str(e)}")
        return JSONResponse(content={"error": str(e)}, status_code=500)

if __name__ == "__main__":
    try:
        # Get port from environment variable or use default
        port = int(os.environ.get("PORT", 8080))
        
        # Start the FastAPI server with uvicorn
        print(f"Starting FastAPI server on port {port}", file=sys.stderr)
        uvicorn.run(app, host="0.0.0.0", port=port)
    except Exception as e:
        error_msg = f"Fatal error in MCP server: {str(e)}\n{traceback.format_exc()}"
        print(error_msg, file=sys.stderr)
        sys.exit(1) 