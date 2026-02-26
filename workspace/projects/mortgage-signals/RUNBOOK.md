# Mortgage Signals Agent — Runbook

How to run daily or weekly lead generation with strict low-cost defaults.

---

## Prerequisites

- OpenClaw installed and configured (see repo README).
- Ollama running with heartbeat model (for example `llama3.2:3b`) so heartbeat uses no paid API tokens.
- Required env key: `ANTHROPIC_API_KEY`.
- Provider flags:
  - `SEARCH_PROVIDER=duckduckgo`
  - `ENRICHMENT_PROVIDER=none`
  - `ALLOW_PAID_PROVIDERS=false`
- Budget policy:
  - Daily budget target: $5
  - Monthly budget target: $200
  - Warning at 75% of each budget

---

## Workflow A: MLO leads (verified identities only)

1. **Define target** — Geography and role scope; set batch size.
2. **Pull real individuals from NMLS (required for live run)** — Use browser workflow in TOOLS.md. Collect real `full_name`, `nmls_id`, employer, and location.
3. **Fail closed if NMLS is unavailable** — Do not synthesize names. Ask user for a seed CSV/list or run dry-run scoring only.
4. **Gather public signals** — Use free search + direct public-page scraping for employer and individual evidence.
5. **Normalize and dedupe** — Merge duplicates; use Sonnet only for ambiguous identity resolution.
6. **Score** — Apply `SIGNAL_LIBRARY.md` and `SCORING_RUBRIC.md` using evidence-backed signals.
7. **Integrity gate before export**:
   - Exclude leads with unverifiable identity.
   - If evidence is missing/ambiguous, set `recommended_next_action=insufficient_evidence`.
8. **Export** — Write `projects/mortgage-signals/outputs/mlo_leads_YYYY-MM-DD.csv` and update `projects/mortgage-signals/outputs/daily_summary_YYYY-MM-DD.md`.

**Required MLO columns:**
`full_name, nmls_id, current_company, current_title, location, linkedin_url, score_total, score_breakdown, recommended_next_action, evidence_urls, evidence_snippets`

---

## Workflow B: Distressed companies

1. **Define target** — Geography and company type.
2. **Crawl public sources** — News/reviews/regulatory updates with rate limits.
3. **Identify/dedupe** — Resolve company entities.
4. **Score distress** — Apply rubric with evidence links/snippets.
5. **Integrity gate** — If evidence is weak, mark `insufficient_evidence`.
6. **Export** — Write `projects/mortgage-signals/outputs/company_leads_YYYY-MM-DD.csv` and update daily summary.

---

## Running cadence

- **Daily/weekly:** Run workflow A and/or B with date-stamped outputs.
- **Cost controls:** Enforce max 5 searches per batch and cooldown. Stop on repeated 429s.
- **Budget logging:** If near 75% of daily/monthly budget, add warning to daily summary and memory.

---

## Output layout

| File | Content |
|------|--------|
| `projects/mortgage-signals/outputs/mlo_leads_YYYY-MM-DD.csv` | Ranked MLO leads with verified identity fields and explainable score breakdowns. |
| `projects/mortgage-signals/outputs/company_leads_YYYY-MM-DD.csv` | Ranked companies with distress score, hypothesis summary, and evidence. |
| `projects/mortgage-signals/outputs/daily_summary_YYYY-MM-DD.md` | Run summary with counts, budget warnings, model escalations, blockers, and next steps. |

---

## Human-in-the-loop

- Agent is research-only. It never sends outreach.
- Outreach decisions and sends are human actions only.
- Do not add or recommend extra paid services unless the user explicitly asks.

---

## Optional add-ons (explicit request only)

Paid search/enrichment adapters and outreach draft generation are optional. Use only when the user explicitly asks and feature flags permit usage.
