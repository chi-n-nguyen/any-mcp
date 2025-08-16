"""
Main entry point for Notion MCP Server
"""

import asyncio
import json
import logging
import sys
import traceback
from .server import NotionMCPServer
from .utils.config import get_notion_token

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    """
    Main server loop - handles stdin/stdout communication for MCP protocol.
    
    This is the standard pattern for MCP servers:
    1. Read JSON-RPC messages from stdin
    2. Process through handle_request
    3. Write responses to stdout
    """
    server = NotionMCPServer()
    
    logger.info("Notion MCP Server starting...")
    token = get_notion_token()
    logger.info(f"Notion API configured: {'Yes' if token else 'No'}")
    
    while True:
        try:
            # Read a line from stdin
            line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            
            if not line:
                break
                
            line = line.strip()
            if not line:
                continue
            
            # Parse JSON-RPC message
            try:
                message = json.loads(line)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON received: {e}")
                continue
            
            # Handle the request
            response = await server.handle_request(message)
            
            # Send response
            print(json.dumps(response), flush=True)
            
        except KeyboardInterrupt:
            logger.info("Server shutting down...")
            break
        except Exception as e:
            logger.error(f"Server error: {e}")
            logger.error(traceback.format_exc())