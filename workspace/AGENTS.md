# Agent operating instructions

## SESSION INITIALIZATION RULE

On every session start:
1) Load ONLY:
   - SOUL.md
   - USER.md
   - IDENTITY.md
   - memory/YYYY-MM-DD.md (if exists)
2) DO NOT auto-load:
   - MEMORY.md
   - Session history
   - Prior messages
   - Previous tool outputs
3) If user asks about prior context:
   - Use memory_search() on demand
   - Pull only the relevant snippet with memory_get()
   - Do not load the whole file
4) At end of session update memory/YYYY-MM-DD.md with:
   - What you worked on
   - Decisions made
   - Leads generated
   - Blockers
   - Next steps

## MODEL SELECTION RULE

Default: Always use Haiku.

Switch to Sonnet ONLY for:
- Complex reasoning / ambiguity resolution
- Scoring rubric changes
- Architecture decisions
- Production code review

When in doubt: try Haiku first.

## HEARTBEAT RULE

Heartbeat must run on local Ollama (no paid API calls for heartbeat).

## RATE LIMITS & BUDGETS

- 5 seconds minimum between any paid API calls
- 10 seconds between web searches/scrapes
- Max 5 searches per batch, then 2-minute break
- If you hit a 429: STOP, wait 5 minutes, retry

DAILY BUDGET: $5 (warn at 75%)
MONTHLY BUDGET: $200 (warn at 75%)

## SEARCH & ENRICHMENT COST RULE

- DO NOT use paid search APIs (Brave, SerpAPI, etc.) unless explicitly enabled via feature flag.
- DO NOT use Apollo.io.
- Default to free search + direct web scraping.
- Email enrichment is OPTIONAL and disabled by default.

## DATA INTEGRITY RULE

- Never fabricate `full_name`, `nmls_id`, `linkedin_url`, employer, evidence URLs, or timestamps.
- If identity is unverifiable or evidence is ambiguous, mark `insufficient_evidence`.
- If NMLS/browser is unavailable, fail closed and request seed data or run dry-run only.
