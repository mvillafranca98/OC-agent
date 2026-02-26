from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

COMPANY_SIGNAL_WEIGHTS: dict[str, int] = {
    "layoffs_or_warn": 22,
    "branch_closures": 20,
    "negative_review_spike": 14,
    "regulatory_actions": 18,
    "leadership_churn": 14,
    "acquisition_rumors": 12,
    "financial_stress_news": 20,
}


@dataclass(slots=True)
class ScoreResult:
    score_total: int
    score_breakdown: dict[str, float]
    recommended_next_action: str


def _action_for_score(score_total: int) -> str:
    if score_total >= 60:
        return "outreach"
    if score_total >= 35:
        return "monitor"
    return "ignore"


def score_company(signal_confidence: Mapping[str, float]) -> ScoreResult:
    breakdown: dict[str, float] = {}
    total = 0.0
    for signal_name, weight in COMPANY_SIGNAL_WEIGHTS.items():
        confidence = float(signal_confidence.get(signal_name, 0.0))
        confidence = min(max(confidence, 0.0), 1.0)
        contribution = round(weight * confidence, 2)
        if contribution > 0:
            breakdown[signal_name] = contribution
            total += contribution

    score_total = int(round(total))
    return ScoreResult(
        score_total=score_total,
        score_breakdown=breakdown,
        recommended_next_action=_action_for_score(score_total),
    )

