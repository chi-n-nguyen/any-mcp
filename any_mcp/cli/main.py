#!/usr/bin/env python3
"""
Any-MCP Polished CLI

Usage examples:
  # List configured MCP servers and status
  python any_mcp_cli.py list

  # Install a local MCP script and enable it
  python any_mcp_cli.py install --name docs --source local://mcp_server.py --desc "Docs demo"

  # Start a configured server, list its tools, and call a tool
  python any_mcp_cli.py start --server docs
  python any_mcp_cli.py tools --server docs
  python any_mcp_cli.py call --server docs --tool read_document --args doc_id=plan.md

  # One-shot against a script or docker image without configuration
  python any_mcp_cli.py call --script mcp_server.py --tool read_document --args doc_id=plan.md
  python any_mcp_cli.py call --docker my/mcp-image:latest --tool do_something --args key=value

  # Start chat (requires CLAUDE env vars); falls back to basic mode otherwise
  python any_mcp_cli.py chat --server docs
"""

from __future__ import annotations

import argparse
import asyncio
import os
from typing import Dict, Tuple, Any
import difflib
import re

from rich.console import Console
from rich.table import Table

from any_mcp.managers.manager import MCPManager
from any_mcp.core.client import MCPClient
from any_mcp.servers.connect_server import ServerConnector
from any_mcp.core.chat import Chat
from any_mcp.core.claude import Claude


console = Console()


def parse_kv_args(arg_string: str | None) -> Dict[str, str]:
    args: Dict[str, str] = {}
    if not arg_string:
        return args
    for pair in arg_string.split(","):
        if not pair.strip():
            continue
        if "=" not in pair:
            raise ValueError("Invalid --args format. Use key=value,key2=value2")
        k, v = pair.split("=", 1)
        args[k.strip()] = v.strip()
    return args


async def cmd_list() -> None:
    async with MCPManager() as mgr:
        status = await mgr.get_mcp_status()

    table = Table(title="Configured MCP Servers")
    table.add_column("Name")
    table.add_column("Type")
    table.add_column("Enabled")
    table.add_column("Active")
    table.add_column("Healthy")
    table.add_column("Description")

    for name, info in status.items():
        table.add_row(
            name,
            str(info.get("type", "")),
            "Yes" if info.get("enabled") else "No",
            "Yes" if info.get("active") else "No",
            "Yes" if info.get("healthy") else "No",
            info.get("description", "") or "",
        )
    console.print(table)


async def cmd_install(name: str, source: str, description: str, env_vars_list: list[str] | None) -> None:
    env_vars: Dict[str, str] = {}
    if env_vars_list:
        for pair in env_vars_list:
            if "=" in pair:
                k, v = pair.split("=", 1)
                env_vars[k] = v

    mgr = MCPManager()
    ok = mgr.installer.install_mcp(name=name, source=source, description=description, env_vars=env_vars)
    if ok:
        console.print(f"[green]Installed MCP '{name}'[/green]")
    else:
        console.print(f"[red]Failed to install MCP '{name}'[/red]")


async def ensure_started(mgr: MCPManager, server: str) -> bool:
    if server in mgr.get_active_mcps():
        return True
    return await mgr.setup_mcp(server)


async def cmd_start(server: str) -> None:
    async with MCPManager() as mgr:
        ok = await ensure_started(mgr, server)
        console.print("[green]Started[/green]" if ok else "[red]Failed[/red]")


async def cmd_stop(server: str) -> None:
    async with MCPManager() as mgr:
        ok = await mgr.stop_mcp(server)
        console.print("[green]Stopped[/green]" if ok else "[red]Failed[/red]")


async def cmd_tools(server: str) -> None:
    async with MCPManager() as mgr:
        await ensure_started(mgr, server)
        tools = await mgr.list_mcp_tools(server)

    table = Table(title=f"Tools for '{server}'")
    table.add_column("Name")
    table.add_column("Description")
    table.add_column("Input Schema (json)")
    for t in tools:
        schema = getattr(t, "inputSchema", None)
        schema_str = "" if schema is None else str(schema)
        table.add_row(t.name, t.description or "", schema_str)
    console.print(table)


