# Setup Instructions — Mortgage Signals Agent

Follow these steps exactly, in order, on a fresh machine.

---

## Step 1 — Install OpenClaw

OpenClaw is the AI agent runtime that powers this project.

```bash
# macOS
curl -fsSL https://install.openclaw.ai | bash
```

After installation, run the onboarding wizard. This creates `~/.openclaw/openclaw.json` and walks you through initial auth setup:

```bash
openclaw onboard
```

---

## Step 2 — Install Ollama and pull the heartbeat model

Ollama runs a local LLM that handles hourly health checks for free (no Anthropic tokens used).

```bash
brew install ollama
ollama pull llama3.2:3b
```

Keep Ollama running in a background terminal whenever you use the agent:

```bash
ollama serve
```

---

## Step 3 — Install Python 3.11+

If you don't have Python 3.11 or newer:

```bash
brew install python
```

Verify:

```bash
python3 --version   # should print 3.11 or higher
```

---

## Step 4 — Clone the repo and create a Python virtual environment

```bash
git clone <repo-url>
cd openclaw_agent
python3 -m venv venv
source venv/bin/activate
```

---

## Step 5 — Install Python dependencies

```bash
pip install -r requirements.txt
```

---

## Step 6 — Create your `.env` file

Copy the example file:

```bash
cp .env.example .env
```

Open `.env` and fill in your API keys:

```env
ANTHROPIC_API_KEY=sk-ant-api03-...   # console.anthropic.com
BRAVE_API_KEY=your-brave-key         # brave.com/search/api
APOLLO_API_KEY=your-apollo-key       # apollo.io → API settings (optional)
```

Where to get each key:

| Key | Link | Required? |
|-----|------|-----------|
| `ANTHROPIC_API_KEY` | https://console.anthropic.com | Yes |
| `BRAVE_API_KEY` | https://brave.com/search/api | Yes (free tier: 2,000 searches/mo) |
| `APOLLO_API_KEY` | Apollo.io → Settings → API | Optional (email enrichment) |

---

## Step 7 — Configure OpenClaw

Copy the example config to OpenClaw's config directory:

```bash
cp openclaw.json.example ~/.openclaw/openclaw.json
```

Open `~/.openclaw/openclaw.json` and update the `workspace` path to your absolute path:

```json
"workspace": "/absolute/path/to/openclaw_agent/workspace"
```

Then add your Brave API key in the same file under `tools.web.search.apiKey`.

Finally, store your Anthropic key in OpenClaw's auth (do this once — do NOT edit `auth.json` directly, OpenClaw overwrites it):

```bash
openclaw config set auth.anthropic.key YOUR_ANTHROPIC_API_KEY
```

---

## Step 8 — Start the OpenClaw gateway

The gateway must be running before you can send any agent commands. Open a dedicated terminal and run:

```bash
openclaw gateway
```

The gateway runs on `http://localhost:18789`. Keep this terminal open for the duration of your session.

To open the dashboard UI in Chrome:

```bash
openclaw dashboard
```

---

## Step 9 — Run the agent

**Option A — via the dashboard**

Open `http://localhost:18789` in Chrome, go to **Chat**, and paste the prompt from `QUICK_TEST.md`.

**Option B — via CLI**

```bash
openclaw agent --agent main --session-id NEW --message "$(cat <<'EOF'
Run Workflow A from projects/mortgage-signals/RUNBOOK.md with a small batch.

Constraints:
- Use Haiku by default; escalate to Sonnet only for ambiguous dedupe/reasoning.
- Use NMLS as identity source for live leads. If NMLS is unavailable, fall back to Brave Search — do not fabricate.
- Use free search + direct scraping by default (Brave + public pages).
- Keep enrichment disabled by default (no paid email APIs).
- Enforce rate limits and budget policy.

Output:
- projects/mortgage-signals/outputs/mlo_leads_YYYY-MM-DD.csv
- projects/mortgage-signals/outputs/daily_summary_YYYY-MM-DD.md
EOF
)"
```

**Option C — one-command local test (Python pipeline, no gateway needed)**

Make sure your venv is active and `.env` is filled in, then:

```bash
make test-live
```

Expected runtime: **2–3 minutes** for a 10-lead batch.

---

## Step 10 — Check outputs

After a run completes, look in:

```
workspace/projects/mortgage-signals/outputs/
  mlo_leads_YYYY-MM-DD.csv        ← ranked leads with NMLS IDs
  daily_summary_YYYY-MM-DD.md     ← run summary, budget, blockers
```

Validate:
- `nmls_id` values are real (not sequential like `1234567`)
- `recommended_next_action` is `Outreach`, `Monitor`, or `Ignore`
- `evidence_summary` cites real sources with dates
- No `-mock` suffixes anywhere

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `Error: Pass --to, --session-id, or --agent` | Add `--agent main` to the CLI command |
| Gateway not responding | Run `openclaw gateway` in a terminal and keep it open |
| Agent returns mock data | Re-run with an explicit live instruction; confirm `DRY_RUN_DATA.md` isn't being referenced unintentionally |
| `auth.json` reverts to old key | Always use `openclaw config set auth.anthropic.key YOUR_KEY` — never edit the file directly |
| Ollama heartbeat errors | Run `ollama serve` in a background terminal and confirm `llama3.2:3b` is pulled |
| NMLS lookup fails (Cloudflare) | Normal — agent falls back to Brave Search automatically |
