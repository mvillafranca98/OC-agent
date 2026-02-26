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
- `ENRICHMENT_PROVIDER=apollo` (or `none` to disable)
- `ALLOW_PAID_PROVIDERS=true` (required when ENRICHMENT_PROVIDER=apollo)

If `ALLOW_PAID_PROVIDERS=false`, paid providers must not run.

## Email enrichment (enabled when ALLOW_PAID_PROVIDERS=true)

Two providers are available. Set `ENRICHMENT_PROVIDER` to choose one.

**Hunter.io** (`ENRICHMENT_PROVIDER=hunter`, `HUNTER_API_KEY` required)
- `GET https://api.hunter.io/v2/email-finder?full_name={name}&domain={domain}&api_key={key}`
- Free tier: 25 email searches/month
- Returns verified work email only — no phone
- Enforce ≥5s between calls
- If no match, leave `email` blank — do not guess or fabricate

**Apollo.io** (`ENRICHMENT_PROVIDER=apollo`, `APOLLO_API_KEY` required)
- `POST https://api.apollo.io/v1/people/match` with `name` and `domain`
- Requires paid plan (~$49/mo) — free tier returns API_INACCESSIBLE error
- Returns email + phone on paid plan
- Enforce ≥5s between calls
- If no match or error, leave `email` and `phone` blank

Both providers add `email` and `phone` columns to the output CSV.

## Optional add-ons (off by default)

Paid search adapters remain disabled unless explicitly enabled by feature flag and user approval.

## Rate limits (must enforce)

- >=5s between API calls
- >=10s between search requests
- Max 5 searches per batch, then ~2 minutes cooldown
- On 429: wait 5 minutes, retry once; if repeated, log and pause

## Safety

- Research-only. No autonomous outreach, purchases, or unauthorized access.
- If user asks for blocked actions, refuse and log the blocked action.
