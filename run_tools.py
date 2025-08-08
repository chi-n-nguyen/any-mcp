#!/usr/bin/env python3
"""
Interactive Tool Runner - Actually run MCP tools
"""

import asyncio
import random

# Mock MCP implementations that actually work
class CalculatorMCP:
    def __init__(self):
        self.tools = ["add", "subtract", "multiply", "divide", "power", "sqrt"]
    
    async def run_tool(self, tool, *args):
        if tool == "add":
            return sum(args)
        elif tool == "subtract":
            return args[0] - sum(args[1:])
        elif tool == "multiply":
            result = 1
            for arg in args:
                result *= arg
            return result
        elif tool == "divide":
            return args[0] / args[1] if len(args) >= 2 else 0
        elif tool == "power":
            return args[0] ** args[1] if len(args) >= 2 else 0
        elif tool == "sqrt":
            return args[0] ** 0.5 if len(args) >= 1 else 0
        return 0

class DocumentMCP:
    def __init__(self):
        self.tools = ["read", "write", "list", "search", "create", "delete"]
        self.documents = {
            "readme.md": "# Welcome to Any-MCP\nThis is the readme file.",
            "config.json": '{"name": "any-mcp", "version": "1.0"}',
            "notes.txt": "Meeting notes from today..."
        }
    
    async def run_tool(self, tool, *args):
        if tool == "list":
            return list(self.documents.keys())
        elif tool == "read":
            filename = args[0] if args else "readme.md"
            return self.documents.get(filename, f"File '{filename}' not found")
        elif tool == "write":
            filename = args[0] if args else "new.txt"
            content = args[1] if len(args) > 1 else "New content"
            self.documents[filename] = content
            return f"Wrote to {filename}"
        elif tool == "create":
            filename = args[0] if args else f"doc_{random.randint(1,999)}.txt"
            content = args[1] if len(args) > 1 else "New document"
            self.documents[filename] = content
            return f"Created {filename}"
        elif tool == "search":
            query = args[0] if args else ""
            matches = [name for name, content in self.documents.items() 
                      if query.lower() in content.lower()]
            return matches
        elif tool == "delete":
            filename = args[0] if args else ""
            if filename in self.documents:
                del self.documents[filename]
                return f"Deleted {filename}"
            return f"File '{filename}' not found"
        return "Unknown operation"

class GitHubMCP:
    def __init__(self):
        self.tools = ["search_repos", "get_user", "create_issue", "list_repos", "search_users"]
    
    async def run_tool(self, tool, *args):
        if tool == "search_repos":
            query = args[0] if args else "python"
            return [f"Repo: {query}-project-{i}" for i in range(1, 4)]
        elif tool == "get_user":
            username = args[0] if args else "octocat"
            return {
                "login": username,
                "followers": random.randint(100, 10000),
                "public_repos": random.randint(10, 200)
            }
        elif tool == "create_issue":
            repo = args[0] if args else "example/repo"
            title = args[1] if len(args) > 1 else "New Issue"
            return f"Created issue '{title}' in {repo} (#42)"
        elif tool == "list_repos":
            user = args[0] if args else "octocat"
            return [f"{user}/repo-{i}" for i in range(1, 6)]
        elif tool == "search_users":
            query = args[0] if args else "developer"
            return [f"user-{query}-{i}" for i in range(1, 4)]
        return "Mock result"

async def main():
    print("🛠️  ANY-MCP INTERACTIVE TOOL RUNNER")
    print("=" * 50)
    print("Available MCPs and Tools:")
    
    # Initialize MCPs
    calc = CalculatorMCP()
    docs = DocumentMCP()
    github = GitHubMCP()
    
    mcps = {
        "calculator": calc,
        "documents": docs,  
        "github": github
    }
    
    # Show available tools
    for mcp_name, mcp in mcps.items():
        print(f"\n📦 {mcp_name.upper()}:")
        for tool in mcp.tools:
            print(f"   • {tool}")
    
    print("\n" + "=" * 50)
    print("🎯 EXAMPLES TO TRY:")
    print("calculator add 15 27")
    print("calculator multiply 6 7")
    print("documents list")
    print("documents read readme.md")
    print("github search_repos python")
    print("github get_user octocat")
    print("quit")
    print("=" * 50)
    
    while True:
        try:
            user_input = input("\n> ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if not user_input:
                continue
            
            parts = user_input.split()
            if len(parts) < 2:
                print("❌ Format: <mcp_name> <tool> [args...]")
                print("   Example: calculator add 5 3")
                continue
            
            mcp_name = parts[0].lower()
            tool = parts[1].lower()
            args = []
            
            # Parse arguments (try to convert numbers)
            for arg in parts[2:]:
                try:
                    if '.' in arg:
                        args.append(float(arg))
                    else:
                        args.append(int(arg))
                except ValueError:
                    args.append(arg)
            
            if mcp_name not in mcps:
                print(f"❌ Unknown MCP: {mcp_name}")
                print(f"   Available: {', '.join(mcps.keys())}")
                continue
            
            if tool not in mcps[mcp_name].tools:
                print(f"❌ Unknown tool: {tool}")
                print(f"   Available for {mcp_name}: {', '.join(mcps[mcp_name].tools)}")
                continue
            
            print(f"🔧 Running {mcp_name}.{tool}({', '.join(map(str, args))})")
            
            result = await mcps[mcp_name].run_tool(tool, *args)
            print(f"✅ Result: {result}")
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())