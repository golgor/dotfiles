# OMP marketplace plugins

Plugins installed into OMP with `omp plugin ...`, one section each. This state lives in
`~/.omp/plugins` (machine-local) and is not owned by mise `[dotfiles]`, so each machine installs
its own copy with the commands below.

## ponytail

"Lazy senior dev" ruleset — YAGNI ladder, stdlib-first, delete-over-add — injected into every
turn's system prompt, plus `/ponytail` commands (`lite|full|ultra|off`, `-review`, `-audit`,
`-debt`, `-gain`, `-help`). Source: https://github.com/DietrichGebert/ponytail

```sh
omp plugin marketplace add DietrichGebert/ponytail
omp plugin install ponytail@ponytail
# then start a fresh session: extensions load at session start, not on /reload-plugins
```

Remove: `omp plugin uninstall ponytail@ponytail && omp plugin marketplace remove ponytail`.

Loads via the legacy `pi.extensions` fallback. ponytail ships adapters for ~20 harnesses, none
targeting OMP: its Claude/Codex command-hooks are inert here. But its bundled Pi extension
(`pi-extension/index.js`, declared in the package's `pi.extensions`) is a real OMP `ExtensionAPI`
module, and OMP loads it through that manifest key. That extension carries the whole behaviour:
per-turn injection via `before_agent_start` → `{ systemPrompt }`, the `/ponytail` commands, and
mode state persisted across `omp -c`.

Verify by asking the running agent to list its system-prompt section headers — `# Ponytail`,
`## The ladder`, etc. appear after the base sections. The system prompt is assembled per request
and never stored in the session file, so the agent's own report is the check.

Cosmetic quirk, works anyway: the extension reads `event.systemPrompt` as a string, but OMP passes
a `string[]`, so the base prompt's segments get comma-joined before the ruleset is appended. The
model reads it fine. A one-line upstream fix (`[...sp, seg]`) would tidy it, but upstream is stale
(100+ open PRs), so it stays as-is.
