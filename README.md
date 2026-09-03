# dotfiles

Personal dotfiles managed with [mise](https://mise.jdx.dev/dotfiles.html) using plain symlinks. Migrated off chezmoi — no templating, no secret manager wiring, no source/target split.

## What's here

| Path | Deploys to | Mode |
| --- | --- | --- |
| `.config/git/config` | `~/.config/git/config` | symlink |
| `.config/atuin/config.toml` | `~/.config/atuin/config.toml` | symlink |
| `.config/herdr/config.toml` | `~/.config/herdr/config.toml` | symlink |
| `.bash_completions.d/` | `~/.bash_completions.d/` | symlink-each |
| `.local/bin/*.sh` | `~/.local/bin/` | symlink-each |

`.local/bin` holds the `cloud-sql-proxy` connection scripts and `ocr.sh`. `symlink-each` links only these files and leaves the rest of your busy `~/.local/bin` alone.

## Daily use

```sh
cd ~/.dotfiles
$EDITOR .config/git/config      # edits are live via the symlink
git commit -am "…" && git push
git pull                        # teammate changes go live instantly
```

You only need `mise bootstrap dotfiles apply` after adding or removing an entry.

## New machine

```sh
git clone git@github.com:golgor/dotfiles.git ~/.dotfiles
cd ~/.dotfiles
mise trust
mise bootstrap dotfiles status   # preview
mise bootstrap dotfiles add ~/.config/git/config …   # or: apply --force
```

Use `dotfiles add` to migrate existing real files without losing them; use `apply --force` to replace them outright.

## Notes

- `ocr.sh` depends on `hyprshot` (Hyprland).
- `git/config` contains name/email; the scripts contain GCP project/instance names. No secrets — but this repo is not the place for any.
- Agent working notes: see `AGENTS.md`.
