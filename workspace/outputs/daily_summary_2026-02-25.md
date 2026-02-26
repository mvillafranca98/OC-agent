# Dry Run — MLO Lead Scoring Summary
**Date:** 2026-02-25  
**Workflow:** Workflow A (MLO Leads) — Dry Run (no web search)  
**Geography:** California  
**Role:** Mortgage Loan Officer  

---

## Run Overview

This was a **dry-run scoring exercise** using pre-built mock data from `projects/mortgage-signals/DRY_RUN_DATA.md`. No web searches were performed; all scoring was applied to provided signals.

**Objective:** Validate signal-to-score mapping, rubric application, and output formatting.

---

## Results

### Counts
- **Total leads scored:** 5
- **High priority (score ≥60, Outreach):** 2
  - Jessica Harmon (Pacific Crest Mortgage) — 63
  - Alicia Nguyen (Horizon Funding Corp) — 63
- **Medium priority (20–59, Monitor):** 3
  - Marcus Delgado (Sunridge Home Loans) — 27
  - Renee Castillo (Golden State Lending Group) — 26
  - David Park (Bay Area Mortgage Partners) — 19

### Scoring method
- **Rubric:** Applied `projects/mortgage-signals/SCORING_RUBRIC.md` (MLO "ready to move" weights and confidence multipliers).
- **Signal library:** Mapped each signal to categories in `projects/mortgage-signals/SIGNAL_LIBRARY.md`.
- **Formula:** score_total = sum of (weight × confidence_multiplier) per signal.
- **Confidence:** high (1.0), medium (0.7), low (0.4).
- **Cap:** None applied (scores capped at 100 per rubric).

### Evidence quality
All 5 leads have at least 2–3 evidence sources with high or medium confidence. Each entry includes:
- Source type and URL
- Snippet (direct quote or paraphrase)
- Timestamp
- Confidence level (high/medium)

---

## Key observations

1. **Two leads (Jessica Harmon, Alicia Nguyen) scored 63:** Both have triple high-confidence signals: explicit job-seeking intent (open-to-work or headline) + employer instability + location disruption. These are **clear outreach targets**.

2. **Three leads moderate to low scores:** Marcus Delgado, Renee Castillo, and David Park all have mixed or softer signals (compensation complaints, title churn, team departures, or single company-turmoil signal). These are **monitor/watchlist** candidates.

3. **Signal distribution:** High-impact signals (open_to_work, company_turmoil, branch_closure_proximity) drove top scores; softer signals (posting frequency, team departures) contributed ~10 points each.

---

## Output files

- **`outputs/mlo_leads_2026-02-25.csv`** — Ranked list with score_breakdown, recommended_next_action, and evidence_summary for each lead.
- **`outputs/daily_summary_2026-02-25.md`** — This summary document.

---

## Model used

- **Claude Haiku** (default, routine scoring and output generation).

---

## Next steps

- If running live Workflow A (with web search), follow the same rubric and format.
- All outreach is human-driven; these scores and evidence summaries are for recruiter review only.
- No API costs for this dry run.
