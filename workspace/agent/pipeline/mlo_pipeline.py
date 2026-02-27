from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
from loguru import logger

from workspace.agent.config import AgentSettings
from workspace.agent.guardrails import MinIntervalLimiter, RateLimitStats, SearchBatchLimiter
from workspace.agent.pipeline.common import PipelineRun
from workspace.agent.providers.enrich_base import EnrichmentProvider
from workspace.agent.providers.enrich_none import NoEnrichmentProvider
from workspace.agent.providers.scrape_base import ScrapeProvider
from workspace.agent.providers.search_base import SearchProvider, SearchResult
from workspace.agent.scoring.score_mlo import score_mlo
from workspace.agent.storage.store_csv import CSVStore

MLO_REQUIRED_COLUMNS = {
    "full_name",
    "nmls_id",
    "current_company",
    "current_title",
    "location",
}

MLO_SIGNAL_KEYWORDS: dict[str, list[str]] = {
    "open_to_work": [
        "open to work",
        "open for work",
        "seeking new opportunities",
        "actively looking",
        "looking for opportunities",
    ],
    "company_turmoil": ["layoff", "restructure", "bankruptcy", "shutdown", "turmoil"],
    "branch_closure_proximity": ["branch closure", "office closure", "closed branch"],
    "compensation_complaints": [
        "commission cut",
        "pay cut",
        "lower split",
        "compensation",
    ],
    "team_departures": ["left the company", "departed", "resigned", "turnover"],
    "profile_changes": ["updated profile", "new role", "changed title"],
    "recruiter_engagement": ["recruiter", "headhunter", "hiring manager"],
}

# Domains that are never a mortgage company's own site.
NON_COMPANY_DOMAINS: frozenset[str] = frozenset({
    "zhihu.com", "whatsapp.com", "facebook.com", "twitter.com", "x.com",
    "instagram.com", "youtube.com", "reddit.com", "wikipedia.org",
    "indeed.com", "glassdoor.com", "yelp.com", "google.com",
    "housingwire.com", "scotsmanguide.com", "nationalmortgageprofessional.com",
    "nmlsconsumeraccess.org", "zillow.com", "realtor.com", "trulia.com",
    "bloomberg.com", "wsj.com", "reuters.com", "businesswire.com",
    "prnewswire.com", "microsoft.com", "apple.com", "amazon.com",
})

# Known company → domain mapping so Hunter hits the right address.
KNOWN_COMPANY_DOMAINS: dict[str, str] = {
    "american financial network": "afncorp.com",
    "american pacific mortgage": "apmortgage.com",
    "caliber home loans": "caliberhomeloans.com",
    "capital mortgage services": "capitalmortgageservices.com",
    "crosscountry mortgage": "crosscountrymortgage.com",
    "fairway": "fairwayindependentmortgage.com",
    "finance of america": "financeofamerica.com",
    "guild mortgage": "guildmortgage.com",
    "guaranteed rate": "rate.com",
    "loandepot": "loandepot.com",
    "movement mortgage": "movement.com",
    "new american funding": "newamericanfunding.com",
    "pennymac": "pennymac.com",
    "planet home lending": "planethomelendinginc.com",
    "prmg": "prmg.net",
    "paramount residential mortgage group": "prmg.net",
    "rate": "rate.com",
    "ufg": "ufg.com",
    "united wholesale mortgage": "uwm.com",
    "uwm": "uwm.com",
}

INTENT_ROLE_TERMS = '"mortgage OR "loan officer" OR "mortgage loan originator" OR MLO'
INTENT_QUERY_TERMS = (
    '"open to work" OR "open for business" OR "actively looking" OR '
    '"seeking opportunities" OR "open for opportunities"'
)

COMPANY_TOKEN_STOPWORDS = {
    "inc",
    "llc",
    "ltd",
    "co",
    "corp",
    "corporation",
    "group",
    "services",
    "financial",
    "mortgage",
    "home",
    "loan",
    "loans",
}


@dataclass(slots=True)
class IntentRule:
    phrase: str
    signal: str
    confidence: float


@dataclass(slots=True)
class IntentMatch:
    signal: str
    phrase: str
    source_url: str
    confidence: float


INTENT_RULES = [
    IntentRule("open to work", "open_to_work", 1.0),
    IntentRule("open for opportunities", "open_to_work", 0.95),
    IntentRule("seeking opportunities", "open_to_work", 0.9),
    IntentRule("actively looking", "open_to_work", 0.9),
    IntentRule("open for business", "open_for_business", 0.85),
    IntentRule("available for business", "open_for_business", 0.8),
]