async def cmd_call_server(server: str, tool: str, arg_string: str | None) -> None:
    args = parse_kv_args(arg_string)
    async with MCPManager() as mgr:
        await ensure_started(mgr, server)
        result = await mgr.call_mcp(server, tool, args)
        if result is None:
            console.print("[red]Tool call failed[/red]")
            return
        console.print(f"[green]Success[/green]: {result}")


async def cmd_call_script(script: str, tool: str, arg_string: str | None) -> None:
    args = parse_kv_args(arg_string)
    use_uv = os.getenv("USE_UV", "0") == "1"
    command, script_args = ("uv", ["run", script]) if use_uv else ("python", [script])
    async with MCPClient(command=command, args=script_args) as client:
        result = await client.call_tool(tool, args)
        if result is None:
            console.print("[red]Tool call failed[/red]")
            return
        console.print(f"[green]Success[/green]: {result}")


async def cmd_call_docker(image: str, tool: str, arg_string: str | None, env_list: list[str] | None) -> None:
    args = parse_kv_args(arg_string)
    env = os.environ.copy()
    if env_list:
        for pair in env_list:
            if "=" in pair:
                k, v = pair.split("=", 1)
                env[k] = v
    docker_args = [
        "run",
        "-i",
        "--rm",
        *([item for k, v in [(e.split("=", 1)[0], e.split("=", 1)[1]) for e in env_list] for item in ("-e", f"{k}={v}")] if env_list else []),
        image,
    ]
    async with MCPClient(command="docker", args=docker_args, env=env) as client:
        result = await client.call_tool(tool, args)
        if result is None:
            console.print("[red]Tool call failed[/red]")
            return
        console.print(f"[green]Success[/green]: {result}")


async def cmd_chat(server: str | None, script: str | None, docker: str | None, env_list: list[str] | None) -> None:
    connector = ServerConnector()
    from contextlib import AsyncExitStack

    async with AsyncExitStack() as stack:
        if server:
            await stack.enter_async_context(connector.manager)
            ok = await connector.connect_to_configured_server(server)
            if not ok:
                console.print("[red]Failed to connect to server[/red]")
                return
        elif script:
            ok = await connector.connect_to_script(script)
            if not ok:
                console.print("[red]Failed to connect to script[/red]")
                return
            await stack.enter_async_context(connector.client)  # type: ignore[arg-type]
        elif docker:
            env_vars: Dict[str, str] = {}
            if env_list:
                for pair in env_list:
                    if "=" in pair:
                        k, v = pair.split("=", 1)
                        env_vars[k] = v
            ok = await connector.connect_to_docker(docker, env_vars)
            if not ok:
                console.print("[red]Failed to connect to docker image[/red]")
                return
            await stack.enter_async_context(connector.client)  # type: ignore[arg-type]
        else:
            console.print("[red]Specify one of --server/--script/--docker[/red]")
            return

        await connector.start_interactive_session()


def _extract_kv_from_text(text: str) -> Dict[str, str]:
    # very light heuristic: parse key=value pairs in NL
    pairs = re.findall(r"(\b[a-zA-Z_][a-zA-Z0-9_]*\b)\s*=\s*([^,;]+)", text)
    return {k: v.strip().strip('"\'') for k, v in pairs}


