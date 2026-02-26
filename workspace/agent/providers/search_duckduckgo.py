from __future__ import annotations

from workspace.agent.providers.search_base import SearchProvider, SearchResult

try:
    from duckduckgo_search import DDGS
except ImportError:  # pragma: no cover - depends on optional install state
    DDGS = None


class DuckDuckGoSearchProvider(SearchProvider):
    name = "duckduckgo"
    paid = False

    def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        if DDGS is None:
            raise RuntimeError(
                "duckduckgo_search is not installed. Install dependencies first."
            )

        results: list[SearchResult] = []
        with DDGS() as ddgs:
            rows = ddgs.text(query, max_results=max_results)
            for rank, row in enumerate(rows, start=1):
                url = row.get("href") or row.get("url") or ""
                if not url:
                    continue
                title = row.get("title", "").strip()
                snippet = row.get("body", "").strip()
                results.append(
                    SearchResult(title=title, url=url, snippet=snippet, rank=rank)
                )
        return results

