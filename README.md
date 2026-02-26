# Mortgage Signals Agent (OpenClaw)

Research-only OpenClaw workspace for low-cost mortgage signal collection and lead scoring. The agent discovers active California MLOs from public sources, scores them on job-switch propensity, and exports ranked CSV outputs — no outreach, no fabrication.

---

## Quickstart

### Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| [OpenClaw](https://docs.openclaw.ai) | 2026.2.24+ | See below |
| [Ollama](https://ollama.ai) | Any | `brew install ollama` |
| Python | 3.11+ | `brew install python` |
| Chrome | Any | Required for browser relay |

**API keys required:**

| Key | Where to get it | Used for |
|-----|----------------|----------|
| `ANTHROPIC_API_KEY` | console.anthropic.com | LLM calls (Haiku default) |
| `BRAVE_API_KEY` | brave.com/search/api | Web search |
| `APOLLO_API_KEY` | apollo.io → API settings | Email enrichment (optional) |

---

### Step 1 — Install OpenClaw

```bash
# macOS
curl -fsSL https://install.openclaw.ai | bash
```

Then run the onboarding wizard:

```bash
openclaw onboard
```

This creates `~/.openclaw/openclaw.json` and walks you through auth setup.

---

### Step 2 — Install Ollama and pull the heartbeat model

```bash
brew install ollama
ollama pull llama3.2:3b
ollama serve   # keep running in a background terminal
```

This keeps the hourly heartbeat free (no Anthropic tokens used for health checks).

---

### Step 3 — Clone this repo and install Python deps

```bash
git clone <repo-url>
cd openclaw_agent
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

### Step 4 — Configure OpenClaw

Copy the example config and set your workspace path:

```bash
cp openclaw.json.example ~/.openclaw/openclaw.json
```

Open `~/.openclaw/openclaw.json` and update the workspace path:

```json
"workspace": "/absolute/path/to/openclaw_agent/workspace"
```

Then store your Anthropic key in OpenClaw's auth (do this once):

```bash
openclaw config set auth.anthropic.key YOUR_ANTHROPIC_API_KEY
```

> **Note:** Do not edit `~/.openclaw/agents/main/agent/auth.json` directly — OpenClaw overwrites it on each run. Always use `openclaw config set`.

---

### Step 5 — Set up environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in your keys:

```env
ANTHROPIC_API_KEY=sk-ant-api03-...
BRAVE_API_KEY=your-brave-key
APOLLO_API_KEY=your-apollo-key   # optional
```

---

### Step 6 — Start the gateway

```bash
openclaw gateway
```

The gateway runs on `http://localhost:18789`. Keep this terminal open.

To open the dashboard UI:

```bash
openclaw dashboard   # opens http://127.0.0.1:18789 in Chrome
```

---

### Step 7 — Set up the Chrome browser relay (for NMLS)

The agent can control Chrome to scrape NMLS Consumer Access. This requires the OpenClaw browser extension.

1. Install the extension into Chrome (one-time):

   ```bash
   openclaw browser extension install
   # Follow the printed instructions:
   # Chrome → chrome://extensions → Developer mode ON → Load unpacked
   # Select: ~/.openclaw/browser/chrome-extension
   ```

2. Pin the **OpenClaw Browser Relay** extension to the Chrome toolbar.

3. Open the extension options page and configure:
   - **Port:** `18792`
   - **Gateway token:** copy from `~/.openclaw/openclaw.json` → `gateway.auth.token`
   - Click **Save**

4. Navigate to any regular web page in Chrome (e.g. `google.com`), then click the extension icon. The badge should show **ON** and a banner will confirm "started debugging this browser."

> **Note:** NMLS Consumer Access (`nmlsconsumeraccess.org`) is behind Cloudflare and blocks automated access. The agent automatically falls back to Brave Search to discover real MLOs from LinkedIn, HousingWire, and public press releases. This is the reliable default path.

---

### Step 8 — Run Workflow A

Open the gateway dashboard or use the CLI:

**Via CLI:**

```bash
openclaw agent --agent main --session-id NEW --message "$(cat <<'EOF'
Run Workflow A from projects/mortgage-signals/RUNBOOK.md with a small batch.

Constraints:
- Use Haiku by default; escalate to Sonnet only for ambiguous dedupe/reasoning.
- Use NMLS as identity source for live leads. If NMLS is unavailable, fall back to Brave Search for real verified identities — do not fabricate.
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

**Via dashboard:** Open `http://localhost:18789`, go to **Chat**, and paste the prompt above.

Expected runtime: **2–3 minutes** for a 10-lead batch using Brave Search.

---

### Step 9 — Check outputs

```
workspace/projects/mortgage-signals/outputs/
  mlo_leads_2026-MM-DD.csv        ← ranked leads, verified identities
  daily_summary_2026-MM-DD.md     ← run summary, budget, blockers
```

Validate:
- `nmls_id` values are real and cross-referenced
- No `-mock` suffixes in LinkedIn URLs
- `recommended_next_action` is `Outreach`, `Monitor`, or `Ignore` (never blank)
- `daily_summary` includes search count and budget used

---

## Architecture

```
openclaw_agent/
├── workspace/
│   ├── SOUL.md             # Agent persona and values
│   ├── IDENTITY.md         # Agent name and role
│   ├── AGENTS.md           # Behavior rules and fail-closed policy
│   ├── TOOLS.md            # Available tools and usage policy
│   ├── USER.md             # User preferences
│   ├── HEARTBEAT.md        # Hourly health check template
│   ├── memory/             # Daily session notes (auto-generated, not committed)
│   ├── outputs/            # Templates and daily summaries
│   └── projects/
│       └── mortgage-signals/
│           ├── RUNBOOK.md          # Workflow steps A and B
│           ├── SCORING_RUBRIC.md   # How leads are scored
│           ├── SIGNAL_LIBRARY.md   # Signal definitions and weights
│           └── outputs/            # CSV and MD outputs (not committed)
├── workspace/agent/        # Python scaffold (optional CLI runner)
├── openclaw.json.example   # Config template
├── .env.example            # Environment variable template
└── requirements.txt        # Python dependencies
```

---

## Cost model

| Component | Cost |
|-----------|------|
| Haiku (default) | ~$0.001–0.003 per run |
| Sonnet (escalation only) | ~$0.01–0.05 per run |
| Heartbeat (Ollama) | Free |
| Brave Search | Free tier: 2,000 searches/mo |
| Apollo enrichment | Free tier: ~50 exports/mo (email only; phone requires paid plan) |

Daily budget target: **$5**. Monthly target: **$200**. Agent warns at 75%.

---

## Guardrails

- **Fail-closed identity:** Agent never fabricates names, NMLS IDs, or LinkedIn URLs. If identity cannot be verified, it sets `recommended_next_action=insufficient_evidence` or asks for a seed CSV.
- **Research-only:** Agent discovers and scores leads. All outreach is a human action.
- **Rate limits enforced:** ≥10s between searches, max 5 searches per batch then 2-minute cooldown.
- **No paid services by default:** Enrichment (Apollo, Hunter) is disabled unless explicitly enabled.

---

## Known limitations

| Issue | Status |
|-------|--------|
| NMLS Consumer Access blocked by Cloudflare | Agent falls back to Brave Search automatically |
| OpenClaw browser relay drops multi-step control | Use Brave Search path (reliable); browser useful for single-step navigation only |
| `auth.json` overwritten by OpenClaw on each run | Always set keys via `openclaw config set`, not by editing the file directly |
| Apollo free tier has no phone numbers | Upgrade to Apollo Basic ($49/mo) for direct/mobile phone exports |
