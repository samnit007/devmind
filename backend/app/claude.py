import json
import os
from typing import AsyncIterator
import anthropic
from app.tools.github import fetch_repo_summary, fetch_file_content
from app.tools.web import tavily_search
from app.tools.files import read_file, list_files

MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")

TOOLS: list[anthropic.types.ToolParam] = [
    {
        "name": "fetch_github_repo",
        "description": "Get a summary of a GitHub repository: description, languages, files, open issues.",
        "input_schema": {
            "type": "object",
            "properties": {
                "repo": {"type": "string", "description": "Full repo name e.g. 'samnit007/devmind'"}
            },
            "required": ["repo"],
        },
    },
    {
        "name": "fetch_github_file",
        "description": "Read the content of a specific file in a GitHub repository.",
        "input_schema": {
            "type": "object",
            "properties": {
                "repo": {"type": "string", "description": "Full repo name e.g. 'samnit007/devmind'"},
                "path": {"type": "string", "description": "File path within the repo e.g. 'README.md'"},
            },
            "required": ["repo", "path"],
        },
    },
    {
        "name": "search_web",
        "description": "Search the web for up-to-date information on any topic.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"}
            },
            "required": ["query"],
        },
    },
    {
        "name": "read_file",
        "description": "Read a local file by relative path.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Relative file path"}
            },
            "required": ["path"],
        },
    },
    {
        "name": "list_files",
        "description": "List files and directories at a local path.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Relative directory path (default '.')"}
            },
            "required": [],
        },
    },
]

SYSTEM = """You are DevMind, an AI assistant for software developers.
You have access to tools: fetch GitHub repos/files, search the web, and read local files.
Use tools whenever they'd give a better answer. Be concise, technical, and direct.
When you use a tool, briefly say what you're doing before the result."""


async def _run_tool(name: str, inputs: dict) -> str:
    if name == "fetch_github_repo":
        return fetch_repo_summary(inputs["repo"])
    if name == "fetch_github_file":
        return fetch_file_content(inputs["repo"], inputs["path"])
    if name == "search_web":
        return await tavily_search(inputs["query"])
    if name == "read_file":
        return read_file(inputs["path"])
    if name == "list_files":
        return list_files(inputs.get("path", "."))
    return f"Unknown tool: {name}"


async def stream_response(
    messages: list[dict],
) -> AsyncIterator[str]:
    """Yield SSE-formatted strings for the frontend."""
    client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    history = list(messages)

    while True:
        async with client.messages.stream(
            model=MODEL,
            max_tokens=4096,
            system=SYSTEM,
            tools=TOOLS,
            messages=history,
        ) as stream:
            tool_calls: list[dict] = []
            current_text = ""

            async for event in stream:
                if event.type == "content_block_start":
                    if event.content_block.type == "tool_use":
                        tool_calls.append({
                            "id": event.content_block.id,
                            "name": event.content_block.name,
                            "input_json": "",
                        })
                        yield f"data: {{\"type\":\"tool_start\",\"name\":\"{event.content_block.name}\"}}\n\n"

                elif event.type == "content_block_delta":
                    delta = event.delta
                    if delta.type == "text_delta":
                        current_text += delta.text
                        text = delta.text.replace('"', '\\"').replace("\n", "\\n")
                        yield f'data: {{"type":"text","delta":"{text}"}}\n\n'
                    elif delta.type == "input_json_delta" and tool_calls:
                        tool_calls[-1]["input_json"] += delta.partial_json

            final = await stream.get_final_message()
            stop_reason = final.stop_reason

            if stop_reason != "tool_use" or not tool_calls:
                yield 'data: {"type":"done"}\n\n'
                return

            # Build assistant message with all content blocks
            history.append({"role": "assistant", "content": final.content})

            # Execute all tool calls
            tool_results = []
            for tc in tool_calls:
                try:
                    inputs = json.loads(tc["input_json"] or "{}")
                except json.JSONDecodeError:
                    inputs = {}
                result = await _run_tool(tc["name"], inputs)
                yield f"data: {{\"type\":\"tool_done\",\"name\":\"{tc['name']}\"}}\n\n"
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tc["id"],
                    "content": result,
                })

            history.append({"role": "user", "content": tool_results})
