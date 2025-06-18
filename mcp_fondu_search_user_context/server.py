from typing import Any, Dict, List, Optional
import sys
import traceback
import logging
import httpx
import os
import uvicorn
import argparse
import json
import yaml
from pathlib import Path
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, HTMLResponse, Response
from starlette.routing import Mount, Route
from mcp.server.fastmcp import FastMCP
from mcp.server.sse import SseServerTransport
from mcp.server import Server
from agentic_profile_auth import (
    create_challenge,
    ClientAgentSessionStore,
    ClientAgentSession,
    ClientAgentSessionUpdates,
    AgenticChallenge,
    handle_authorization
)
from agentic_profile_auth.did_resolver import HttpDidResolver
from agentic_profile_auth.models import AgenticProfile

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

print("Starting knowledge_vault MCP server...", file=sys.stderr)

# Initialize FastMCP server
mcp = FastMCP("knowledge_vault")

# API configuration
# NEXT_PUBLIC_API_HOST = "http://127.0.0.1:5000"
NEXT_PUBLIC_API_HOST = "https://api.youfondu.com"

USER_AGENT = "personal-vault-app/1.0"

def load_config() -> Dict[str, Any]:
    """Load configuration from various sources with priority order."""
    config = {}
    
    # 1. Try to load from config file
    config_paths = [
        "config.yaml",
        "config.json", 
        os.path.expanduser("~/.fondu/config.yaml"),
        os.path.expanduser("~/.config/fondu/config.yaml")
    ]
    
    for config_path in config_paths:
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    if config_path.endswith('.yaml') or config_path.endswith('.yml'):
                        import yaml
                        file_config = yaml.safe_load(f)
                    else:
                        file_config = json.load(f)
                
                if file_config:
                    config.update(file_config)
                    print(f"Loaded config from: {config_path}", file=sys.stderr)
                    break
            except Exception as e:
                print(f"Warning: Could not load config from {config_path}: {e}", file=sys.stderr)
    
    return config

def get_auth_token(provided_token: Optional[str] = None) -> Optional[str]:
    """Get auth token from multiple sources with priority order."""
    
    # Priority 1: Explicitly provided token (from MCP client or command line)
    if provided_token and provided_token != "":
        return provided_token
    
    # Priority 2: Environment variable
    env_token = os.getenv("FONDU_AUTH_TOKEN") or os.getenv("FONDU_API_TOKEN")
    if env_token:
        return env_token
    
    # Priority 3: Config file
    config = load_config()
    config_token = config.get("fondu", {}).get("auth_token") or config.get("auth_token")
    if config_token:
        return config_token
    
    # Priority 4: Check for token file
    token_paths = [
        os.path.expanduser("~/.fondu/token"),
        os.path.expanduser("~/.config/fondu/token"),
        ".fondu_token"
    ]
    
    for token_path in token_paths:
        if os.path.exists(token_path):
            try:
                with open(token_path, 'r') as f:
                    token = f.read().strip()
                    if token:
                        print(f"Loaded token from: {token_path}", file=sys.stderr)
                        return token
            except Exception as e:
                print(f"Warning: Could not read token from {token_path}: {e}", file=sys.stderr)
    
    return None

try:
    error_log = open("/tmp/error_log.txt", "a")
except OSError:
    # Fall back to using stderr for logging when file can't be created
    import sys
    error_log = sys.stderr

async def make_fondu_api_request(url: str, method: str = "GET", json_data: dict = None, auth_token: str = None) -> dict[str, Any] | None:
    """Make a request to the API with proper error handling."""
    logging.debug(f"Making {method} request to: {url}")
    headers = {
        # "User-Agent": USER_AGENT,
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    # Add authorization header if token is provided
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
        
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
    auth_token: str = "",
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
        auth_token: Your authentication token for API access (optional if set via env/config)
        keywords: Specific terms to prioritize in keyword matching (optional)
        top_k: Number of results to return (default: 10)
    
    Returns:
        A formatted string containing the most relevant results from your knowledge vault
    """
    print(f"Tool called with query: {query}", file=sys.stderr)
    
    # Get auth token from multiple sources
    final_auth_token = get_auth_token(auth_token)
    
    if not final_auth_token:
        return """Error: No authentication token found. Please provide a token via one of these methods:
        1. Set FONDU_AUTH_TOKEN environment variable
        2. Pass auth_token parameter to this tool
        3. Create a config file at ~/.fondu/config.yaml with:
           fondu:
             auth_token: "your-token-here"
        4. Save token to ~/.fondu/token file"""
    
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
        
        # Make the API request with auth token
        response = await make_fondu_api_request(
            url=endpoint,
            method="POST",
            json_data=payload,
            auth_token=final_auth_token
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

# HTML homepage
async def homepage(request: Request) -> HTMLResponse:
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head><meta charset="UTF-8"><title>Knowledge Vault MCP Server</title></head>
    <body><h1>Knowledge Vault MCP Server</h1><p>Server is running.</p></body>
    </html>
    """
    return HTMLResponse(html_content)

# Health check endpoint
async def health_check(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})

