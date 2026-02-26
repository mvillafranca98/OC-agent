# Tool usage and constraints

## Default tool stack (lowest-cost mode)

- **Anthropic model API** for core reasoning (Haiku by default).
- **Ollama heartbeat** for local idle checks (no paid heartbeat calls).
- **DuckDuckGo search (default)** for public evidence lookup.
- **Direct public-page scraping** (company sites, news, job boards, review sites).
- **Browser to NMLS Consumer Access** for real, licensed MLO identities.

Do not introduce paid connectors by default.

## Allowed tools and usage

- **Search** — Use free search (DuckDuckGo HTML strategy by default). Respect rate limits below.

- **Scraping** — Scrape only public pages required for evidence extraction. Prefer lightweight request-based scraping first; use browser rendering only for JS-heavy pages.

- **NMLS Consumer Access (primary identity source)** — Use browser tool to extract real, licensed MLOs:
  1. Open `https://www.nmlsconsumeraccess.org/FieldSearch.aspx`
  2. Set Individual search, State target, License Type = Mortgage Loan Originator, Status = Active
  3. Extract: `full_name`, `nmls_id`, `employer_name`, `city`, `state`
  4. Paginate until requested batch size is reached

- **Fail-closed rule when NMLS/browser is unavailable**:
  - Do not synthesize names or IDs.
  - Ask user for seed data (CSV/list), or run dry-run scoring only.
  - Log blocker in daily summary.

- **Evidence integrity**:
  - Every lead must include a verifiable identity source and evidence URLs/snippets for scored signals.
  - If evidence is ambiguous or missing, set `recommended_next_action=insufficient_evidence`.
  - Never guess LinkedIn URLs or contact info.

- **Memory** — Use `memory_search()` and `memory_get()` for targeted recall only.

- **File write** — Write only under:
  - `projects/mortgage-signals/outputs/` for CSVs and daily summaries
  - `memory/` for daily memory notes
  - `projects/mortgage-signals/` only when user explicitly asks to update docs

## Provider feature flags (required)

- `SEARCH_PROVIDER=duckduckgo`
- `ENRICHMENT_PROVIDER=none`
- `ALLOW_PAID_PROVIDERS=false`

If `ALLOW_PAID_PROVIDERS=false`, paid providers must not run.

## Optional add-ons (off by default)

Paid search/enrichment adapters are optional integrations and remain disabled unless explicitly enabled by feature flag and user approval.

## Rate limits (must enforce)

- >=5s between API calls
- >=10s between search requests
- Max 5 searches per batch, then ~2 minutes cooldown
- On 429: wait 5 minutes, retry once; if repeated, log and pause

## Safety

- Research-only. No autonomous outreach, purchases, or unauthorized access.
- If user asks for blocked actions, refuse and log the blocked action.
