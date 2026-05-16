import os
import httpx


async def tavily_search(query: str, max_results: int = 5) -> str:
    """Search the web using Tavily and return a text summary of results."""
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return "Web search unavailable: TAVILY_API_KEY not set."

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.tavily.com/search",
            json={"api_key": api_key, "query": query, "max_results": max_results},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

    results = data.get("results", [])
    if not results:
        return "No results found."

    lines = []
    for r in results:
        lines.append(f"**{r['title']}**\n{r['url']}\n{r.get('content', '')[:300]}\n")
    return "\n".join(lines)
