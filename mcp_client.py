import sys
import asyncio
import logging
from typing import Optional, Any
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)


class MCPClient:
    def __init__(
        self,
        command: str,
        args: list[str],
        env: Optional[dict] = None,
    ):
        self._command = command
        self._args = args
        self._env = env
        self._session: Optional[ClientSession] = None
        self._exit_stack: AsyncExitStack = AsyncExitStack()

    async def connect(self):
        """Establish connection to the MCP server."""
        try:
            server_params = StdioServerParameters(
                command=self._command,
                args=self._args,
                env=self._env,
            )
            stdio_transport = await self._exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            _stdio, _write = stdio_transport
            self._session = await self._exit_stack.enter_async_context(
                ClientSession(_stdio, _write)
            )
            await self._session.initialize()
            logger.info(f"Connected to MCP server: {self._command}")
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            raise

    def session(self) -> ClientSession:
        if self._session is None:
            raise ConnectionError(
                "Client session not initialized. Call connect() first."
            )
        return self._session

    async def list_tools(self) -> list[types.Tool]:
        """Return a list of tools defined by the MCP server."""
        try:
            session = self.session()
            response = await session.list_tools()
            return response.tools
        except Exception as e:
            logger.error(f"Failed to list tools: {e}")
            return []

    async def call_tool(
        self, tool_name: str, tool_input: dict
    ) -> types.CallToolResult | None:
        """Call a particular tool and return the result."""
        try:
            session = self.session()
            response = await session.call_tool(tool_name, tool_input)
            return response
        except Exception as e:
            logger.error(f"Failed to call tool {tool_name}: {e}")
            return None

    async def list_prompts(self) -> list[types.Prompt]:
        """Return a list of prompts defined by the MCP server."""
        try:
            session = self.session()
            response = await session.list_prompts()
            return response.prompts
        except Exception as e:
            logger.error(f"Failed to list prompts: {e}")
            return []

    async def get_prompt(self, prompt_name: str, args: dict[str, str]) -> list[types.PromptMessage]:
        """Get a particular prompt defined by the MCP server."""
        try:
            session = self.session()
            response = await session.get_prompt(prompt_name, args)
            return response.messages
        except Exception as e:
            logger.error(f"Failed to get prompt {prompt_name}: {e}")
            return []

    async def read_resource(self, uri: str) -> Any:
        """Read a resource, parse the contents and return it."""
        try:
            session = self.session()
            response = await session.read_resource(uri)
            return response.contents
        except Exception as e:
            logger.error(f"Failed to read resource {uri}: {e}")
            return None

    async def cleanup(self):
        """Clean up the client session and connections."""
        try:
            await self._exit_stack.aclose()
            self._session = None
            logger.info("MCP client cleaned up successfully")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()


# For testing
async def main():
    async with MCPClient(
        # If using Python without UV, update command to 'python' and remove "run" from args.
        command="uv",
        args=["run", "mcp_server.py"],
    ) as client:
        tools = await client.list_tools()
        print(f"Available tools: {[tool.name for tool in tools]}")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())
