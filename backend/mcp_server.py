"""
DevMind MCP Server — exposes the same tools via the Model Context Protocol.
Run: python mcp_server.py
Connect via MCP Inspector or Claude Desktop.
"""
import asyncio
from dotenv import load_dotenv
load_dotenv()

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types
from app.tools.github import fetch_repo_summary, fetch_file_content
from app.tools.web import tavily_search
from app.tools.files import read_file, list_files

server = Server("devmind")


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="fetch_github_repo",
            description="Get a summary of a GitHub repository.",
            inputSchema={
                "type": "object",
                "properties": {"repo": {"type": "string"}},
                "required": ["repo"],
            },
        ),
        types.Tool(
            name="fetch_github_file",
            description="Read a file from a GitHub repository.",
            inputSchema={
                "type": "object",
                "properties": {
                    "repo": {"type": "string"},
                    "path": {"type": "string"},
                },
                "required": ["repo", "path"],
            },
        ),
        types.Tool(
            name="search_web",
            description="Search the web for up-to-date information.",
            inputSchema={
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        ),
        types.Tool(
            name="read_file",
            description="Read a local file.",
            inputSchema={
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
        ),
        types.Tool(
            name="list_files",
            description="List files in a local directory.",
            inputSchema={
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": [],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "fetch_github_repo":
        result = fetch_repo_summary(arguments["repo"])
    elif name == "fetch_github_file":
        result = fetch_file_content(arguments["repo"], arguments["path"])
    elif name == "search_web":
        result = await tavily_search(arguments["query"])
    elif name == "read_file":
        result = read_file(arguments["path"])
    elif name == "list_files":
        result = list_files(arguments.get("path", "."))
    else:
        result = f"Unknown tool: {name}"

    return [types.TextContent(type="text", text=result)]


if __name__ == "__main__":
    asyncio.run(stdio_server(server))
