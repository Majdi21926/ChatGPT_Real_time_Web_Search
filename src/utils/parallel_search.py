"""Anonymous Parallel Search MCP adapter for the chatbot's text-search tools."""

import asyncio
import json
from typing import List, Optional
from urllib.parse import urlsplit

import anyio
import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


MCP_URL = "https://search.parallel.ai/mcp"
USER_AGENT = (
    "ChatGPT-Real-time-Web-Search/1.0 "
    "(+https://github.com/Majdi21926/ChatGPT_Real_time_Web_Search)"
)
SEARCH_TIMEOUT = 30


def _results(response, max_results):
    if response.isError:
        raise RuntimeError("Parallel search returned an error")
    payload = response.structuredContent
    if payload is None:
        payload = json.loads("\n".join(
            block.text for block in response.content if block.type == "text"
        ))
    if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
        raise ValueError("Unexpected Parallel search response")
    results = []
    for item in payload["results"]:
        if not isinstance(item, dict):
            continue
        url = item.get("url", "")
        if not isinstance(url, str):
            continue
        try:
            parsed = urlsplit(url)
            if parsed.scheme not in ("http", "https") or not parsed.hostname:
                continue
        except ValueError:
            continue
        excerpts = item.get("excerpts", [])
        description = "\n".join(x for x in excerpts if isinstance(x, str)) if isinstance(excerpts, list) else ""
        results.append({
            "title": item.get("title") or "Untitled",
            "url": url,
            "description": description,
        })
        if len(results) >= max_results:
            break
    return results


class ParallelSearch:
    @staticmethod
    async def _search(query, max_results):
        # Bound the whole handshake and tool call, and allow cancellation to unwind
        # the SDK's transport tasks and HTTP client. Never send ambient API keys.
        with anyio.fail_after(SEARCH_TIMEOUT):
            async with httpx.AsyncClient(
                headers={"User-Agent": USER_AGENT},
                timeout=SEARCH_TIMEOUT,
                follow_redirects=True,
            ) as http_client:
                async with streamable_http_client(MCP_URL, http_client=http_client) as (read, write, _):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        response = await session.call_tool("web_search", {
                            "objective": query,
                            "search_queries": [query],
                        })
                        return _results(response, max_results)

    @staticmethod
    def retrieve_results(query: str, max_results: Optional[int] = 5) -> List:
        """Search the web with Parallel and return source URLs and excerpts."""
        if not isinstance(query, str) or not query.strip():
            raise ValueError("Search query must not be empty")
        if max_results is None:
            max_results = 5
        if type(max_results) is not int or not 1 <= max_results <= 20:
            raise ValueError("max_results must be an integer between 1 and 20")
        return asyncio.run(ParallelSearch._search(query, max_results))

    @staticmethod
    def search_text(query: str, max_results: Optional[int] = 5) -> List:
        """Search the web with Parallel and return source URLs and excerpts."""
        return ParallelSearch.retrieve_results(query, max_results)
