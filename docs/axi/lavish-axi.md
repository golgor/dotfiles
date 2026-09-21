# lavish-axi

Lavish Editor: opens an agent-written HTML artifact (plan, comparison, diagram,
report) in a local browser so the human can annotate elements and text, edit
Mermaid diagrams as whiteboards, and send that feedback back to the agent.
Sessions are keyed by the artifact's canonical file path, so there are no
session IDs to track.

- Source: <https://github.com/kunchenguid/lavish-axi>
- npm: [`lavish-axi`](https://www.npmjs.com/package/lavish-axi)
- Command: `lavish-axi`

## Requirements

- **Node 22+** (package `engines`), stricter than the Node 20+ the other tools
  here need. The global `node` is `latest`, so this is satisfied.
- A desktop browser on the machine running the CLI.
- No auth, no account, no token. Only `lavish-axi share` talks to a third-party
  service, and it is opt-in per command.

## Install

Tracked via the mise npm backend:

```toml
# .config/mise/config.toml
"npm:lavish-axi" = "latest"
```

```sh
mise install
lavish-axi            # lists open sessions + usage guidance
```

The package clears aube's low-download gate on its own (~9k downloads/week), so
it needs **no** entry in `.config/aube/config.toml`.

## Usage shape

```sh
lavish-axi artifact.html         # open/resume a review session
lavish-axi poll artifact.html    # long-poll; returns the feedback the user sent
lavish-axi end artifact.html     # agent-initiated end (reopen still allowed)
lavish-axi stop                  # shut down the background server
```

`lavish-axi design` and `lavish-axi playbook [id]` are the agent-facing
authoring guidance; they are the reason the skill stub stays thin upstream.

## Network exposure

With Tailscale running, the review server **automatically** listens on loopback
*and* this machine's Tailscale IPv4, and prints a MagicDNS URL so the artifact
can be reviewed from a phone on the tailnet. That listener is unauthenticated
and can serve local files to anything that can reach it. Verified on this
machine: the session URL came back as `…ts.vpn.iot.toolsense.io:4387`, i.e. the
work tailnet.

`.config/environment.d/lavish-axi.conf` therefore sets
`LAVISH_AXI_HOST=127.0.0.1`, which overrides the Tailscale binding and keeps the
server loopback-only. Phone review over the tailnet is given up deliberately:
the listener has no authentication and the tailnet is a work network. Drop that
setting (per machine, in the moment) if you ever actually want to review an
artifact from a phone.

Measured on 2026-09-21: with the variable set, `ss -ltn` shows `127.0.0.1:4387`
alone and the session URL is `http://127.0.0.1:4387/...`. Without it, the same
command returns a MagicDNS URL on the work tailnet.

`environment.d` reaches a process through the systemd user manager, so a login
session that started before the file existed keeps the old environment, and so
does every terminal and daemon under it. A first sync of this file takes effect
at the next login. To check the live state rather than the file:

```sh
systemd-run --user --wait --pipe /usr/bin/env | grep LAVISH   # what new processes get
grep -z LAVISH_AXI_HOST /proc/self/environ                    # what this shell has
```

## State and secrets

- Session state, attachments, and `server.log` live under `~/.lavish-axi/`
  (`LAVISH_AXI_STATE_DIR` to move it). Machine-local; never tracked here.
- The background server self-stops 30 minutes idle
  (`LAVISH_AXI_IDLE_TIMEOUT_MS`).
- Every run posts a pageview to an Umami endpoint, `a.kunchenguid.com` unless
  `LAVISH_AXI_UMAMI_HOST` overrides it. The behavior lives in `src/telemetry.js`
  and appears in neither the README nor the CLI help; failures are swallowed, so
  nothing surfaces it. `LAVISH_AXI_TELEMETRY=0` opts out and is set in the same
  `environment.d` file.
- `lavish-axi share` publishes to **ht-ml.app**, a third-party host not part of
  Lavish, public by default. `--private` returns a generated password once, and
  the agent has to relay it, so it lands in the transcript. Pages cannot be made
  public again and cannot be deleted — `--unpublish` only replaces the content
  with a locked placeholder. Treat any share as permanent and public-ish; don't
  share work artifacts casually.

## Skill, hooks, and plugin: none of them used here

Upstream ships three discovery mechanisms. None add capability — the CLI works
with zero setup — and all three were evaluated and rejected:

- **Skill** (`npx skills add kunchenguid/lavish-axi --skill lavish -g`, or
  vendoring `skills/lavish` from the repo). It is a 33-line stub carrying no
  workflow instructions by design, and it tells the agent to invoke
  `npx -y lavish-axi` and to rewrite the CLI's own follow-up commands into npx
  form. That bypasses the mise-tracked install: measured 0.1.74 via npx and a
  2.7 s resolve against 0.1.73 on PATH, instantly. Tracking the version and then
  not using it is worse than not tracking it.
- **Hooks** (`lavish-axi setup hooks`). SessionStart hook for Claude Code,
  Codex, OpenCode, GitHub Copilot CLI. The only thing it adds over a skill is
  live open-session state in a fresh session, paid for with tokens in every
  session, including the ones that never touch HTML. Shared hook caveats: the
  hooks notes in this folder's `README.md`.
- **Plugin** (`lavish-axi setup plugin`). Registers the package directory with
  VS Code, Cursor, and Copilot CLI. Declares no MCP server, so its entire
  payload is the same skill.

Routing instead comes from the one-line entry in the tracked
[`.pi/agent/APPEND_SYSTEM.md`](../../.pi/agent/APPEND_SYSTEM.md), which reaches
Pi and OMP — the harnesses actually in use, and the ones no upstream installer
writes to. Combined with the AXI contract already stated there (bare `<tool>`
prints live state plus next-step commands), an agent that knows the name
self-serves most of the rest from `lavish-axi --help`.

Self-serve has one measured gap, so `APPEND_SYSTEM.md` carries three extra
sentences for this tool. `lavish-axi design` states that the agent must open
every matching playbook before writing HTML; an agent that read `design` still
opened one playbook out of four (2026-09-21). `lavish-axi playbook` takes a
single id and ignores extra ones with exit 0, which makes the loop worth
spelling out. The volatile material — themes, CDN versions, playbook bodies —
stays behind the lookup, where it cannot go stale.
