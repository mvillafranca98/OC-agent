from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd

from workspace.agent.config import AgentSettings
from workspace.agent.guardrails import MinIntervalLimiter, RateLimitStats, SearchBatchLimiter
from workspace.agent.pipeline.common import PipelineRun
from workspace.agent.providers.scrape_base import ScrapeProvider
from workspace.agent.providers.search_base import SearchProvider, SearchResult
from workspace.agent.scoring.score_company import score_company
from workspace.agent.storage.store_csv import CSVStore

COMPANY_REQUIRED_COLUMNS = {"company_name", "location"}

COMPANY_SIGNAL_KEYWORDS: dict[str, list[str]] = {
    "layoffs_or_warn": ["layoff", "warn notice", "staff reduction", "headcount cut"],
    "branch_closures": ["branch closure", "office closure", "market exit"],
    "negative_review_spike": ["negative reviews", "poor management", "toxic culture"],
    "regulatory_actions": ["cfpb", "enforcement action", "consent order", "fine"],
    "leadership_churn": ["ceo departure", "executive departure", "leadership change"],
    "acquisition_rumors": ["acquisition rumor", "exploring sale", "m&a chatter"],
    "financial_stress_news": ["liquidity", "credit line", "financial stress", "losses"],
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
        str(row.get("company_name", "")).strip(),
        str(row.get("location", "")).strip(),
        "mortgage layoffs branch closures regulatory",
    ]
    return " ".join(part for part in parts if part)


def _website_from_results(results: list[SearchResult]) -> str:
    for item in results:
        parsed = urlparse(item.url)
        if not parsed.netloc:
            continue
        return f"{parsed.scheme or 'https'}://{parsed.netloc.lower()}"
    return ""


def _infer_confidence(results: list[SearchResult], scraped_text: str) -> dict[str, float]:
    snippets = " ".join(result.snippet for result in results).lower()
    corpus = f"{snippets} {scraped_text}".lower()
    return {
        signal_name: _keyword_confidence(corpus, keywords)
        for signal_name, keywords in COMPANY_SIGNAL_KEYWORDS.items()
    }


def _distress_hypothesis(score_breakdown: dict[str, float]) -> str:
    if not score_breakdown:
        return "No strong distress signal detected from available evidence."
    top_signals = sorted(
        score_breakdown.items(), key=lambda item: item[1], reverse=True
    )[:2]
    joined = ", ".join(name for name, _ in top_signals)
    return f"Primary distress indicators: {joined}."


class CompanyPipeline:
    def __init__(
        self,
        settings: AgentSettings,
        search_provider: SearchProvider,
        scrape_provider: ScrapeProvider,
        csv_store: CSVStore,
    ) -> None:
        self.settings = settings
        self.search_provider = search_provider
        self.scrape_provider = scrape_provider
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
        missing = sorted(COMPANY_REQUIRED_COLUMNS - set(frame.columns))
        if missing:
            missing_text = ", ".join(missing)
            raise ValueError(f"Missing required company input columns: {missing_text}")

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
            score = score_company(confidence)

            evidence_urls = [item.url for item in results[:5]]
            evidence_snippets = [item.snippet for item in results[:5] if item.snippet]

            action = score.recommended_next_action
            if not evidence_urls:
                action = "insufficient_evidence"
            action_counts[action] = action_counts.get(action, 0) + 1

            output_rows.append(
                {
                    "company_name": row.get("company_name", ""),
                    "location": row.get("location", ""),
                    "website": row.get("website", "") or _website_from_results(results),
                    "score_total": score.score_total,
                    "score_breakdown": json.dumps(score.score_breakdown, sort_keys=True),
                    "distress_hypothesis": _distress_hypothesis(score.score_breakdown),
                    "recommended_next_action": action,
                    "evidence_urls": " | ".join(evidence_urls),
                    "evidence_snippets": " | ".join(evidence_snippets),
                }
            )

        output_path = output_dir / f"company_leads_{run_date.isoformat()}.csv"
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

