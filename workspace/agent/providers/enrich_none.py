from __future__ import annotations

from urllib.parse import urlparse

from workspace.agent.providers.enrich_base import ContactSuggestion, EnrichmentProvider


def _normalize_website(url_or_host: str | None) -> str:
    if not url_or_host:
        return ""
    value = url_or_host.strip()
    if not value:
        return ""
    if value.startswith(("http://", "https://")):
        return value
    return f"https://{value}"


def _host_from_url(url_or_host: str | None) -> str:
    website = _normalize_website(url_or_host)
    if not website:
        return ""
    parsed = urlparse(website)
    host = parsed.netloc.lower()
    return host[4:] if host.startswith("www.") else host


def _suggest_pattern(full_name: str, host: str) -> str:
    if not host:
        return ""
    parts = [part for part in full_name.lower().split() if part]
    if len(parts) < 2:
        return ""
    return f"{parts[0]}.{parts[-1]}@{host}"


class NoEnrichmentProvider(EnrichmentProvider):
    name = "none"
    paid = False

    def suggest_contact(
        self, full_name: str, company_website: str | None
    ) -> ContactSuggestion:
        website = _normalize_website(company_website)
        host = _host_from_url(website)
        contact_page = f"{website.rstrip('/')}/contact" if website else ""
        suggested_email = _suggest_pattern(full_name=full_name, host=host)
        return ContactSuggestion(
            company_website=website,
            contact_page_url=contact_page,
            suggested_email_pattern=suggested_email,
        )

