from __future__ import annotations

import requests

from workspace.agent.providers.search_base import SearchProvider, SearchResult

BRAVE_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"


class BraveSearchProvider(SearchProvider):
    name = "brave"
    paid = True

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        try:
            resp = requests.get(
                BRAVE_SEARCH_URL,
                headers={
                    "Accept": "application/json",
                    "Accept-Encoding": "gzip",
                    "X-Subscription-Token": self.api_key,
                },
                params={"q": query, "count": max_results},
                timeout=10,
            )
            resp.raise_for_status()
        except Exception:
            return []

        results: list[SearchResult] = []
        for rank, item in enumerate(
            resp.json().get("web", {}).get("results", []), start=1
        ):
            url = item.get("url", "").strip()
            if not url:
                continue
            results.append(
                SearchResult(
                    title=item.get("title", "").strip(),
                    url=url,
                    snippet=item.get("description", "").strip(),
                    rank=rank,
                )
            )
        return results
