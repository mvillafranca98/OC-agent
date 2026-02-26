from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(slots=True)
class ContactSuggestion:
    company_website: str
    contact_page_url: str
    suggested_email_pattern: str
    email: str = ""
    phone: str = ""


class EnrichmentProvider(ABC):
    name: str
    paid: bool = False

    @abstractmethod
    def suggest_contact(self, full_name: str, company_website: str | None) -> ContactSuggestion:
        raise NotImplementedError

