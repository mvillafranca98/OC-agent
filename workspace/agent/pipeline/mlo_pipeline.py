from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd

from workspace.agent.config import AgentSettings
from workspace.agent.guardrails import MinIntervalLimiter, RateLimitStats, SearchBatchLimiter
from workspace.agent.pipeline.common import PipelineRun
from workspace.agent.providers.enrich_base import EnrichmentProvider
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
    "open_to_work": ["open to work", "exploring opportunities", "seeking new role"],
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


def _keyword_confidence(corpus: str, phrases: list[str]) -> float:
    match_count = sum(corpus.count(phrase) for phrase in phrases)
    if match_count >= 2:
        return 0.7
    if match_count == 1:
        return 0.4
    return 0.0


def _build_query(row: dict[str, object]) -> str:
    parts = [
        str(row.get("full_name", "")).strip(),
        str(row.get("current_company", "")).strip(),
        "mortgage loan officer",
        str(row.get("location", "")).strip(),
    ]
    return " ".join(part for part in parts if part)


def _company_site_from_results(results: list[SearchResult]) -> str:
    for item in results:
        parsed = urlparse(item.url)
        if not parsed.netloc:
            continue
        host = parsed.netloc.lower()
        if "linkedin.com" in host:
            continue
        return f"{parsed.scheme or 'https'}://{host}"
    return ""


def _linkedin_url(results: list[SearchResult]) -> str:
    for item in results:
        if "linkedin.com/in/" in item.url:
            return item.url
    return ""


def _infer_confidence(results: list[SearchResult], scraped_text: str) -> dict[str, float]:
    snippets = " ".join(result.snippet for result in results).lower()
    corpus = f"{snippets} {scraped_text}".lower()

    confidence: dict[str, float] = {}
    for signal_name, keywords in MLO_SIGNAL_KEYWORDS.items():
        base_conf = _keyword_confidence(corpus, keywords)
        if signal_name == "open_to_work" and base_conf > 0:
            confidence[signal_name] = 1.0
        else:
            confidence[signal_name] = base_conf

    # Posting frequency proxy: more indexed mentions can indicate movement or chatter.
    if len(results) >= 5:
        confidence["posting_frequency"] = 0.7
    elif len(results) >= 3:
        confidence["posting_frequency"] = 0.4
    else:
        confidence["posting_frequency"] = 0.0

    return confidence


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
        searches_executed = 0
        action_counts = {"outreach": 0, "monitor": 0, "ignore": 0, "insufficient_evidence": 0}

        for row in rows:
            cooldown_hit = self.batch_limiter.before_next_search()
            if cooldown_hit:
                stats.batch_cooldowns += 1

            search_wait = self.search_limiter.wait()
            if search_wait > 0:
                stats.wait_events += 1
                stats.waited_seconds += search_wait

            query = _build_query(row)
            results = self.search_provider.search(
                query, max_results=self.settings.search_results_per_query
            )
            searches_executed += 1

            scraped_text_parts: list[str] = []
            for result in results[: self.settings.scrape_top_n]:
                scrape_wait = self.scrape_limiter.wait()
                if scrape_wait > 0:
                    stats.wait_events += 1
                    stats.waited_seconds += scrape_wait

                try:
                    page = self.scrape_provider.scrape(result.url)
                    scraped_text_parts.append(page.text)
                except Exception:
                    continue

            scraped_text = " ".join(scraped_text_parts)
            confidence = _infer_confidence(results=results, scraped_text=scraped_text)
            score = score_mlo(confidence)

            evidence_urls = [item.url for item in results[:5]]
            evidence_snippets = [item.snippet for item in results[:5] if item.snippet]
            company_website = _company_site_from_results(results)
            contact = self.enrichment_provider.suggest_contact(
                full_name=str(row.get("full_name", "")),
                company_website=company_website,
            )

            action = score.recommended_next_action
            if not evidence_urls:
                action = "insufficient_evidence"
            action_counts[action] = action_counts.get(action, 0) + 1

            output_rows.append(
                {
                    "full_name": row.get("full_name", ""),
                    "nmls_id": row.get("nmls_id", ""),
                    "current_company": row.get("current_company", ""),
                    "current_title": row.get("current_title", ""),
                    "location": row.get("location", ""),
                    "linkedin_url": _linkedin_url(results),
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

