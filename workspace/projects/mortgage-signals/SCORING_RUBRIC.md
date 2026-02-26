# Scoring rubric — Mortgage Signals Agent

Stable reference for weights and confidence. Use for explainable score breakdowns; keep this file cache-friendly.

---

## A) MLO “ready to move” scoring

### Signal weights (example; adjust per org preference)

| Signal category | Weight | Notes |
|-----------------|--------|-------|
| Open to work | High (e.g. 25) | Strong explicit intent |
| Profile changes (recent) | Medium (e.g. 15) | Suggests active job search |
| Posting frequency (career dissatisfaction) | Medium (e.g. 15) | Soft signal |
| Recruiter engagement | Medium (e.g. 12) | If clearly public |
| Team departures | Medium (e.g. 12) | Context-dependent |
| Compensation / commission complaints | Medium (e.g. 12) | Push factor |
| Branch closure proximity | High (e.g. 20) | Strong structural push |
| Company turmoil | High (e.g. 18) | Employer instability |

### Confidence multiplier

- **High confidence:** 1.0 (direct quote, primary source, recent)
- **Medium confidence:** 0.7 (paraphrase, secondary source, or older)
- **Low confidence:** 0.4 (hearsay, vague, or single weak signal)

**Score per signal:** weight × confidence. **Score total:** sum of signal scores (capped at 100 if desired). **Score breakdown:** list each signal type and its contribution so recruiters see “why” the lead was ranked.

### Recommended next action

- **Outreach** — Score above threshold (e.g. ≥60) and strong evidence; prioritize for contact.
- **Monitor** — Moderate score or mixed evidence; add to watchlist or follow up later.
- **Ignore** — Low score or insufficient evidence; do not prioritize.

---

## B) Company distress scoring

### Signal weights (example)

| Signal category | Weight | Notes |
|-----------------|--------|-------|
| Layoffs / WARN / staff reductions | High (e.g. 22) | Direct distress indicator |
| Branch closures | High (e.g. 20) | Contraction signal |
| Negative review spike | Medium (e.g. 14) | Reputation and morale |
| Regulatory actions | High (e.g. 18) | Compliance and stability risk |
| Leadership churn | Medium (e.g. 14) | Strategy and stability |
| Acquisition rumors / broker chatter | Medium (e.g. 12) | Possible readiness to sell |
| Financial stress (news) | High (e.g. 20) | Liquidity or solvency |

### Confidence multiplier

Same as MLO: High 1.0, Medium 0.7, Low 0.4.

**Score total:** Sum of (weight × confidence) per signal; cap at 100 if desired. **Breakdown:** List each signal and its contribution. **Distress hypothesis:** One short paragraph per company summarizing the main signals and evidence (for the company lead output).

### Recommended next action

- **Outreach** — High distress score; company may be open to acquisition or key talent may be open to move.
- **Monitor** — Moderate score; track for changes.
- **Ignore** — Low score or insufficient evidence.

---

## Output requirements

- Every lead (MLO or company) must have a **score_total** and **score_breakdown** (explainable).
- High-priority leads must include at least 2 evidence sources or 1 high-confidence source with a clear snippet.
- CSVs must use consistent columns so they open cleanly in Google Sheets; no broken formatting (escape quotes in CSV, consistent date format).
