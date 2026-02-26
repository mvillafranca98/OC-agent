from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(slots=True)
class ScrapedPage:
    url: str
    title: str
    text: str
    status_code: int


class ScrapeProvider(ABC):
    name: str

    @abstractmethod
    def scrape(self, url: str) -> ScrapedPage:
        raise NotImplementedError

