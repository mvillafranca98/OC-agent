# Quick test run — Mortgage Signals Agent

Minimal setup and one small run so you can see results quickly.

---

## 1. Setup (minimal)

Do this once before your first test.

| Step | What to do |
|------|------------|
| **OpenClaw** | Install [OpenClaw](https://docs.openclaw.ai) and run `openclaw setup` (or `openclaw onboard`). |
| **Ollama** | Install [Ollama](https://ollama.ai), then run `ollama pull llama3.2:3b` so heartbeat uses no paid tokens. |
| **Config** | Copy `openclaw.json.example` to `~/.openclaw/openclaw.json`. Set `agents.defaults.workspace` to this repo’s `workspace/` folder (full path). |
| **Anthropic key** | Create an API key at [console.anthropic.com](https://console.anthropic.com). Set `ANTHROPIC_API_KEY` in your environment (e.g. in `.env` or `export` in the shell you use to run OpenClaw). |
| **Search (optional)** | For real web search during the run, add a search API key (e.g. [Brave Search API](https://brave.com/search/api/)). Without it, the agent can still do a **dry run** (e.g. score and export from a small hand-fed or mock list). |

---

## 2. Run a small test

1. Start OpenClaw (e.g. `openclaw gateway` or your usual way to chat with the agent).
2. In a **new session**, paste a prompt like this (adjust geography/role if you like):

   **Workflow A (MLO leads), small batch:**

   ```text
   Run Workflow A from projects/mortgage-signals/RUNBOOK.md with a small test batch:
   - Geography: California (or one state you care about)
   - Role: mortgage loan officer
   - Limit to top 5–10 candidates so we can validate the output quickly.
   Write the ranked list to outputs/mlo_leads_YYYY-MM-DD.csv and update outputs/daily_summary_YYYY-MM-DD.md (use today’s date for YYYY-MM-DD).
   ```

   **Or Workflow B (distressed companies), small batch:**

   ```text
   Run Workflow B from projects/mortgage-signals/RUNBOOK.md with a small test batch:
   - Geography: California (or one state)
   - Company type: mortgage lenders/brokers
   - Limit to 5–10 companies.
   Write the ranked list to outputs/company_leads_YYYY-MM-DD.csv and update outputs/daily_summary_YYYY-MM-DD.md (use today’s date).
   ```

3. Let the agent finish. It will create (or update) files in **`workspace/outputs/`**.

---

## 3. Where to see the results (your “database”)

The agent does **not** write to a database by default. It writes to files in **`workspace/outputs/`**. You can treat those as your test results and open them in any of these ways.

### Option A: Spreadsheet (simplest)

- **MLO run:** Open `workspace/outputs/mlo_leads_YYYY-MM-DD.csv` in Excel, Numbers, or [Google Sheets](https://sheets.google.com) (File → Import → Upload and choose the CSV).
- **Company run:** Open `workspace/outputs/company_leads_YYYY-MM-DD.csv` the same way.
- **Run summary:** Open `workspace/outputs/daily_summary_YYYY-MM-DD.md` in any text editor or Markdown viewer.

No account needed for local spreadsheets; Google Sheets needs a free Google account.

### Option B: SQLite (query results like a database)

If you want to query results with SQL (filter, sort, join), load the CSV into SQLite once per test run:

```bash
cd /path/to/openclaw_agent/workspace/outputs

# Create a SQLite DB and import the MLO CSV (use today’s date in the filename)
sqlite3 quick_test.db
```

In the SQLite shell:

```sql
.mode csv
.import mlo_leads_2026-02-25.csv mlo_leads
-- If the first row is headers, run: delete from mlo_leads where full_name = 'full_name';
.quit
```

Then query:

```bash
sqlite3 quick_test.db "SELECT full_name, current_company, score_total FROM mlo_leads ORDER BY score_total DESC LIMIT 10;"
```

Use the same idea for `company_leads_YYYY-MM-DD.csv` (e.g. `.import company_leads_2026-02-25.csv company_leads`). SQLite is free and needs no server or account.

### Option C: Keep only the CSV + summary

You can ignore SQLite and use only:

- **`outputs/mlo_leads_YYYY-MM-DD.csv`** or **`outputs/company_leads_YYYY-MM-DD.csv`** — your “result set.”
- **`outputs/daily_summary_YYYY-MM-DD.md`** — what the agent did, any issues, and next steps.

---

## 4. What to check after the test

- Files exist under `workspace/outputs/` with today’s date in the name.
- CSV opens without errors and has columns like `full_name`, `current_company`, `score_total`, `score_breakdown`, and evidence/snippet columns.
- `daily_summary_YYYY-MM-DD.md` describes the run (e.g. how many leads, any budget or rate-limit notes).

If something failed (e.g. no search API), the daily summary should mention it; you can still do a dry run with a tiny hand-fed list to confirm scoring and export.

---

## 5. One-liner path reference

- **Outputs (your test results):** `openclaw_agent/workspace/outputs/`
- **Today’s MLO CSV:** `workspace/outputs/mlo_leads_YYYY-MM-DD.csv`
- **Today’s company CSV:** `workspace/outputs/company_leads_YYYY-MM-DD.csv`
- **Today’s summary:** `workspace/outputs/daily_summary_YYYY-MM-DD.md`

Replace `YYYY-MM-DD` with the date you ran the test (e.g. `2026-02-25`).