def _keyword_confidence(corpus: str, phrases: list[str]) -> float:
    match_count = sum(corpus.count(phrase) for phrase in phrases)
    if match_count >= 2:
        return 0.7
    if match_count == 1:
        return 0.4
    return 0.0


def _clean_text(raw: str) -> str:
    return re.sub(r"\s+", " ", raw.lower()).strip()


def _build_queries(row: dict[str, object], max_variants: int) -> list[str]:
    full_name = str(row.get("full_name", "")).strip()
    company = str(row.get("current_company", "")).strip()
    location = str(row.get("location", "")).strip()

    query_candidates = [
        # Simple baseline: works reliably with DuckDuckGo and returns real evidence
        f"{full_name} {company} mortgage loan officer {location}",
        # LinkedIn profile lookup: second query dedicated to finding the profile URL
        f'"{full_name}" "{company}" site:linkedin.com',
        # Fallback without site restriction if LinkedIn query returns nothing
        f"{full_name} mortgage loan officer linkedin {location}",
    ]

    deduped: list[str] = []
    seen: set[str] = set()
    for candidate in query_candidates:
        query = " ".join(candidate.split())
        if not query or query in seen:
            continue
        seen.add(query)
        deduped.append(query)
        if len(deduped) >= max_variants:
            break
    return deduped


def _tokenize_company(company: str) -> set[str]:
    tokens = {
        token
        for token in re.findall(r"[a-z0-9]+", company.lower())
        if len(token) > 2 and token not in COMPANY_TOKEN_STOPWORDS
    }
    return tokens


