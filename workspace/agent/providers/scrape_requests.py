from __future__ import annotations

import re

import requests
from bs4 import BeautifulSoup
from trafilatura import extract

from workspace.agent.providers.scrape_base import ScrapeProvider, ScrapedPage

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36"
    )
}


class RequestsScrapeProvider(ScrapeProvider):
    name = "requests"

    def __init__(self, timeout_seconds: float = 15.0) -> None:
        self.timeout_seconds = timeout_seconds

    def scrape(self, url: str) -> ScrapedPage:
        response = requests.get(
            url, timeout=self.timeout_seconds, headers=DEFAULT_HEADERS
        )
        response.raise_for_status()
        html = response.text

        content = extract(
            html,
            url=url,
            include_comments=False,
            include_tables=False,
            favor_precision=True,
        )
        if not content:
            soup = BeautifulSoup(html, "lxml")
            for tag in soup(["script", "style", "noscript"]):
                tag.decompose()
            content = " ".join(soup.stripped_strings)

        soup = BeautifulSoup(html, "lxml")
        title = ""
        if soup.title and soup.title.string:
            title = soup.title.string.strip()

        text = re.sub(r"\s+", " ", content or "").strip()
        return ScrapedPage(
            url=url,
            title=title,
            text=text[:20000],
            status_code=response.status_code,
        )

