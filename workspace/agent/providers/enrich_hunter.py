from __future__ import annotations

import time

import requests

from workspace.agent.providers.enrich_base import ContactSuggestion, EnrichmentProvider
from workspace.agent.providers.enrich_none import (
    _host_from_url,
    _normalize_website,
    _suggest_pattern,
)

HUNTER_EMAIL_FINDER_URL = "https://api.hunter.io/v2/email-finder"


class HunterEnrichmentProvider(EnrichmentProvider):
    name = "hunter"
    paid = True

    def __init__(self, api_key: str, interval_seconds: float = 5.0) -> None:
        self._api_key = api_key
        self._interval_seconds = interval_seconds
        self._last_call: float = 0.0

    def suggest_contact(
        self, full_name: str, company_website: str | None
    ) -> ContactSuggestion:
        website = _normalize_website(company_website)
        host = _host_from_url(website)
        contact_page = f"{website.rstrip('/')}/contact" if website else ""
        suggested_email = _suggest_pattern(full_name=full_name, host=host)

        if not host:
            return ContactSuggestion(
                company_website=website,
                contact_page_url=contact_page,
                suggested_email_pattern=suggested_email,
                email="",
                phone="",
            )

        elapsed = time.monotonic() - self._last_call
        if elapsed < self._interval_seconds:
            time.sleep(self._interval_seconds - elapsed)

        try:
            self._last_call = time.monotonic()
            response = requests.get(
                HUNTER_EMAIL_FINDER_URL,
                params={
                    "full_name": full_name,
                    "domain": host,
                    "api_key": self._api_key,
                },
                timeout=15,
            )
            if response.status_code == 200:
                data = response.json().get("data") or {}
                email = data.get("email") or ""
                return ContactSuggestion(
                    company_website=website,
                    contact_page_url=contact_page,
                    suggested_email_pattern=suggested_email,
                    email=email,
                    phone="",  # Hunter does not provide phone numbers
                )
        except Exception:
            pass

        return ContactSuggestion(
            company_website=website,
            contact_page_url=contact_page,
            suggested_email_pattern=suggested_email,
            email="",
            phone="",
        )
