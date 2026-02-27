from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator

FREE_SEARCH_PROVIDERS = {"duckduckgo", "searxng"}
FREE_ENRICHMENT_PROVIDERS = {"none"}


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    return int(raw)


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    return float(raw)


class AgentSettings(BaseModel):
    workspace_root: Path = Field(default=Path("workspace"))
    output_root: Path = Field(default=Path("workspace/projects/mortgage-signals/outputs"))

    search_provider: str = Field(default="duckduckgo")
    enrichment_provider: str = Field(default="none")
    allow_paid_providers: bool = Field(default=False)

    max_searches_per_batch: int = Field(default=5)
    search_interval_seconds: float = Field(default=10.0)
    api_interval_seconds: float = Field(default=5.0)
    batch_cooldown_seconds: int = Field(default=120)
    search_results_per_query: int = Field(default=5)
    scrape_top_n: int = Field(default=2)
    scrape_timeout_seconds: float = Field(default=15.0)
    mlo_intent_query_variants: int = Field(default=2)
    require_intent_signal: bool = Field(default=True)
    intent_min_confidence: float = Field(default=0.7)

    daily_budget_usd: float = Field(default=5.0)
    monthly_budget_usd: float = Field(default=200.0)
    budget_warning_ratio: float = Field(default=0.75)

    anthropic_primary_model: str = Field(default="anthropic/claude-haiku-4-5")
    anthropic_sonnet_model: str = Field(default="anthropic/claude-sonnet-4-5")
    heartbeat_model: str = Field(default="ollama/llama3.2:3b")

    @field_validator("search_provider", "enrichment_provider")
    @classmethod
    def _normalize_provider(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if not cleaned:
            raise ValueError("provider value cannot be empty")
        return cleaned

    @field_validator(
        "max_searches_per_batch",
        "search_results_per_query",
        "scrape_top_n",
        "mlo_intent_query_variants",
    )
    @classmethod
    def _require_positive_int(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("value must be > 0")
        return value

    @field_validator(
        "search_interval_seconds",
        "api_interval_seconds",
        "scrape_timeout_seconds",
        "intent_min_confidence",
    )
    @classmethod
    def _require_positive_float(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("value must be > 0")
        return value

    @field_validator("intent_min_confidence")
    @classmethod
    def _intent_confidence_in_range(cls, value: float) -> float:
        if value > 1.0:
            raise ValueError("intent_min_confidence must be <= 1.0")
        return value

    @classmethod
    def from_env(cls) -> "AgentSettings":
        load_dotenv()
        return cls(
            workspace_root=Path(os.getenv("WORKSPACE_ROOT", "workspace")),
            output_root=Path(
                os.getenv(
                    "OUTPUT_ROOT",
                    "workspace/projects/mortgage-signals/outputs",
                )
            ),
            search_provider=os.getenv("SEARCH_PROVIDER", "duckduckgo"),
            enrichment_provider=os.getenv("ENRICHMENT_PROVIDER", "none"),
            allow_paid_providers=_env_bool("ALLOW_PAID_PROVIDERS", False),
            max_searches_per_batch=_env_int("MAX_SEARCHES_PER_BATCH", 5),
            search_interval_seconds=_env_float("SEARCH_INTERVAL_SECONDS", 10.0),
            api_interval_seconds=_env_float("API_INTERVAL_SECONDS", 5.0),
            batch_cooldown_seconds=_env_int("BATCH_COOLDOWN_SECONDS", 120),
            search_results_per_query=_env_int("SEARCH_RESULTS_PER_QUERY", 5),
            scrape_top_n=_env_int("SCRAPE_TOP_N", 2),
            scrape_timeout_seconds=_env_float("SCRAPE_TIMEOUT_SECONDS", 15.0),
            mlo_intent_query_variants=_env_int("MLO_INTENT_QUERY_VARIANTS", 2),
            require_intent_signal=_env_bool("REQUIRE_INTENT_SIGNAL", True),
            intent_min_confidence=_env_float("INTENT_MIN_CONFIDENCE", 0.7),
            daily_budget_usd=_env_float("DAILY_BUDGET_USD", 5.0),
            monthly_budget_usd=_env_float("MONTHLY_BUDGET_USD", 200.0),
            budget_warning_ratio=_env_float("BUDGET_WARNING_RATIO", 0.75),
            anthropic_primary_model=os.getenv(
                "ANTHROPIC_PRIMARY_MODEL", "anthropic/claude-haiku-4-5"
            ),
            anthropic_sonnet_model=os.getenv(
                "ANTHROPIC_SONNET_MODEL", "anthropic/claude-sonnet-4-5"
            ),
            heartbeat_model=os.getenv("HEARTBEAT_MODEL", "ollama/llama3.2:3b"),
        )

    def is_paid_search_provider(self) -> bool:
        return self.search_provider not in FREE_SEARCH_PROVIDERS

    def is_paid_enrichment_provider(self) -> bool:
        return self.enrichment_provider not in FREE_ENRICHMENT_PROVIDERS

    def validate_feature_flags(self) -> None:
        if self.allow_paid_providers:
            return
        if self.is_paid_search_provider():
            raise ValueError(
                f"Paid search provider '{self.search_provider}' is blocked. "
                "Set ALLOW_PAID_PROVIDERS=true to override."
            )
        if self.is_paid_enrichment_provider():
            raise ValueError(
                f"Paid enrichment provider '{self.enrichment_provider}' is blocked. "
                "Set ALLOW_PAID_PROVIDERS=true to override."
            )
