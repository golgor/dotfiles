# Oh My Pi (`omp`)

[Oh My Pi](https://github.com/can1357/oh-my-pi) (`omp`) is an agent coding harness forked from Mario Zechner's upstream [Pi](https://github.com/badlogic/pi-mono), built with a native Rust core and Bun runtime.

## Installation & Updates

`omp` is tracked globally via mise in `.config/mise/config.toml`:

```toml
[tools]
"github:can1357/oh-my-pi" = "latest"
```

Mise downloads the pre-built standalone binary (`omp-linux-x64`) directly from GitHub releases without needing local compilation.

To install or update:
```sh
mise install        # or: mup
```

Verify:
```sh
omp --version
```

## Configuration & Paths

Unlike upstream Pi (`~/.pi`), `omp` uses isolated `.omp` roots by default:

| Level | Path | Notes |
| --- | --- | --- |
| **Global Config** | `~/.omp/agent/config.yml` | Main global settings |
| **Global Profiles**| `~/.omp/profiles/<name>/agent/` | Profile-scoped configurations (`omp --profile <name>`) |
| **Project Config**| `<cwd>/.omp/config.yml` or `settings.json` | Project-local overrides |
| **Session DB / State** | `~/.omp/agent/` | History and SQLite runtime state |

## Global Prompt Policy

The tracked [Pi append prompt](../../.pi/agent/APPEND_SYSTEM.md) is symlinked to
`~/.omp/agent/APPEND_SYSTEM.md` by mise. It is the global default shared with Pi;
edit the tracked source rather than either deployed path.

OMP uses a project `APPEND_SYSTEM.md` or `--append-system-prompt` as a deliberate
override of that default. Do not add `SYSTEM.md`: it replaces OMP's built-in
prompt rather than extending it.

## Skills & Capabilities

`omp` includes an `agents` discovery provider (`discovery/agents.ts`) and natively discovers skills from:
- `~/.agents/skills` (where `mise run deploy-skills` links shared dotfiles skills)
- `<project>/.agents/skills`
- `~/.claude/skills` and `~/.codex/skills`
- `~/.omp/agent/skills` (native OMP user skills)

All shared dotfiles skills deployed by `mise run deploy-skills` work out of the box in `omp`.

## Marketplace plugins

Plugins installed with `omp plugin ...` (e.g. ponytail): setup, gotchas, and why non-native plugins still load — [omp-plugins.md](omp-plugins.md).

## Key Features & Differences from Upstream Pi

- **Integrated LSP**: 14 built-in LSP ops wired into edits and renames (`workspace/willRenameFiles`).
- **Integrated DAP Debugging**: Supports `lldb-dap`, `dlv`, and `debugpy` to attach, inspect stack frames, and diagnose crashes.
- **Persistent Sandbox Execution**: Persistent Python and Bun execution kernels with loopback tool calling.
- **Time-Traveling Stream Rules (TTSR)**: Real-time stream interception that course-corrects model rule violations mid-generation.
- **Agent Hub (`Alt+A`)**: TUI surface to monitor, steer, revive, or kill subagents running in isolated git worktrees.
- **Reviewer / Advisor Model**: Secondary model reading turns in parallel and injecting advisory notes or blockers.
- **Live Collaboration (`/collab`)**: Session sharing over terminal or browser via relay.
