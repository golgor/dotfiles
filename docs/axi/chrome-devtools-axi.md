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
- Google Chrome, stable channel (`/opt/google/chrome/chrome`), tracked as the
  host package `pacman:google-chrome` in `mise.toml`. chrome-devtools-mcp
  launches that channel by default and does not detect Omarchy's Chromium; on a
  Chromium-only machine every command fails with `BRIDGE_NOT_READY`.
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

That default session is shared: two agents running multi-step flows at once
drive the same browser and act on each other's page state. Give each concurrent
agent its own session:

```sh
CHROME_DEVTOOLS_AXI_SESSION=<unique-name> chrome-devtools-axi open <url>
```

Each name gets its own bridge, port, and headless Chrome. Do not export
`CHROME_DEVTOOLS_AXI_PORT` globally: it forces every session onto one port and
the second bridge fails to start.
