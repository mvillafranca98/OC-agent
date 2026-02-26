from __future__ import annotations

import argparse
import os
from datetime import date
from pathlib import Path

from loguru import logger

from workspace.agent.config import AgentSettings
from workspace.agent.pipeline.common import PipelineRun
from workspace.agent.pipeline.company_pipeline import CompanyPipeline
from workspace.agent.pipeline.mlo_pipeline import MLOPipeline
from workspace.agent.providers.enrich_apollo import ApolloEnrichmentProvider
from workspace.agent.providers.enrich_base import EnrichmentProvider
from workspace.agent.providers.enrich_hunter import HunterEnrichmentProvider
from workspace.agent.providers.enrich_none import NoEnrichmentProvider
from workspace.agent.providers.scrape_requests import RequestsScrapeProvider
from workspace.agent.providers.search_base import SearchProvider
from workspace.agent.providers.search_duckduckgo import DuckDuckGoSearchProvider
from workspace.agent.storage.store_csv import CSVStore


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Low-cost mortgage signals scaffold runner."
    )
    parser.add_argument(
        "--workflow",
        required=True,
        choices=["mlo", "company"],
        help="Pipeline to run.",
    )
    parser.add_argument(
        "--input-csv",
        required=True,
        help="Absolute or relative CSV path with input records.",
    )
    parser.add_argument(
        "--date",
        default=date.today().isoformat(),
        help="Run date in YYYY-MM-DD format.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional max rows to process.",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Optional output directory override.",
    )
    return parser.parse_args()


def _build_search_provider(settings: AgentSettings) -> SearchProvider:
    if settings.search_provider == "duckduckgo":
        return DuckDuckGoSearchProvider()
    if not settings.allow_paid_providers:
        raise ValueError(
            f"Search provider '{settings.search_provider}' is blocked by feature flags."
        )
    raise NotImplementedError(
        f"Search provider '{settings.search_provider}' is not implemented yet."
    )


def _build_enrichment_provider(settings: AgentSettings) -> EnrichmentProvider:
    if settings.enrichment_provider == "none":
        return NoEnrichmentProvider()
    if not settings.allow_paid_providers:
        raise ValueError(
            "Paid enrichment provider requested while ALLOW_PAID_PROVIDERS=false."
        )
    if settings.enrichment_provider == "hunter":
        api_key = os.getenv("HUNTER_API_KEY", "")
        if not api_key:
            raise ValueError("HUNTER_API_KEY is not set in environment.")
        return HunterEnrichmentProvider(
            api_key=api_key,
            interval_seconds=settings.api_interval_seconds,
        )
    if settings.enrichment_provider == "apollo":
        api_key = os.getenv("APOLLO_API_KEY", "")
        if not api_key:
            raise ValueError("APOLLO_API_KEY is not set in environment.")
        return ApolloEnrichmentProvider(
            api_key=api_key,
            interval_seconds=settings.api_interval_seconds,
        )
    raise NotImplementedError(
        f"Enrichment provider '{settings.enrichment_provider}' is not implemented yet."
    )


def _daily_summary_lines(
    run: PipelineRun,
    workflow: str,
    run_date: date,
    settings: AgentSettings,
) -> list[str]:
    return [
        "# Daily Summary",
        f"**Date:** {run_date.isoformat()}",
        f"**Workflow:** {workflow}",
        "",
        "## Run overview",
        f"- Rows exported: {run.rows_written}",
        f"- Searches executed: {run.searches_executed}",
        f"- Rate-limit wait events: {run.rate_wait_events}",
        f"- Rate-limit wait seconds: {run.rate_wait_seconds}",
        f"- Batch cooldown events: {run.cooldown_events}",
        "",
        "## Action counts",
        f"- Outreach: {run.action_counts.get('outreach', 0)}",
        f"- Monitor: {run.action_counts.get('monitor', 0)}",
        f"- Ignore: {run.action_counts.get('ignore', 0)}",
        f"- insufficient_evidence: {run.insufficient_evidence}",
        "",
        "## Guardrails and providers",
        f"- Search provider: {settings.search_provider}",
        f"- Enrichment provider: {settings.enrichment_provider}",
        f"- ALLOW_PAID_PROVIDERS: {str(settings.allow_paid_providers).lower()}",
        "- Heartbeat model (local): ollama/llama3.2:3b",
        "",
        "## Outputs",
        f"- CSV: {run.output_path}",
    ]


def _write_daily_summary(
    run: PipelineRun,
    workflow: str,
    run_date: date,
    output_dir: Path,
    settings: AgentSettings,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / f"daily_summary_{run_date.isoformat()}.md"
    summary = "\n".join(_daily_summary_lines(run, workflow, run_date, settings)).strip()
    summary_path.write_text(f"{summary}\n", encoding="utf-8")
    return summary_path


def main() -> int:
    args = _parse_args()
    run_date = date.fromisoformat(args.date)

    settings = AgentSettings.from_env()
    if args.output_dir:
        settings = settings.model_copy(update={"output_root": Path(args.output_dir)})
    settings.validate_feature_flags()

    input_path = Path(args.input_csv)
    if not input_path.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_path}")

    output_dir = settings.output_root
    search_provider = _build_search_provider(settings)
    enrichment_provider = _build_enrichment_provider(settings)
    scrape_provider = RequestsScrapeProvider(
        timeout_seconds=settings.scrape_timeout_seconds
    )
    csv_store = CSVStore()

    logger.info("Running workflow={} input={}", args.workflow, input_path)
    if args.workflow == "mlo":
        pipeline = MLOPipeline(
            settings=settings,
            search_provider=search_provider,
            scrape_provider=scrape_provider,
            enrichment_provider=enrichment_provider,
            csv_store=csv_store,
        )
        run = pipeline.run(
            input_csv=input_path,
            run_date=run_date,
            output_dir=output_dir,
            limit=args.limit,
        )
    else:
        pipeline = CompanyPipeline(
            settings=settings,
            search_provider=search_provider,
            scrape_provider=scrape_provider,
            csv_store=csv_store,
        )
        run = pipeline.run(
            input_csv=input_path,
            run_date=run_date,
            output_dir=output_dir,
            limit=args.limit,
        )

    summary_path = _write_daily_summary(
        run=run,
        workflow=args.workflow,
        run_date=run_date,
        output_dir=output_dir,
        settings=settings,
    )
    logger.info("CSV written: {}", run.output_path)
    logger.info("Summary written: {}", summary_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

