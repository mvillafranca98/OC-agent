# Quick test run — Mortgage Signals Agent

Validate the full workflow end-to-end in under 5 minutes.

---

## Prerequisites checklist

Before running, confirm:

- [ ] `openclaw gateway` is running (`http://localhost:18789` responds)
- [ ] Ollama is running (`ollama serve`) with `llama3.2:3b` pulled
- [ ] `~/.openclaw/openclaw.json` has correct workspace path and Brave API key
- [ ] Anthropic key is stored: `openclaw config set auth.anthropic.key sk-ant-...`
- [ ] `.env` has `ANTHROPIC_API_KEY` and `BRAVE_API_KEY` set

---

## Option A — Dry run (no API costs, instant)

Uses 5 pre-built mock leads from `DRY_RUN_DATA.md`. Validates the full scoring + export pipeline. Output is marked as test data.

```bash
openclaw agent --agent main --json --message "Run Workflow A dry run using DRY_RUN_DATA.md. Output to projects/mortgage-signals/outputs/mlo_leads_$(date +%Y-%m-%d).csv and projects/mortgage-signals/outputs/daily_summary_$(date +%Y-%m-%d).md"
```

Expected: completes in ~15 seconds.

---

## Option B — Live run (recommended, uses Brave Search)

Discovers real California MLOs from public sources (LinkedIn, HousingWire, press releases) and scores them.

```bash
openclaw agent --agent main --json --message "$(cat <<'EOF'
Run Workflow A from projects/mortgage-signals/RUNBOOK.md with a small batch.

Constraints:
- Use Haiku by default; escalate to Sonnet only for ambiguous dedupe/reasoning.
- Use NMLS as identity source. If NMLS is unavailable, fall back to Brave Search for real verified identities — do not fabricate.
- Prioritize LinkedIn intent signals: "open to work" and "open for business".
- Use free search + direct scraping by default (Brave + public pages).
- Keep enrichment disabled by default (no paid email APIs).
- Enforce rate limits and budget policy.
- Do not recommend add-on paid services unless I explicitly ask.

Output:
- projects/mortgage-signals/outputs/mlo_leads_YYYY-MM-DD.csv
- projects/mortgage-signals/outputs/daily_summary_YYYY-MM-DD.md
EOF
)"
```

Expected: completes in 2–3 minutes for a 10-lead batch.

> **Note:** NMLS Consumer Access is behind Cloudflare. The agent falls back to Brave Search automatically — this is normal and produces real, verifiable leads.

---

## Validate outputs

Check these after the run:

```bash
ls workspace/projects/mortgage-signals/outputs/
```

Open the CSV and confirm:
- `full_name` and `nmls_id` are real (not `-mock` or sequential like `1234567`)
- `recommended_next_action` is `Outreach`, `Monitor`, or `Ignore`
- `evidence_summary` cites real sources with dates
- No fabricated rows — if identity was unverifiable, row should show `insufficient_evidence`

Open the daily summary and confirm:
- Search count and budget are logged
- Rate limit compliance is noted

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `Error: Pass --to, --session-id, or --agent` | Add `--agent main` to the command |
| Agent returns mock data | Check that `DRY_RUN_DATA.md` isn't being used unintentionally; re-run with explicit live instruction |
| `tab not found` browser errors | Expected if using browser relay; agent falls back to Brave Search automatically |
| `auth.json` reverts to old key | Use `openclaw config set auth.anthropic.key YOUR_KEY` instead of editing the file |
| Gateway not responding | Run `openclaw gateway` in a terminal and keep it open |

---

## Output paths

```
workspace/projects/mortgage-signals/outputs/mlo_leads_YYYY-MM-DD.csv
workspace/projects/mortgage-signals/outputs/daily_summary_YYYY-MM-DD.md
```
