# OpenCode (`opencode`)

[OpenCode](https://opencode.ai) (`opencode`) is a terminal coding-agent harness. This machine runs the V2 line
(`2.x`); the V1 config layout is gone.

## Installation & Updates

Tracked globally via mise in `.config/mise/config.toml`:

```toml
[tools]
opencode = { version = "latest", allow_builds = ["@opencode/cli"] }
```

`opencode` ships as a single self-contained binary that bundles the server, so there is no separate server to
install. The CLI does start that server as a long-running background service (`opencode serve --service`), and the
service keeps running the version it was started from. To install or update:

```sh
mise install        # or: mise upgrade opencode
opencode service restart   # after an upgrade, so the background server runs the new version too
```

Skipping the restart leaves a new CLI talking to the old server until the service next restarts.

Verify:

```sh
opencode --version
```

## Configuration & Paths

V2 splits configuration by responsibility. A `tui.json`/`tui.jsonc` file is dead; the terminal client reads
`cli.json` and nothing else.

| Level | Path | Notes |
| --- | --- | --- |
| **Server & project config** | `~/.config/opencode/opencode.json` | Tracked. Models, agents, MCP servers, permissions, references |
| **Terminal client config** | `~/.config/opencode/cli.json` | Tracked. Theme, keybinds, CLI-only plugins |
| **Global agents** | `~/.config/opencode/agents/` | Tracked. Markdown subagents with YAML frontmatter |
| **Global skills** | `~/.config/opencode/skills/` | Not tracked (empty). Skills also load from `~/.claude/skills` |
| **Runtime state** | `~/.local/share/opencode/` | Machine-local. Session DB, logs, auth, MCP OAuth tokens |
| **Service registration** | `~/.local/state/opencode/` | Machine-local. Background-service auth |
| **Project config** | `<project>/opencode.json` or `<project>/.opencode/opencode.json` | Per-repo overrides |

Only the three tracked paths above are symlinked into this repo. `service.json` holds a generated service password,
and `~/.local/share/opencode/auth.json` holds provider credentials — neither is tracked.

## Migrating from V1

V1 config is normalized in memory but not rewritten, so a stale V1 file keeps working. Convert deliberately
instead. The shape changes that matter:

| V1 | V2 |
| --- | --- |
| `tui.json` / `tui.jsonc` | `cli.json` (one global file) |
| `autoupdate: false` | `update: "disable"` |
| `mcp: { server: {...} }` | `mcp: { servers: { server: {...} } }` |
| `enabled: true` | `disabled: false` |
| `clientId` | `client_id` (snake case) |
| `permission: { bash: "ask" }` | `permissions: [{ action: "shell", resource: "*", effect: "ask" }]` |
| agent `temperature` | `request.body.temperature` |
| `skill` / `skillEnabled` | `skills` array |

Permission actions renamed: `bash` → `shell`, `task` → `subagent`, `write`/`patch` → `edit`.

One trap: V1 agent frontmatter used a permission **map** (`permissions: { edit: ask }`). V2 expects an ordered
**list** of `{ action, resource, effect }` rules. A V1 map is silently ignored, so the subagent runs with the
default permissions instead of the intended restrictions. Check with the API:

```sh
opencode api get /api/agent
```

## Plugins

The plugin API broke between V1 and V2. A V1 plugin (a function returning tools and hooks) does not run in V2.

| V1 | V2 |
| --- | --- |
| `export const Plugin = async () => ({ "tool.execute.before": ... })` | `export default Plugin.define({ id, setup(ctx) { ... } })` |
| `client.app.log(...)` | `ctx.location`, `ctx.session`, `ctx.model`, ... domain methods |
| `ctx.event.subscribe()` | `ctx.event.subscribe()` |

Every V2 plugin needs a stable `id`; plugin storage is scoped by it.

## Herdr Integration

The [herdr](https://herdr.dev) terminal workspace manager tracks OpenCode session state for its pane UI. It is
installed separately and owns its own files, which are **not** tracked here:

```sh
herdr integration install opencode
```

It writes `~/.config/opencode/plugins/herdr-agent-state.js`, `herdr-tui-session.js`, `herdr-opencode/`, and
`tui.jsonc`. It also registers itself in the tracked `cli.json` under `plugins`:

```json
"plugins": ["./herdr-opencode"]
```

That entry is the V2 form. Herdr rewrites `cli.json` in place when it reinstalls, which preserves the symlink into
this repo — so the change lands here as a diff, the same way the tracked Pi `settings.json` behaves.

Herdr's files are not tracked because `herdr integration install opencode` regenerates them. The one exception is
the `cli.json` entry above, which herdr needs and which is already tracked.

## References

`references` in `opencode.json` give named access to directories outside the project. This repo's config adds two:

| Alias | Path | Use |
| --- | --- | --- |
| `dotfiles` | `~/.dotfiles` | This repository: machine setup, mise tasks, conventions |
| `config` | `~/.config` | User-level configuration of installed tools |

Attach one by alias, then ask for a path under it. This is the way to reach files outside the project, since the
`@` picker only searches the session directory and skips dotfiles.

## Secrets

Provider credentials live in `~/.local/share/opencode/auth.json` and are not tracked. `opencode auth list` shows what
is connected. Environment variables from [fnox](../../docs/rbw-fnox-research.md) (for example `OPENCODE_API_KEY`)
reach the harness through the shell; an expired one shows up as a `401` in `~/.local/share/opencode/log/opencode.log`
with a message about the key having expired.

## Troubleshooting

```sh
opencode service status              # background service health
opencode service restart             # restart it, e.g. after an upgrade
opencode api get /api/config         # resolved config as the server sees it
opencode api get /api/agent          # agents and their effective permissions
opencode api get /api/mcp            # MCP server connection state
opencode plugin list                 # loaded plugins
opencode --standalone                # private server, to isolate shared-service issues
```

Logs: `~/.local/share/opencode/log/opencode.log`. Filter `role=cli` for the terminal client and `role=server` for
sessions, providers, and plugins.
