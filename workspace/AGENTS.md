# Agent operating instructions

## Session initialization and memory discipline (FR-1)

**On session start, treat as loaded:**

- SOUL.md, USER.md, IDENTITY.md
- `memory/YYYY-MM-DD.md` (today’s date) if it exists

**Do not assume in context:**

- MEMORY.md
- Full session history or prior messages
- Previous tool outputs

**When you need prior context:** Use `memory_search()` or `memory_get()` to fetch only the snippets you need. Do not assume the full history is in the prompt.

**End of session (or before long breaks):** Update `memory/YYYY-MM-DD.md` with: work done, decisions, leads produced, blockers, and next steps. Keep it concise.

**Acceptance:** Session context should stay small (~2–8KB typical on a new session). Memory use is explicit and scoped.

---

## Model routing (FR-2)

**Default (Haiku):** Use for routine work:

- Extraction, summarization, simple classification
- CSV shaping and formatting
- Single-signal scoring and evidence capture

**Escalate to Sonnet** when:

- Refining multi-signal scoring rubrics or resolving conflicting evidence
- Quality-checking outreach drafts
- Ambiguous entity dedupe or identity resolution (same person/company across sources)
- Complex "why did we rank this lead?" reasoning

**Opus:** Only for rare hardest cases (e.g. very ambiguous merge or policy edge case).

**Logging:** When you switch to Sonnet (or Opus), note the reason briefly in the daily summary or in `memory/YYYY-MM-DD.md` (e.g. "Escalated to Sonnet: dedupe of two MLO profiles"). Target: 80%+ of actions on Haiku.

---

## Rate limits and budget (FR-4)

**API and search discipline (enforce via your behavior):**

- ≥5 seconds between API calls (e.g. search, enrichment).
- ≥10 seconds between search requests.
- Max 5 searches per batch, then a ~2 minute break before the next batch.
- If you receive a 429 (rate limit): stop, wait 5 minutes, then retry once. If it happens again, note it in the daily summary and pause further search until the next run or user guidance.

**Budget:**

- Respect daily (and optionally monthly) budget. If you have a daily cap (e.g. $5), treat 75% of that as a warning threshold: when approaching it, note a budget warning in the daily summary and in memory.
- Check usage in the Anthropic console when documented in the RUNBOOK; log warnings in the daily summary.

---

## Workflows

**Workflow A — MLO leads:** See `projects/mortgage-signals/RUNBOOK.md`. Steps: define geography/role → crawl sources → normalize/dedupe → score (SIGNAL_LIBRARY + SCORING_RUBRIC) → optional enrichment → export `outputs/mlo_leads_YYYY-MM-DD.csv` and update `outputs/daily_summary_YYYY-MM-DD.md`.

**Workflow B — Distressed companies:** Same RUNBOOK. Steps: define geography/company types → crawl news/reviews/lists → identify/dedupe → score distress → export `outputs/company_leads_YYYY-MM-DD.csv` and update the daily summary.

Both workflows are research-only and produce ranked lists with evidence; no autonomous outreach.

---

## Safety (FR-8)

- Refuse to send emails, InMails, or any outbound message without explicit user confirmation.
- Refuse purchases and unauthorized access to private systems.
- When you block an action, note it (e.g. in `memory/YYYY-MM-DD.md` or daily summary): "Blocked: [action]; reason: no explicit confirmation." This serves as a simple audit trail.
