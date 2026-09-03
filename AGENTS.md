# AGENTS.md

A [mise](https://mise.jdx.dev/dotfiles.html) dotfiles repo. Entries live in `mise.toml` under `[dotfiles]`; this file carries the conventions that config cannot show you.

## Model: symlink

Every entry is `symlink` or `symlink-each`, so each deployed file in `~` points into this checkout. **Editing a file here is live immediately** — no apply step. Run `mise bootstrap dotfiles apply` only when the *set* of entries changes (a new file, a removed file, a mode change). Pulling teammate changes is a plain `git pull`; a merge conflict is resolved in git and the live file is fixed in the same move.

## Adding a file

Capture the live file rather than hand-placing it:

```sh
mise bootstrap dotfiles add ~/.config/foo/bar.toml
```

`add` moves the real file into this repo, writes the `[dotfiles]` entry, and symlinks it back. Scripts under `.local/bin/` must stay executable — mise takes permissions from the source file, so `chmod +x` the source.

## Applying onto a machine that has the real files

First apply conflicts because real files sit where symlinks belong. mise **refuses rather than clobbers**. Resolve with `dotfiles add` (non-destructive, preferred) or `mise bootstrap dotfiles apply --force` (replaces them). Check first with `mise bootstrap dotfiles status` / `diff`.

## Track config, never runtime state

`herdr` and `atuin` write large runtime trees; only their `config.toml` is portable. Keep out of the repo:

- **herdr**: everything except `config.toml`. `plugins.json` hardcodes absolute, content-hashed plugin paths; `.sock` / `.log` / `.lock` / `session.json` / `plugins/` are per-machine state.
- **atuin**: `config.toml` only. The encryption key and session live under `~/.local/share/atuin/`, never here.

Before adding any new config, confirm the app does not rewrite it via temp-file-rename — that replaces the symlink with a real file and silently breaks the link. For such apps use `mode = "copy"` and re-capture edits with `dotfiles add`.

## Suggested skills

- `writing-for-agents` — editing this file or `README.md`.
- `research` — verifying mise behaviour against the docs before changing the model.
