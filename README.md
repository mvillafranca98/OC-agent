# Mortgage Signals Agent (OpenClaw)

Research-only OpenClaw agent for EPA mortgage recruiting: ranked lead lists for **MLOs likely to move** and **mortgage companies potentially distressed or ready to sell**, with evidence and explainable scoring.

## What this repo contains

- **workspace/** — OpenClaw workspace files (SOUL, USER, IDENTITY, AGENTS, TOOLS, HEARTBEAT, memory/, outputs/, projects/mortgage-signals/).
- **openclaw.json.example** — Example config: Haiku default, Ollama heartbeat, model aliases. Copy and adapt to `~/.openclaw/openclaw.json`; do not commit secrets.
- **requirements.txt** — For supporting scripts (exporters, signal scoring, enrichment, CSV/Sheet tooling). OpenClaw is the runtime; install it separately.
- **README.md** — This file.

## Setup (Phase 0)

1. **Machine** — Use a dedicated or controlled machine. Install [OpenClaw](https://docs.openclaw.ai) and run `openclaw setup` / `openclaw onboard` as needed.
2. **Ollama** — Install [Ollama](https://ollama.ai), then pull a small model for heartbeat (e.g. `ollama pull llama3.2:3b`) so idle checks use no paid API tokens.
3. **Config** — Copy `openclaw.json.example` to `~/.openclaw/openclaw.json`. Set:
   - Default model to Claude Haiku (or current Haiku model id).
   - Heartbeat: `every` (e.g. `1h`), `model` to your Ollama model (e.g. `ollama/llama3.2:3b`), and the example prompt.
   - Ollama provider with `api: "openai-responses"` and correct `baseUrl` (e.g. `http://127.0.0.1:11434/v1`).
   - Model aliases: `haiku`, `sonnet`, (optional) `opus`.
4. **Workspace** — Point OpenClaw at this repo’s workspace:
   - Either copy the contents of `workspace/` into `~/.openclaw/workspace`, or
   - Set `agents.defaults.workspace` in `openclaw.json` to the full path of this repo’s `workspace/` directory.
5. **Secrets** — Store in env (e.g. `.env`) or OpenClaw auth; never commit. Typical: `ANTHROPIC_API_KEY`, search API key (e.g. Brave), optional enrichment API key (e.g. Hunter.io).

## Running (Phase 1–2)

- **Workflow A (MLO leads):** See `workspace/projects/mortgage-signals/RUNBOOK.md`. Define geography/role → crawl → dedupe → score → optional enrich → export `outputs/mlo_leads_YYYY-MM-DD.csv` and `outputs/daily_summary_YYYY-MM-DD.md`.
- **Workflow B (Distressed companies):** Same RUNBOOK. Define geography/company types → crawl → dedupe → score distress → export `outputs/company_leads_YYYY-MM-DD.csv` and update daily summary.

Run via OpenClaw (e.g. start gateway and ask the agent to run the appropriate workflow). Both workflows are research-only; no autonomous outreach.

## Workspace layout

| Path | Purpose |
|------|--------|
| SOUL.md, USER.md, IDENTITY.md | Loaded every session; persona, mission, identity. |
| AGENTS.md | Session init, memory discipline, model routing, rate limits, workflows. |
| TOOLS.md | Tool usage, rate limits, safety. |
| HEARTBEAT.md | Optional checklist for heartbeat runs. |
| memory/ | Daily memory `memory/YYYY-MM-DD.md`. |
| outputs/ | `mlo_leads_*.csv`, `company_leads_*.csv`, `daily_summary_*.md`. |
| projects/mortgage-signals/ | SIGNAL_LIBRARY.md, SCORING_RUBRIC.md, RUNBOOK.md. |

## QA checklist

- **Session start:** Context small (~2–8KB typical); only SOUL, USER, IDENTITY, today’s memory.
- **Heartbeat:** No paid token usage (Ollama only).
- **Rate limiting:** On 429, agent stops, waits 5 min, retries; backoff documented in AGENTS.md/TOOLS.md.
- **Lead outputs:** Schema consistent; CSVs open in Google Sheets; no broken formatting.
- **Scoring:** Score breakdown sums correctly; breakdown present per lead.
- **Dedupe:** Same person/company not duplicated across sources.
- **Safety:** Agent refuses send/purchase without explicit confirmation; blocked actions noted for audit.

## Supporting scripts

Use `requirements.txt` for Python scripts that support the agent (e.g. CSV export, signal scoring, enrichment API clients). Install with `pip install -r requirements.txt` in the environment where those scripts run.

## License and compliance

Use in line with your org’s compliance and IT policies. The agent is research-only and human-in-the-loop; no autonomous emailing or purchases.
