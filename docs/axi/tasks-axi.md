# tasks-axi

Agent-ergonomic markdown-backed task and backlog manager. Edits `backlog.md` in
place with byte-exact round-trips, dependency tracking, dispatch holds, and
TOON output.

- Source: <https://github.com/kunchenguid/tasks-axi>
- npm: [`tasks-axi`](https://www.npmjs.com/package/tasks-axi)
- Command: `tasks-axi`

## Requirements

- Node 20+.
- A markdown backlog (`backlog.md` or `data/backlog.md`). No external services or auth.

## Install

Tracked via the mise npm backend and exempted in `~/.config/aube/config.toml`:

```toml
# .config/mise/config.toml
"npm:tasks-axi" = "latest"
```

```sh
mise install
tasks-axi           # dashboard: live backlog summary, in-flight, queued, and ready tasks
```

(Zero-install alternative: `npx -y tasks-axi <command>`.)

## Role

`tasks-axi` provides agent-ergonomic task and backlog management without
bloating context. It mutates `backlog.md` directly with structured, low-token
commands, keeping markdown as the human-readable source of truth while
truncating long task bodies in list queries.

## Usage

```sh
tasks-axi                            # dashboard: summary, in-flight, queued, ready
tasks-axi ready                      # show dispatchable, unblocked work
tasks-axi add <id> "<title>"         # add task (--kind, --repo, --priority, --start)
tasks-axi start <id>                 # mark task in flight
tasks-axi done <id> --pr <url>       # mark task done with PR link
tasks-axi block <id> --by <id>       # add dependency edge
tasks-axi hold <id> --reason "<txt>" # pause dispatch with structured hold
tasks-axi show <id> --full           # inspect full notes/body on demand
tasks-axi update <id> --body "<txt>" # replace task body
```

Run `tasks-axi --help` or `tasks-axi <command> --help` for the full command list.

## Hooks

`tasks-axi setup hooks` installs the SessionStart hook for Claude Code, Codex, and OpenCode to feed the live backlog as ambient context at session start. Opt-in, machine-local; restart the agent after. Shared hook caveats: the hooks notes in this folder's `README.md`.
