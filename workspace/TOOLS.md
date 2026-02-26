# Tool usage and constraints

## Allowed tools and usage

- **Search** — Use the configured search API (Brave Search; `BRAVE_API_KEY` is set) for public sources: news, job boards, company sites, NMLS/registry where available, reviews. Respect rate limits below.

- **NMLS Consumer Access — primary source for real individuals (browser required)** — Use the browser tool to navigate NMLS Consumer Access and extract real, licensed MLO names. This is the authoritative public registry; every name returned is a real, currently-licensed mortgage loan officer. Do NOT invent fictional people — every lead must come from NMLS or another verifiable public source.

  Steps:
  1. Open browser to: `https://www.nmlsconsumeraccess.org/FieldSearch.aspx`
  2. Set: Individual search, State = target state, License Type = Mortgage Loan Originator, Status = Active
  3. Extract from results: full_name, nmls_id, employer_name, city, state
  4. Collect the requested batch size (e.g. 10, 25, 50). Use pagination if needed.
  - NMLS does NOT provide email, phone, or LinkedIn URL — those must come from enrichment (see below).
  - NMLS ID is valuable: include it in every lead row for verification purposes.

- **Apollo.io enrichment (email lookup, secondary)** — `APOLLO_API_KEY` is set. After getting real names from NMLS, attempt to enrich each lead with email via Apollo's people/match endpoint. Phone numbers require a paid Apollo plan — leave `phone` blank on free tier; do not guess.

  Enrichment call (use `exec` with a Python one-liner):
  ```
  POST https://api.apollo.io/v1/people/match
  Headers: Content-Type: application/json, X-Api-Key: <APOLLO_API_KEY>
  Body: { "first_name": "<first>", "last_name": "<last>", "organization_name": "<employer>", "reveal_personal_emails": true }
  ```
  Returns: `email`, `linkedin_url`, `phone_numbers` (paid only). If the endpoint returns 403, note it in the daily summary and leave email blank — do not fabricate.

- **LinkedIn URL lookup via Brave Search (fallback)** — If Apollo enrichment is unavailable, search `"<full name>" "<employer>" mortgage loan officer linkedin site:linkedin.com` via Brave Search. Only record a LinkedIn URL if the search returns a direct, unambiguous match to that individual. Do not guess or construct URLs.

- **Contact enrichment note** — Never use contact info for autonomous outreach. Lookup/verification only. Store in CSV columns: `email`, `email_verification_status` (verified/unverified/blank), `phone`, `phone_type`.
- **Memory** — `memory_search()` for semantic recall; `memory_get()` for targeted reads of `memory/YYYY-MM-DD.md` or other memory files. Use these when you need prior context instead of assuming it is in the prompt.
- **File write** — Write only under:
  - `outputs/` — CSVs and daily summaries (`mlo_leads_YYYY-MM-DD.csv`, `company_leads_YYYY-MM-DD.csv`, `daily_summary_YYYY-MM-DD.md`).
  - `memory/` — Daily memory file `memory/YYYY-MM-DD.md` and any other memory files you are instructed to update.
  - `projects/mortgage-signals/` — Only when explicitly updating project docs (e.g. RUNBOOK, signal library) per user request. Do not change SIGNAL_LIBRARY or SCORING_RUBRIC casually; they are stable and cache-friendly.
- **Read** — You may read any file under the workspace to follow RUNBOOK, rubrics, and signal libraries.

## Rate limits (you must enforce)

- ≥5s between API calls (including search).
- ≥10s between search requests.
- Max 5 searches per batch; then wait ~2 minutes before the next batch.
- On 429: stop, wait 5 minutes, retry once. If 429 persists, record in daily summary and pause search until next run or user says otherwise.

## Safety

- Research-only. Do not use tools to send email, make purchases, or access systems that require authorization unless the user has explicitly confirmed.
- If a tool or a user request would cause an outbound send or purchase, refuse and log the blocked action in memory or the daily summary.
