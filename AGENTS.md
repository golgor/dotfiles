# AGENTS.md

Personal dotfiles for golgor's Omarchy/Arch machines (work laptop + stationary), managed by [mise](https://mise.jdx.dev/dotfiles.html). Primary job: keep the two machines in sync day-to-day via `git pull` over live symlinks. Secondary: bootstrap a fresh machine flawlessly, and serve as the authoritative record of how the environment is constructed. Single-user by design — never generalize for other users or other OSes. Work (Toolsense) and personal config deliberately coexist on every machine: one flat repo, no mise `-E` profiles.

Entries live in `mise.toml` under `[dotfiles]`; this file carries the conventions that config cannot show you. `CONTEXT.md` carries the glossary, decision record, and non-goals — read it before questioning terminology or re-litigating a scope decision.

## Workflow: PRs to main

`main` is protected: no direct pushes, no force pushes. Make changes on a branch and open a PR, even for small edits. Remember the symlink model when reviewing: a checked-out branch is already live on this machine.

## Model: symlink

Every entry is `symlink` or `symlink-each`, so each deployed file in `~` points into this checkout. **Editing a file here is live immediately** — no apply step. Run `mise bootstrap dotfiles apply` only when the *set* of entries changes (a new file, a removed file, a mode change). Pulling changes from the other machine is a plain `git pull`; a merge conflict is resolved in git and the live file is fixed in the same move.

## Adding a file

Capture the live file rather than hand-placing it:

```sh
mise bootstrap dotfiles add ~/.config/foo/bar.toml
```

`add` moves the real file into this repo, writes the `[dotfiles]` entry, and symlinks it back. Scripts under `.local/bin/` must stay executable — mise takes permissions from the source file, so `chmod +x` the source.

## Applying onto a machine that has the real files

First apply conflicts because real files sit where symlinks belong. mise **refuses rather than clobbers**. Resolve with `dotfiles add` (non-destructive, preferred) or `mise bootstrap dotfiles apply --force` (replaces them). Check first with `mise bootstrap dotfiles status` / `diff`.

## Public repo: no secrets

Treat every committed file, branch, and PR as public. Before adding config, scan for tokens, credentials, auth sessions, private keys, kubeconfigs, and host-specific runtime state. Do not commit secrets even if the remote is currently private.

Known sharp edges:

- **Zed**: `settings.json` and `keymap.json` are tracked; extension/runtime data under `~/.local/share/zed/` is not. GitHub access for agents goes through the authenticated `gh` CLI—do not add the GitHub MCP server, Copilot CLI agent, or PAT settings without an explicit new need. Zed canonicalizes its settings path before atomic writes, so saving settings preserves the symlink and updates the repo target.
- **Kubernetes/GCP** auth belongs in `~/.kube/config`, `~/.config/gcloud/`, and local credential stores, not in this repo. Tasks may set those up, but dotfiles should not track them.

If a portable config genuinely needs secrets, use the fnox model below rather than plaintext exports or committed credentials.

## fnox secret model

`fnox.toml` is the shared manifest and may be tracked because it contains Bitwarden references, not plaintext values. Treat even manifest metadata as public: secret names and Bitwarden item/field names are visible in git.

Keep machine-local fnox state out of the repo:

- `~/fnox.local.toml` — encrypted local sync cache
- `~/.config/fnox/age.txt` — private age key
- `~/.config/fnox/config.toml` — local `sync-age` provider

Never print secret values in chat or logs. When inspecting shell config or fnox state, report variable names only and redact values. After changing `fnox.toml`, run `fs` or `cd ~ && rbw unlock && fnox sync --provider sync-age --local-file --force` so the local cache matches the manifest.

## Mise tools: local vs global

Tools in this repo's `mise.toml` are active inside `~/.dotfiles`; user-level CLIs that must work from any directory also belong in `.config/mise/conf.d/dotfiles-tools.toml`, deployed to `~/.config/mise/conf.d/`. Keep those tool versions in sync. Do not hide shim-resolution problems with ad-hoc `mise use -g` unless the task is explicitly to mutate this one machine's global mise config.

## Track config, never runtime state

`herdr` and `atuin` write large runtime trees; only their `config.toml` is portable. Keep out of the repo:

- **herdr**: everything except `config.toml`. `plugins.json` hardcodes absolute, content-hashed plugin paths; `.sock` / `.log` / `.lock` / `session.json` / `plugins/` are per-machine state.
- **atuin**: `config.toml` only. The encryption key and session live under `~/.local/share/atuin/`, never here.
- **Neovim**: runtime/plugin state lives under `~/.local/share/nvim/`, `~/.local/state/nvim/`, and `~/.cache/nvim/`. `~/.config/nvim/lua/plugins/theme.lua` is Omarchy-managed current-theme state and is intentionally not tracked.

`~/.config/hypr` is tracked as a whole directory. After Hyprland config changes, validate with `hyprctl reload` and `hyprctl configerrors`.

`~/.bashrc` is tracked and public. Keep its guard convention: every `eval "$(tool ...)"` is wrapped in `command -v tool`, so a fresh machine mid-bootstrap still gets a working shell. Curl-pipe installers that append to `.bashrc` write through the symlink and show up as a repo diff — review and fold or drop the addition. The fnox block is tracked content; `setup-fnox` creates only machine-local files and never edits shell config.

Before adding any new config, confirm the app does not rewrite it via temp-file-rename — that replaces the symlink with a real file and silently breaks the link. For such apps use `mode = "copy"` and re-capture edits with `dotfiles add`.

## Agent skills: one tracked copy, mise projects it

`skills/common/` is the single copy of every shared agent skill; mise `symlink-each` projects it into `~/.agents/skills` (Pi, Codex) and `~/.claude/skills` (Claude Code). Skills listed in `.mise/skills/*.toml` are **immutable vendored snapshots** — editing one in place blocks future `mise run update-skills`. Read `skills/AGENTS.md` before changing anything under `skills/`.

Other owners keep their directories: `hey` (HEY CLI, marked `.managed-by-hey-cli`), `omarchy` and `diagnose-crash` (symlinks into `/usr/share/omarchy`), `~/.codex/skills/.system` (Codex), Claude's `synced/`, and the external research links left in `~/.pi/agent/skills`. Leave them uncaptured; `symlink-each` coexists with them.

## Tasks: bash for glue, Python for logic

A task that mostly chains host CLIs stays a bash file under `.mise/tasks/` (`setup-fnox`, `setup-kube-contexts`). A task with real logic — parsing, comparing trees, validating, anything you would want a test for — lives in the `automation/` uv project and is wired up as a one-line `[tasks]` entry in `mise.toml` calling `uv run --project automation --no-dev <command>`. Do not write a bash file whose only job is to call `uv run`. Read `automation/AGENTS.md` before working in that project; run `mise run check` before opening a PR that touches it.

## Mise docs vs installed mise

Refresh and test local behavior before changing bootstrap/package semantics. Mise docs may track unreleased `main` features; if the desired config depends on an unreleased mise PR, keep the declarative target only when the user explicitly accepts that delay and document the release dependency in the PR/HANDOFF.

## Suggested skills

- `writing-for-agents` — editing this file or `README.md`, never the vendored skills under `skills/common/`.
- `research` — verifying mise behaviour against the docs before changing the model.
- `tdd` — adding or changing anything under `automation/` (see `automation/AGENTS.md`).
