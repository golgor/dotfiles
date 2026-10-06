# chrome-devtools-axi

Browser automation for agents: an AXI wrapper around
[chrome-devtools-mcp](https://www.npmjs.com/package/chrome-devtools-mcp) that
opens pages, clicks through flows, takes screenshots, and reads console and
network output, with TOON output and next-step hints.

- Source: <https://github.com/kunchenguid/chrome-devtools-axi>
- npm: [`chrome-devtools-axi`](https://www.npmjs.com/package/chrome-devtools-axi)
- Command: `chrome-devtools-axi`

Firstmate's bootstrap checks for it and uses it for browser work, such as
checking how a rendered HTML page looks.

## Requirements

- Node 20+ (package `engines`).
- A local Chrome/Chromium that chrome-devtools-mcp can launch headless.
- No auth, no account, no token.

## Install

Tracked via the mise npm backend:

```toml
# .config/mise/config.toml
"npm:chrome-devtools-axi" = "latest"
```

```sh
mise install
chrome-devtools-axi            # live browser state + usage guidance
```

The package clears aube's low-download gate on its own (~9k downloads/week on
2026-10-06), so it needs **no** entry in `.config/aube/config.toml`.

## Session hook

Optional and machine-local, like the other tools in [README.md](README.md):

```sh
chrome-devtools-axi setup hooks
```

It writes a SessionStart hook into Claude Code, Codex, and OpenCode config.
Restart the agent session afterwards.

## How it runs

The CLI talks to a persistent local bridge on `localhost:9224`, which keeps one
chrome-devtools-mcp session alive across invocations.
