# Quick test run — Mortgage Signals Agent

Minimal validation of low-cost defaults.

## 1) Prerequisites

- OpenClaw is installed and running.
- Ollama is running with `llama3.2:3b`.
- `~/.openclaw/openclaw.json` copied from `openclaw.json.example`.
- `ANTHROPIC_API_KEY` is set.
- `.env` has:
  - `SEARCH_PROVIDER=duckduckgo`
  - `ENRICHMENT_PROVIDER=none`
  - `ALLOW_PAID_PROVIDERS=false`

## 2) Run Workflow A (small batch)

Use this prompt in OpenClaw:

```text
Run Workflow A from projects/mortgage-signals/RUNBOOK.md with a small batch.

Constraints:
- Use Haiku by default; escalate to Sonnet only for ambiguous dedupe/reasoning.
- Use NMLS as identity source for live leads.
- If NMLS/browser is unavailable, fail closed: do not synthesize names; ask for seed CSV or run dry-run only.
- Use free search + direct scraping by default.
- Keep enrichment disabled by default.
- Enforce rate limits and budget policy.

Output:
- projects/mortgage-signals/outputs/mlo_leads_YYYY-MM-DD.csv
- projects/mortgage-signals/outputs/daily_summary_YYYY-MM-DD.md
```

## 3) Validate output

Check:
- `workspace/projects/mortgage-signals/outputs/mlo_leads_YYYY-MM-DD.csv`
- `workspace/projects/mortgage-signals/outputs/daily_summary_YYYY-MM-DD.md`

Confirm:
- identity fields are verifiable
- no fabricated rows
- weak rows are marked `insufficient_evidence`

