# superbee

Cross-session agent memory as a markdown knowledge bundle in your repo, plus an
agent-first CLI. Typed markdown docs, compare-and-swap writes, conflict-safe
sync on a dedicated `board` branch.

- Source: <https://github.com/Holaxis-ai/superbee>
- npm: [`superbee`](https://www.npmjs.com/package/superbee)
- Command: `superbee`

> **Early and experimental.** Pre-1.0; formats and commands change without
> ceremony. Depend on it accordingly.

## Requirements

- Node 20+. macOS, Linux, or native Windows.

## Install

Tracked via the mise npm backend:

```toml
# .config/mise/config.toml
"npm:superbee" = "latest"
```

```sh
mise install
superbee setup      # read-only; reports health and returns one safe next command
```

### Version note

The upstream README pushes `superbee@next` because the `latest` (stable) package
rejects **Windows**. On Linux/macOS the stable `latest` is the documented install,
so `"npm:superbee" = "latest"` is correct here and keeps the repo's latest-only
policy. Only switch to a dist-tag if you add a native-Windows machine.

## Notes

- A shared bundle lives on an orphan `board` branch (never merges into `main`).
  If you enable sharing, protect `board` with delete/force-push protection like `main`.
- `npx -y superbee` runs read-only/bootstrap commands without installing.

## Hooks

`superbee hook install [--scope project|user]` installs the SessionStart hook — it runs `superbee session-start` (pulls the board, then renders a compact orientation) for Claude Code, Codex, and OpenCode. `superbee hook status` / `uninstall` manage it; `superbee setup` is the agent-driven inspector that recommends it. Opt-in, machine-local; restart the agent after. Shared hook caveats: the hooks notes in this folder's `README.md`.
</content>
