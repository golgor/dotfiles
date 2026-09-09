# AXI tools

[AXI](https://axi.md) (Agent eXperience Interface) tools are agent-ergonomic CLIs:
token-efficient [TOON](https://toonformat.dev/) output, structured errors, and
next-step hints. They are plain global npm CLIs, so most of them install through
mise's npm backend and stay tracked in this repo.

Catalog: <https://github.com/kunchenguid/axi>

## How they are installed here

Each npm-published tool is declared in `../../.config/mise/config.toml` under
`[tools]` as `"npm:<package>" = "latest"`. mise installs the global npm package
itself, keyed to `latest`, tracked in this repo, and synced to both machines by
`git pull` — same pattern as `npm:@earendil-works/pi-coding-agent`.

Deploy after editing the config:

```sh
mise install        # or: mup
```

Prefer this over `npm install -g`: the mise entry is tracked, reproducible on a
fresh bootstrap, and survives a node version change (mise reinstalls).

## aube backend and the low-download gate

mise's `npm` backend is not npm — it embeds **[aube](https://aube.sh)** (same
author, jdx) as the install engine (`npm.package_manager = "auto"`). Every
`npm:` tool gets an `aube-lock.yaml` under its install dir.

aube runs supply-chain checks during resolution. One is a **low-download gate**:
any package under **1000 downloads/week** is challenged as possible
typosquatting, and in a non-interactive shell (bootstrap, CI, an agent) aube
**fails the install** with `ERR_AUBE_LOW_DOWNLOAD_PACKAGE` / `user aborted`
instead of prompting.

Most axi tools are niche and trip this gate (only `gh-axi` and `ntn` clear it).
The fix is aube's own allowlist, tracked at `~/.config/aube/config.toml`
(`../../.config/aube/config.toml`):

```toml
allowedUnpopularPackages = [
  "notion-axi", "pg-axi", "gws-axi", "slack-axi", "superbee",
  "@andershoffmann/obsidian-axi",
]
```

This exempts only the named packages from the reputation gates; aube's OSV
malicious-package check still runs, and the gate stays on for everything else.
When a tool clears 1000/week on its own, drop its entry. Add a new gated tool by
adding both its `npm:` line to the mise config and its name here.

We keep aube as the backend rather than switching to plain npm
(`npm.package_manager = "npm"`) so the OSV check and speed still apply to every
other tool.

## The tools

| Tool | Package | mise-tracked | External setup | Doc |
| --- | --- | --- | --- | --- |
| gh-axi | `gh-axi` | yes | `gh` (already in mise), `gh auth login` | [gh-axi.md](gh-axi.md) |
| obsidian-axi | `@andershoffmann/obsidian-axi` | yes | none (reads vault folder) | [obsidian-axi.md](obsidian-axi.md) |
| notion-axi | `notion-axi` | yes | `ntn` CLI + `ntn login` | [notion-axi.md](notion-axi.md) |
| gws-axi | `gws-axi` | yes | Google Cloud OAuth (BYO client) | [gws-axi.md](gws-axi.md) |
| pg-axi | `pg-axi` | yes | reachable Postgres (connection string) | [pg-axi.md](pg-axi.md) |
| slack-axi | `slack-axi` | yes | Slack app + `xoxp` token | [slack-axi.md](slack-axi.md) |
| superbee | `superbee` | yes | `superbee setup` (early/experimental) | [superbee.md](superbee.md) |
| kubernetes-axi | — (not on npm) | **no** | git clone; `kubectl` (in mise) | [kubernetes-axi.md](kubernetes-axi.md) |

All tools need **Node 20+** (the global `node` is already `latest`).

## Skills and session hooks

Each tool ships an optional Agent Skill (command surface on demand) and a hook
command that injects live tool state at the start of every agent session. Shared
facts for every hook below: **opt-in** (never auto-installed), idempotent (safe to
re-run; repairs a stale executable path), written into **Claude Code / Codex /
OpenCode** config — not Pi, and **not tracked** in this repo (machine-local, run
per machine). Restart the agent session after installing.

| Tool | Hook command | Injects at session start |
| --- | --- | --- |
| gh-axi | `gh-axi setup hooks` | current repo's open issues + PRs |
| notion-axi | `notion-axi setup hooks` | compact Notion workspace view (recent pages/dbs) |
| obsidian-axi | `obsidian-axi setup hooks` | vault dashboard (needs a global install) |
| gws-axi | `gws-axi setup hooks` | authed accounts, write-protection, setup/health |
| slack-axi | `slack-axi setup hooks` | active workspace + channel count |
| superbee | `superbee hook install [--scope project\|user]` | bundle orientation (pulls board, renders) |
| pg-axi | — none — | inspection tool, no hook command |
| kubernetes-axi | `kubernetes-axi hooks install --agent all --scope project --execute` | ambient k8s context (per upstream README; clone-only, unverified) |

The axi tools' own Agent Skills are separate from this repo's skills
(`skills/common/` + `mise run deploy-skills`) and are not deployed here.

## Guiding agents to use them

Installing a tool does not make an agent reach for it. Two routing paths are
available:

1. **Skill + SessionStart hook** (upstream-recommended, per AXI principle 7). Each
   tool ships an Agent Skill and a hook installer, e.g. `gh-axi setup hooks` or
   `npx skills add maximebrmd/notion-axi --skill notion-axi -g`. The hook feeds
   ambient context at session start; the skill teaches the command surface on
   demand. Run per machine; treat this as machine-local state.

2. **The tracked Pi/OMP append prompt**
   ([`.pi/agent/APPEND_SYSTEM.md`](../../.pi/agent/APPEND_SYSTEM.md)). It contains
   the global AXI routing directive and is symlinked to both harnesses by mise;
   see [OMP configuration](../tools/omp.md). Edit that source when the routing
   changes rather than copying its instructions elsewhere.

   `kubernetes-axi` is omitted because it is not installed; see its page.

## Secrets

No axi auth token belongs in this repo (see the root `AGENTS.md`). Tokens live in
OS keychains or under `~/.config/<tool>/` per machine. Each tool's doc says where.
</content>
</invoke>
