from __future__ import annotations

from typing import Any

from app.plugins.context import PluginSystemContext
from app.schemas.plugin import PipelineContext


_http = None


def configure(ctx: PluginSystemContext) -> None:
    global _http
    _http = ctx.http_client


def _mock_results(query: str, count: int) -> list[dict[str, str]]:
    return [
        {
            "title": f"Результат {i + 1}: {query[:50]}",
            "url": f"https://example.com/result-{i + 1}",
            "snippet": (
                f"Это демонстрационный сниппет по запросу '{query[:60]}'. "
                f"Реальный поиск настраивается через Brave Search API."
            ),
        }
        for i in range(count)
    ]


async def _brave_search(
    query: str, api_key: str, count: int,
) -> list[dict[str, str]]:
    if not _http or not api_key:
        return []
    try:
        response = await _http.get(
            "https://api.search.brave.com/res/v1/web/search",
            params={"q": query, "count": count},
            headers={
                "Accept": "application/json",
                "X-Subscription-Token": api_key,
            },
            timeout=10.0,
        )
        response.raise_for_status()
        data = response.json()
        raw = data.get("web", {}).get("results", [])
        return [
            {
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "snippet": r.get("description", ""),
            }
            for r in raw[:count]
        ]
    except Exception:
        return []


async def handle(
    ctx: PipelineContext, settings: dict[str, Any],
) -> PipelineContext:
    if not settings.get("enabled", True):
        return ctx

    provider = str(settings.get("provider", "mock"))
    count = int(settings.get("results_count", 3))
    query = ctx.prompt[:200]

    if provider == "brave":
        results = await _brave_search(
            query, str(settings.get("api_key", "")), count,
        )
    else:
        results = _mock_results(query, count)

    if not results:
        return ctx

    ctx.metadata["web_results"] = results
    ctx.metadata["web_used"] = True
    ctx.metadata["web_provider"] = provider

    web_text = "\n".join(
        f"- {r['title']} ({r['url']}): {r['snippet']}"
        for r in results
    )
    ctx.prompt = (
        f"Свежие результаты из веба:\n{web_text}\n\n"
        f"{ctx.prompt}"
    )
    return ctx