def _best_tool_match(tools: list, query: str) -> Tuple[str | None, float]:
    query_l = query.lower()
    tokens = [w for w in re.findall(r"[a-zA-Z_]+", query_l) if len(w) > 2]

    # verb hints
    verb_boost: Dict[str, float] = {}
    if any(v in tokens for v in ["read", "get", "show", "fetch", "list", "view", "open"]):
        verb_boost["read"] = 0.2
        verb_boost["list"] = 0.15
    if any(v in tokens for v in ["edit", "update", "write", "set", "change", "modify"]):
        verb_boost["edit"] = 0.2

    def score_tool(name: str) -> float:
        name_l = name.lower()
        base = difflib.SequenceMatcher(None, query_l, name_l).ratio()
        token_best = 0.0
        starts_bonus = 0.0
        for t in tokens:
            r = difflib.SequenceMatcher(None, t, name_l).ratio()
            if r > token_best:
                token_best = r
            if name_l.startswith(t):
                starts_bonus = max(starts_bonus, 0.15)

        # verb-based boost mapped to tool name substrings
        vbonus = 0.0
        if "read" in name_l:
            vbonus += verb_boost.get("read", 0.0)
            vbonus += verb_boost.get("list", 0.0)
        if any(k in name_l for k in ["edit", "write", "update"]):
            vbonus += verb_boost.get("edit", 0.0)

        return 0.5 * base + 0.5 * token_best + starts_bonus + vbonus

    best_name = None
    best_score = -1.0
    for t in tools:
        s = score_tool(t.name)
        if s > best_score:
            best_name = t.name
            best_score = s
    return best_name, best_score


async def _connect_ephemeral(script: str | None, docker: str | None, env_list: list[str] | None,
                            module: str | None = None, module_args: list[str] | None = None) -> MCPClient:
    if module:
        # Run a Python module via -m
        cmd = "python"
        args = ["-m", module]
        if module_args:
            args += module_args
        client = MCPClient(command=cmd, args=args)
        await client.connect()
        return client
    elif script:
        use_uv = os.getenv("USE_UV", "0") == "1"
        command, script_args = ("uv", ["run", script]) if use_uv else ("python", [script])
        client = MCPClient(command=command, args=script_args)
        await client.connect()
        return client
    else:
        env = os.environ.copy()
        if env_list:
            for pair in env_list:
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    env[k] = v
        docker_args = ["run", "-i", "--rm"]
        if env_list:
            for pair in env_list:
                if "=" in pair:
                    docker_args += ["-e", pair]
        docker_args.append(docker)  # type: ignore[arg-type]
        client = MCPClient(command="docker", args=docker_args, env=env)
        await client.connect()
        return client


