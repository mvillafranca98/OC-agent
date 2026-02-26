# Mortgage Signals Agent (OpenClaw)

Low-cost OpenClaw workspace for mortgage lead intelligence.

Default behavior:
- Paid API calls only for Anthropic LLM usage.
- Heartbeat runs on local Ollama.
- Haiku is default; Sonnet only for complex escalations.
- Free search + direct scraping by default.
- Email enrichment disabled by default.

## Repo layout

- `workspace/` — OpenClaw working context.
- `workspace/agent/` — Python scaffold (pipelines/providers/scoring/storage).
- `openclaw.json.example` — Haiku-first + Ollama heartbeat config template.
- `requirements.txt` — Free-default dependency set.

## Setup

1. Install OpenClaw and run onboarding:
   - `openclaw onboard`
2. Install Ollama and start local model:
   - `ollama pull llama3.2:3b`
   - `ollama serve`
3. Copy OpenClaw config template:
   - `cp openclaw.json.example ~/.openclaw/openclaw.json`
4. Set required key:
   - `ANTHROPIC_API_KEY`
5. Copy env template for Python scaffold:
   - `cp .env.example .env`

## Provider feature flags

Set in `.env`:

```env
SEARCH_PROVIDER=duckduckgo
ENRICHMENT_PROVIDER=none
ALLOW_PAID_PROVIDERS=false
```

If `ALLOW_PAID_PROVIDERS=false`, paid adapters must not run.

## Running

Agent-guided workflows:
- `workspace/projects/mortgage-signals/RUNBOOK.md`

Optional Python scaffold CLI:

```bash
python3 -m workspace.agent.main --workflow mlo --input-csv /absolute/path/to/mlo.csv
python3 -m workspace.agent.main --workflow company --input-csv /absolute/path/to/company.csv
```

Default output location:
- `workspace/projects/mortgage-signals/outputs/`

