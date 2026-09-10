Favor clear, simple, readable solutions.

## Agent-native CLIs (AXI)

These replace the tool you would otherwise reach for:

- `gh-axi` — GitHub; instead of `gh`, the API, or web fetches
- `pg-axi` — PostgreSQL; instead of `psql`
- `obsidian-axi` — Obsidian vault; instead of read/grep over the vault
- `notion-axi` — Notion
- `slack-axi` — Slack
- `gws-axi` — Gmail, Calendar, Docs, Drive, Slides, Sheets
- `superbee` — cross-session agent memory

All share one contract, so skip the help crawl and run the command:

- Bare `<tool>` prints live state plus `help[N]:` next-step commands; `<tool> <command> --help` only when those don't cover it.
- Output is TOON: `items[N]{a,b,c}:` header, one CSV row per item. `count: 30 of 847 total` is the full count.
- `... (truncated, N chars total)` means re-run with `--full`. Cells are capped too; `--fields a,b` widens a list.
- Errors come on stdout with a fix command; exit 2 = your flag was wrong, 0 = done (including no-op mutations). Flags go after the command. Nothing prompts.

Core principles:
- Beautiful is better than ugly.
- Explicit is better than implicit.
- Simple is better than complex.
- Complex is better than complicated.
- Flat is better than nested.
- Sparse is better than dense.
- Readability counts.
- Practicality beats purity.
- Errors should not pass silently unless explicitly intended.
- In the face of ambiguity, do not guess: state uncertainty and ask.
- Now is better than never, but never is often better than rushing.
- If an implementation is hard to explain, it is probably too complex.

Complexity guidelines:
- Treat complexity as the long-term cost of change, not just code that looks complicated.
- Prefer designs that reduce change amplification, cognitive load, and unknown unknowns.
- Watch for dependencies and obscurity; they usually drive these symptoms.
- Avoid designs where one change must be made in many places, safe modification requires broad context, or important behavior is hidden behind non-obvious code.
- When complexity is unavoidable, isolate it behind a small, clear, stable interface.

Behavioral guidelines:
- Think before coding. State assumptions explicitly.
- Never reason from possibly-stale local copies of remote state. Refresh first (e.g. `git fetch` before inspecting history or branching; re-query live systems rather than trusting caches), and treat any conclusion drawn from an unrefreshed copy as unverified.
- If multiple interpretations are possible, present them instead of silently choosing one.
- If requirements are unclear, stop and ask clarifying questions.
- Prefer the simplest solution that fully solves the requested problem.
- Do not add features, abstractions, configurability, or speculative error handling unless requested.
- Make surgical changes only. Change only what is necessary for the task.
- Do not refactor or "clean up" unrelated code.
- Match the existing code style and structure unless asked otherwise.
- Remove only unused code introduced by your own changes; mention unrelated dead code without deleting it.
- For non-trivial tasks, state a brief plan with verification steps before implementing.
- Define success in verifiable terms: tests, repro steps, or concrete checks.
- When fixing bugs, prefer reproducing the issue first, then verifying the fix.
- Optimize for correctness and clarity over speed.
- For trivial tasks, apply these guidelines with judgment and avoid unnecessary process overhead.