async def cmd_nl(server: str | None, script: str | None, docker: str | None, query: str, env_list: list[str] | None,
                 module: str | None = None, module_args: list[str] | None = None) -> None:
    """One-shot NL → tool call. If Claude env is present, we will still perform fuzzy match first.
    If no good match is found and Claude is configured, we can later route via LLM (future).
    """
    if server:
        async with MCPManager() as mgr:
            await ensure_started(mgr, server)
            tools = await mgr.list_mcp_tools(server)
            tool_name, score = _best_tool_match(tools, query)
            if not tool_name or score < 0.5:
                console.print("[red]Could not infer tool from query[/red]")
                return
            # extract arguments heuristically
            args = _extract_kv_from_text(query)
            result = await mgr.call_mcp(server, tool_name, args)
            if result is None:
                console.print("[red]Tool call failed[/red]")
            else:
                console.print(f"[green]Success[/green]: {result}")
    else:
        # ephemeral client for script/docker
        client = await _connect_ephemeral(script, docker, env_list, module=module, module_args=module_args)
        try:
            tools = await client.list_tools()
            tool_name, score = _best_tool_match(tools, query)
            if not tool_name or score < 0.5:
                console.print("[red]Could not infer tool from query[/red]")
                return
            args = _extract_kv_from_text(query)
            result = await client.call_tool(tool_name, args)
            if result is None:
                console.print("[red]Tool call failed[/red]")
            else:
                console.print(f"[green]Success[/green]: {result}")
        finally:
            await client.cleanup()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="any-mcp-cli", description="Polished CLI for Any-MCP")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="List configured MCP servers")

    p_install = sub.add_parser("install", help="Install an MCP (docker or local)")
    p_install.add_argument("--name", required=True)
    p_install.add_argument("--source", required=True, help="docker://image or local://path")
    p_install.add_argument("--desc", default="")
    p_install.add_argument("--env", action="append", help="KEY=VALUE", default=None)

    p_start = sub.add_parser("start", help="Start a configured MCP server")
    p_start.add_argument("--server", required=True)

    p_stop = sub.add_parser("stop", help="Stop a configured MCP server")
    p_stop.add_argument("--server", required=True)

    p_tools = sub.add_parser("tools", help="List tools for a server")
    p_tools.add_argument("--server", required=True)

    p_call = sub.add_parser("call", help="Call a tool (server/script/docker)")
    target = p_call.add_mutually_exclusive_group(required=True)
    target.add_argument("--server")
    target.add_argument("--script")
    target.add_argument("--docker")
    target.add_argument("--module")
    p_call.add_argument("--tool", required=True)
    p_call.add_argument("--args", help="key=value,key2=value2")
    p_call.add_argument("--env", action="append", help="KEY=VALUE for docker", default=None)
    p_call.add_argument("--module-args", help="Extra args for --module, space-separated string", default=None)

    p_chat = sub.add_parser("chat", help="Interactive chat with a server (Claude optional)")
    target2 = p_chat.add_mutually_exclusive_group(required=True)
    target2.add_argument("--server")
    target2.add_argument("--script")
    target2.add_argument("--docker")
    target2.add_argument("--module")
    p_chat.add_argument("--env", action="append", help="KEY=VALUE for docker", default=None)
    p_chat.add_argument("--module-args", help="Extra args for --module, space-separated string", default=None)

    p_nl = sub.add_parser("nl", help="One-shot natural language command → tool call")
    trg = p_nl.add_mutually_exclusive_group(required=True)
    trg.add_argument("--server")
    trg.add_argument("--script")
    trg.add_argument("--docker")
    trg.add_argument("--module")
    p_nl.add_argument("--query", required=True, help="Natural language instruction")
    p_nl.add_argument("--env", action="append", help="KEY=VALUE for docker", default=None)
    p_nl.add_argument("--module-args", help="Extra args for --module, space-separated string", default=None)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.cmd == "list":
        asyncio.run(cmd_list())
        return
    if args.cmd == "install":
        asyncio.run(cmd_install(args.name, args.source, args.desc, args.env))
        return
    if args.cmd == "start":
        asyncio.run(cmd_start(args.server))
        return
    if args.cmd == "stop":
        asyncio.run(cmd_stop(args.server))
        return
    if args.cmd == "tools":
        asyncio.run(cmd_tools(args.server))
        return
    if args.cmd == "call":
        if args.server:
            asyncio.run(cmd_call_server(args.server, args.tool, args.args))
            return
        if args.script:
            asyncio.run(cmd_call_script(args.script, args.tool, args.args))
            return
        if args.module:
            mod_args = args.module_args.split() if args.module_args else []
            # Reuse NL path internals for ephemeral module call by crafting a simple query 'tool=...'
            q = f"{args.tool} " + (" ".join([f"{k}={v}" for k,v in parse_kv_args(args.args).items()]) if args.args else "")
            asyncio.run(cmd_nl(None, None, None, q, None, module=args.module, module_args=mod_args))
            return
        if args.docker:
            asyncio.run(cmd_call_docker(args.docker, args.tool, args.args, args.env))
            return
    if args.cmd == "chat":
        # Note: current chat path does not support module directly; fallback by script/module ephemeral client via connect_server if needed later
        asyncio.run(cmd_chat(args.server, args.script, args.docker, args.env))
        return
    if args.cmd == "nl":
        mod_args = args.module_args.split() if getattr(args, "module_args", None) else []
        asyncio.run(cmd_nl(args.server, args.script, args.docker, args.query, args.env, module=getattr(args, "module", None), module_args=mod_args))
        return


if __name__ == "__main__":
    main()

