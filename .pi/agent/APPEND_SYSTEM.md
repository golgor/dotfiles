Favor clear, simple, readable solutions.

## Agent-native CLIs

Prefer these agent-native CLIs over MCP servers or raw CLIs:

- `gh-axi` for GitHub
- `obsidian-axi` for Obsidian vaults
- `notion-axi` for Notion
- `gws-axi` for Google Workspace (Gmail, Calendar, Docs, Drive, Slides, Sheets)
- `slack-axi` for Slack
- `pg-axi` for PostgreSQL
- `superbee` for cross-session agent memory

Run bare `<tool>` for live state or `<tool> --help` for the command surface.

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
