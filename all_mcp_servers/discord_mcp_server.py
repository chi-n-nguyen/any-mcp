#!/usr/bin/env python3
"""
Test file for DiscordMCPClient Python module
"""

import asyncio
from discord_mcp_server.src.index import DiscordMCPClient


async def test_read_messages(client):
    """Test reading messages from general chat"""
    try:
        messages = await client.readMessages({
            "channel": "general",
            "limit": 5
        })
        print(f"📖 Read {len(messages)} messages from #general:")
        for msg in messages:
            print(f"  {msg['author']}: {msg['content'][:50]}...")
        return True
    except Exception as e:
        print(f"❌ Error reading messages: {e}")
        return False


async def test_discord_client():
    """Test the DiscordMCPClient functionality"""
    client = None
    try:
        # Create a new DiscordMCPClient instance
        client = DiscordMCPClient()
        
        # Start the bot in the background
        bot_task = asyncio.create_task(client.login(client.token))
        
        # Wait for the bot to be ready (similar to TypeScript version)
        print("Waiting for Discord bot to be ready...")
        while not client.isReady():
            await asyncio.sleep(0.5)
        
        print('✅ Discord client is ready!')
        
        # Get available guilds
        guilds = client.getGuilds()
        print(f'Available guilds: {guilds}')
        
        # Test reading messages
        await test_read_messages(client)
        
        print("✅ Test completed successfully!")
        
    except Exception as error:
        print(f'❌ Error testing Discord client: {error}')
    finally:
        # Clean up
        if client:
            await client.client.close()
            # Cancel the bot task
            if 'bot_task' in locals():
                bot_task.cancel()
                try:
                    await bot_task
                except asyncio.CancelledError:
                    pass


# Run the test
if __name__ == "__main__":
    asyncio.run(test_discord_client())
