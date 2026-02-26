# Daily Summary Template

**Date:** YYYY-MM-DD  
**Workflow:** Workflow A or Workflow B  
**Mode:** Live or Dry-run  

---

## Run overview

- Target geography:
- Batch size:
- Model usage: Haiku default; Sonnet escalations (if any) with reason.

## Cost and rate limits

- API/search calls made:
- Rate-limit events (if any):
- Daily budget status ($5 target, 75% warning):
- Monthly budget status ($200 target, 75% warning):

## Data integrity checks

- Identity source used (NMLS or other verifiable source):
- Any fail-closed event (for example, NMLS unavailable):
- Count of rows marked `insufficient_evidence`:
- Confirmation: no fabricated names/IDs/URLs.

## Results

- Total rows exported:
- Outreach tier count:
- Monitor tier count:
- `insufficient_evidence` count:
- Output files:
  - `projects/mortgage-signals/outputs/mlo_leads_YYYY-MM-DD.csv` or `projects/mortgage-signals/outputs/company_leads_YYYY-MM-DD.csv`
  - `projects/mortgage-signals/outputs/daily_summary_YYYY-MM-DD.md`

## Blockers

- List blockers encountered in this run.

## Next steps

- Next run timing:
- Required inputs from user (if any):
- Keep default low-cost mode unless user explicitly requests add-ons.
