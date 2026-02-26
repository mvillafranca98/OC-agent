# User and mission context

## Primary users

- **Recruiters / Ops** — Need ranked lead lists with evidence and minimal tech friction. They use the outputs to decide who to contact and how to prioritize.
- **Sales leadership** — Need high-level pipeline visibility and credible, explainable lead quality so they can trust the pipeline.

## Stakeholders

- Direct superior (implementation owner)
- Compliance / IT (if deployed on a controlled machine; they care about safety controls and auditability)

## Success metrics (EPA)

- **Quality:** ≥70% of "High score" leads are deemed "worth outreach" by recruiter review. ≥95% of leads include at least 2 sources or 1 high-confidence source with a clear snippet.
- **Efficiency:** Idle cost near zero (heartbeat uses local Ollama). Per-run budget adherence (e.g. ≤$5/day warning threshold).
- **Operational:** Time-to-first-ranked-list under ~30 minutes from a fresh run (depends on batch size).

## Mission

Automate research and signal detection to produce prioritized lead lists and outreach-ready briefs for mortgage recruiting: MLOs likely to move, and mortgage companies that may be distressed or ready to sell. All outputs are for human review; no autonomous outreach.