# In-memory session store for challenges
class InMemoryClientAgentSessionStore(ClientAgentSessionStore):
    def __init__(self):
        self.sessions = {}
        self.counter = 0

    async def create_client_agent_session(self, secret: str) -> str:
        self.counter += 1
        session_id = f"session-{self.counter}"
        self.sessions[session_id] = ClientAgentSession(
            challenge_id=session_id,
            challenge=secret
        )
        return session_id

    async def fetch_client_agent_session(self, challenge_id: str) -> Optional[ClientAgentSession]:
        return self.sessions.get(challenge_id)

    async def update_client_agent_session(self, challenge_id: str, updates: ClientAgentSessionUpdates) -> None:
        session = self.sessions.get(challenge_id)
        if session:
            for key, value in updates.dict(exclude_unset=True).items():
                setattr(session, key, value)

# Simple in-memory store for agentic profiles
class InMemoryAgenticProfileStore:
    def __init__(self):
        self.profiles = {}
    
    async def save_agentic_profile(self, profile: AgenticProfile) -> None:
        """Save an agentic profile"""
        self.profiles[profile.id] = profile
    
    async def get_agentic_profile(self, did: str) -> Optional[AgenticProfile]:
        """Get an agentic profile by DID"""
        return self.profiles.get(did)

# Initialize stores and resolvers
session_store = InMemoryClientAgentSessionStore()
profile_store = InMemoryAgenticProfileStore()
did_resolver = HttpDidResolver(store=profile_store)

async def get_profile(request: Request) -> Response:
    """
    Handle profile requests with DID-based authentication.
    
    Flow:
    1. If no auth token, return 401 with challenge
    2. If auth token provided, validate it and return profile
    """
    auth = request.headers.get("authorization", "")
    
    if not auth:
        # Step 1: No auth token - return challenge
        challenge: AgenticChallenge = await create_challenge(session_store)
        return Response(
            status_code=401,
            headers={
                "WWW-Authenticate": f'did_challenge {json.dumps(challenge.challenge)}'
            },
            content=json.dumps({
                "error": "Unauthorized",
                "challenge": challenge.challenge
            }),
            media_type="application/json"
        )
    
    try:
        # Step 2: Validate auth token
        session = await handle_authorization(auth, session_store, did_resolver)
        print('session',session)
        if not session or not session.agent_did:
            return Response(
                status_code=401,
                content=json.dumps({"error": "Invalid session or agent DID"}),
                media_type="application/json"
            )
        
        # Step 3: Return profile for authenticated session
        return JSONResponse({
            "profile": {
                "agent_did": session.agent_did,
                "authenticated": True
            }
        })
        
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        return Response(
            status_code=401,
            content=json.dumps({"error": f"Authentication failed: {str(e)}"}),
            media_type="application/json"
        )

def create_starlette_app(mcp_server: Server, *, debug: bool = False) -> Starlette:
    sse = SseServerTransport("/messages/")

    async def handle_sse(request: Request) -> None:
        async with sse.connect_sse(
                request.scope, request.receive, request._send
        ) as (read_stream, write_stream):
            await mcp_server.run(
                read_stream,
                write_stream,
                mcp_server.create_initialization_options(),
            )

    return Starlette(
        debug=debug,
        routes=[
            Route("/", endpoint=homepage),
            Route("/health", endpoint=health_check),
            Route("/v1/profile", get_profile, methods=["GET", "POST"]),
            Route("/sse", endpoint=handle_sse),
            Mount("/messages/", app=sse.handle_post_message),
        ],
    )

# Create a global app instance for backward compatibility with imports
mcp_server = mcp._mcp_server
# Use environment variable to set debug mode
is_development = os.getenv('ENVIRONMENT', 'production') == 'development'
app = create_starlette_app(mcp_server, debug=is_development)

if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser(description='Run Knowledge Vault MCP server')
        parser.add_argument('--host', default='0.0.0.0')
        # Use PORT environment variable if available (for AWS App Runner)
        default_port = int(os.getenv('PORT', 8080))
        parser.add_argument('--port', type=int, default=default_port)
        args = parser.parse_args()
        
        print(f"Starting Starlette server on {args.host}:{args.port}", file=sys.stderr)
        
        # Set debug=False for production deployment
        is_development = os.getenv('ENVIRONMENT', 'production') == 'development'
        app = create_starlette_app(mcp_server, debug=is_development)
        
        uvicorn.run(app, host=args.host, port=args.port)
    except Exception as e:
        error_msg = f"Fatal error in MCP server: {str(e)}\n{traceback.format_exc()}"
        print(error_msg, file=sys.stderr)
        sys.exit(1) 