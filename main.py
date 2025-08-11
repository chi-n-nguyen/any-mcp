#!/usr/bin/env python3
"""
Entry point for the any-mcp application.
"""

import sys
import asyncio
from any_mcp.main import main

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())