def _normalized_host(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    return host


def _company_site_from_results(results: list[SearchResult], company: str) -> str:
    # Check known domain lookup first — most reliable.
    company_key = company.lower().strip()
    for key, domain in KNOWN_COMPANY_DOMAINS.items():
        if key in company_key or company_key in key:
            return f"https://{domain}"

    company_tokens = _tokenize_company(company)
    best_url = ""
    best_score = float("-inf")

    for item in results:
        host = _normalized_host(item.url)
        if not host or "linkedin.com" in host:
            continue
        # Skip obviously non-company domains.
        base = ".".join(host.split(".")[-2:]) if host.count(".") >= 1 else host
        if base in NON_COMPANY_DOMAINS:
            continue

        host_text = host.replace(".", " ").replace("-", " ")
        overlap = sum(1 for token in company_tokens if token in host_text)
        rank_boost = max(0.0, (6 - item.rank) * 0.1)
        score = overlap * 2 + rank_boost

        if score > best_score:
            parsed = urlparse(item.url)
            best_url = f"{parsed.scheme or 'https'}://{host}"
            best_score = score

    if best_url:
        return best_url

    for item in results:
        host = _normalized_host(item.url)
        if not host or "linkedin.com" in host:
            continue
        base = ".".join(host.split(".")[-2:]) if host.count(".") >= 1 else host
        if base in NON_COMPANY_DOMAINS:
            continue
        parsed = urlparse(item.url)
        return f"{parsed.scheme or 'https'}://{host}"
    return ""


def _linkedin_url(results: list[SearchResult]) -> str:
    for item in results:
        if "linkedin.com/in/" in item.url:
            return item.url
    return ""


def _best_intent_match(
    current: IntentMatch | None, candidate: IntentMatch | None
) -> IntentMatch | None:
    if candidate is None:
        return current
    if current is None:
        return candidate
    if candidate.confidence > current.confidence:
        return candidate
    return current


def _match_intent_for_text(text: str, source_url: str) -> IntentMatch | None:
    normalized = _clean_text(text)
    if not normalized:
        return None

    is_linkedin_profile = "linkedin.com/in/" in source_url
    for rule in INTENT_RULES:
        if rule.phrase in normalized:
            confidence = rule.confidence
            if not is_linkedin_profile:
                confidence = max(0.4, confidence - 0.25)
            return IntentMatch(
                signal=rule.signal,
                phrase=rule.phrase,
                source_url=source_url,
                confidence=round(confidence, 2),
            )
    return None


def _detect_intent(
    results: list[SearchResult], scraped_pages: dict[str, str]
) -> IntentMatch | None:
    best: IntentMatch | None = None

    for result in results:
        snippet_text = f"{result.title} {result.snippet}"
        candidate = _match_intent_for_text(snippet_text, result.url)
        best = _best_intent_match(best, candidate)

    for source_url, page_text in scraped_pages.items():
        candidate = _match_intent_for_text(page_text, source_url)
        best = _best_intent_match(best, candidate)

    return best


def _infer_confidence(
    results: list[SearchResult],
    scraped_text: str,
    intent_match: IntentMatch | None,
) -> dict[str, float]:
    snippets = " ".join(result.snippet for result in results).lower()
    corpus = f"{snippets} {scraped_text}".lower()

    confidence: dict[str, float] = {}
    for signal_name, keywords in MLO_SIGNAL_KEYWORDS.items():
        confidence[signal_name] = _keyword_confidence(corpus, keywords)

    if len(results) >= 8:
        confidence["posting_frequency"] = 0.8
    elif len(results) >= 5:
        confidence["posting_frequency"] = 0.7
    elif len(results) >= 3:
        confidence["posting_frequency"] = 0.4
    else:
        confidence["posting_frequency"] = 0.2

    if intent_match:
        if intent_match.signal == "open_to_work":
            confidence["open_to_work"] = max(
                confidence.get("open_to_work", 0.0),
                intent_match.confidence,
            )
        elif intent_match.signal == "open_for_business":
            confidence["open_to_work"] = max(
                confidence.get("open_to_work", 0.0),
                max(0.65, intent_match.confidence - 0.1),
            )
            confidence["profile_changes"] = max(
                confidence.get("profile_changes", 0.0), 0.4
            )

    return confidence


def _dedupe_results(
    existing: list[SearchResult], incoming: list[SearchResult]
) -> list[SearchResult]:
    seen = {result.url for result in existing}
    merged = list(existing)
    for result in incoming:
        if result.url in seen:
            continue
        seen.add(result.url)
        merged.append(result)
    return merged


class MLOPipeline:
    def __init__(
        self,
        settings: AgentSettings,
        search_provider: SearchProvider,
        scrape_provider: ScrapeProvider,
        enrichment_provider: EnrichmentProvider,
        csv_store: CSVStore,
    ) -> None:
        self.settings = settings
        self.search_provider = search_provider
        self.scrape_provider = scrape_provider
        self.enrichment_provider = enrichment_provider
        self.no_enrichment_provider = NoEnrichmentProvider()
        self.csv_store = csv_store

        self.search_limiter = MinIntervalLimiter(settings.search_interval_seconds)
        self.scrape_limiter = MinIntervalLimiter(settings.search_interval_seconds)
        self.batch_limiter = SearchBatchLimiter(
            max_per_batch=settings.max_searches_per_batch,
            cooldown_seconds=settings.batch_cooldown_seconds,
        )

    def run(
        self,
        input_csv: Path,
        run_date: date,
        output_dir: Path,
        limit: int | None = None,
        target_complete: int | None = None,
    ) -> PipelineRun:
        frame = pd.read_csv(input_csv)
        missing = sorted(MLO_REQUIRED_COLUMNS - set(frame.columns))
        if missing:
            missing_text = ", ".join(missing)
            raise ValueError(f"Missing required MLO input columns: {missing_text}")

        rows = frame.to_dict(orient="records")
        if limit is not None:
            rows = rows[:limit]

        stats = RateLimitStats()
        output_rows: list[dict[str, object]] = []
        complete_count = 0
        searches_executed = 0
        action_counts = {
            "outreach": 0,
            "monitor": 0,
            "ignore": 0,
            "insufficient_evidence": 0,
        }

        for row in rows:
            if target_complete is not None and complete_count >= target_complete:
                break
            queries = _build_queries(
                row=row,
                max_variants=self.settings.mlo_intent_query_variants,
            )

            combined_results: list[SearchResult] = []
            intent_match: IntentMatch | None = None

            for query in queries:
                cooldown_hit = self.batch_limiter.before_next_search()
                if cooldown_hit:
                    stats.batch_cooldowns += 1

                search_wait = self.search_limiter.wait()
                if search_wait > 0:
                    stats.wait_events += 1
                    stats.waited_seconds += search_wait

                query_results = self.search_provider.search(
                    query, max_results=self.settings.search_results_per_query
                )
                searches_executed += 1
                combined_results = _dedupe_results(combined_results, query_results)

                quick_match = _detect_intent(query_results, {})
                intent_match = _best_intent_match(intent_match, quick_match)
                if (
                    intent_match
                    and intent_match.confidence >= self.settings.intent_min_confidence
                    and len(combined_results) >= 3
                ):
                    break

            scraped_pages: dict[str, str] = {}
            for result in combined_results[: self.settings.scrape_top_n]:
                scrape_wait = self.scrape_limiter.wait()
                if scrape_wait > 0:
                    stats.wait_events += 1
                    stats.waited_seconds += scrape_wait

                try:
                    page = self.scrape_provider.scrape(result.url)
                    scraped_pages[result.url] = page.text
                except Exception:
                    continue

            page_corpus = " ".join(scraped_pages.values())
            scraped_intent_match = _detect_intent(combined_results, scraped_pages)
            intent_match = _best_intent_match(intent_match, scraped_intent_match)

            confidence = _infer_confidence(
                results=combined_results,
                scraped_text=page_corpus,
                intent_match=intent_match,
            )
            score = score_mlo(confidence)

            evidence_urls = [item.url for item in combined_results[:5]]
            evidence_snippets = [
                item.snippet for item in combined_results[:5] if item.snippet
            ]
            company_website = _company_site_from_results(
                combined_results, str(row.get("current_company", ""))
            )

            intent_is_strong = bool(
                intent_match
                and intent_match.confidence >= self.settings.intent_min_confidence
            )

            action = score.recommended_next_action
            if intent_is_strong and action == "ignore":
                action = "monitor"
            if self.settings.require_intent_signal and not intent_is_strong:
                action = "insufficient_evidence"
            if not evidence_urls:
                action = "insufficient_evidence"
            action_counts[action] = action_counts.get(action, 0) + 1

            contact = self.no_enrichment_provider.suggest_contact(
                full_name=str(row.get("full_name", "")),
                company_website=company_website,
            )
            # Run enrichment on all leads with evidence, not just intent-qualified ones.
            if evidence_urls and self.enrichment_provider.name != "none":
                enriched_contact = self.enrichment_provider.suggest_contact(
                    full_name=str(row.get("full_name", "")),
                    company_website=company_website,
                )
                if enriched_contact.email:
                    contact.email = enriched_contact.email
                if enriched_contact.phone:
                    contact.phone = enriched_contact.phone

            linkedin_url = _linkedin_url(combined_results)
            output_row = {
                "full_name": row.get("full_name", ""),
                "nmls_id": row.get("nmls_id", ""),
                "current_company": row.get("current_company", ""),
                "current_title": row.get("current_title", ""),
                "location": row.get("location", ""),
                "linkedin_url": linkedin_url,
                "intent_signal": intent_match.signal if intent_is_strong else "",
                "intent_phrase": intent_match.phrase if intent_is_strong else "",
                "intent_source_url": intent_match.source_url if intent_is_strong else "",
                "intent_confidence": (
                    intent_match.confidence if intent_is_strong else 0.0
                ),
                "email": contact.email,
                "phone": contact.phone,
                "company_website": contact.company_website,
                "contact_page_url": contact.contact_page_url,
                "suggested_email_pattern": contact.suggested_email_pattern,
                "score_total": score.score_total,
                "score_breakdown": json.dumps(score.score_breakdown, sort_keys=True),
                "recommended_next_action": action,
                "evidence_urls": " | ".join(evidence_urls),
                "evidence_snippets": " | ".join(evidence_snippets),
            }

            is_complete = bool(contact.email and linkedin_url)
            if target_complete is not None and not is_complete:
                logger.info(
                    "Skipping {} — missing {} (target_complete mode)",
                    row.get("full_name", ""),
                    "email" if not contact.email else "linkedin_url",
                )
                continue

            output_rows.append(output_row)
            if is_complete:
                complete_count += 1
                logger.info(
                    "Complete lead {}/{}: {}",
                    complete_count,
                    target_complete or "∞",
                    row.get("full_name", ""),
                )

        output_rows.sort(
            key=lambda row: (
                1 if row.get("intent_signal") else 0,
                float(row.get("intent_confidence", 0.0) or 0.0),
                int(row.get("score_total", 0) or 0),
            ),
            reverse=True,
        )

        output_path = output_dir / f"mlo_leads_{run_date.isoformat()}.csv"
        self.csv_store.write_rows(output_rows, output_path)

        return PipelineRun(
            output_path=output_path,
            rows_written=len(output_rows),
            searches_executed=searches_executed,
            insufficient_evidence=action_counts.get("insufficient_evidence", 0),
            action_counts=action_counts,
            rate_wait_events=stats.wait_events,
            rate_wait_seconds=round(stats.waited_seconds, 2),
            cooldown_events=stats.batch_cooldowns,
        )
