# dotfiles

Personal dotfiles for my Omarchy/Arch machines, managed with [mise](https://mise.jdx.dev/dotfiles.html) using plain symlinks. The point: my laptop and stationary machine stay in sync with a plain `git pull`, and a fresh machine gets my whole working environment — tools, host packages, config, and secret wiring — from a handful of commands. Config lives here; runtime state and secret values stay out. Migrated off chezmoi.

This repo is tuned to my machines and preferences, not built for reuse — but feel free to borrow ideas. Terminology and design decisions are documented in [CONTEXT.md](CONTEXT.md).

## What's here

### Dotfiles

| Path | Deploys to | Mode |
| --- | --- | --- |
| `.bashrc` | `~/.bashrc` | symlink |
| `.config/git/config` | `~/.config/git/config` | symlink |
| `.config/atuin/config.toml` | `~/.config/atuin/config.toml` | symlink |
| `.config/herdr/config.toml` | `~/.config/herdr/config.toml` | symlink |
| `.config/hypr/` | `~/.config/hypr/` | symlink |
| `.config/mise/conf.d/dotfiles-tools.toml` | `~/.config/mise/conf.d/dotfiles-tools.toml` | symlink |
| `.config/starship.toml` | `~/.config/starship.toml` | symlink |
| `.config/zed/settings.json` | `~/.config/zed/settings.json` | symlink |
| `.config/zed/keymap.json` | `~/.config/zed/keymap.json` | symlink |
| `.config/nvim/` selected files | `~/.config/nvim/` | symlink |
| `fnox.toml` | `~/fnox.toml` | symlink |
| `.bash_completions.d/` | `~/.bash_completions.d/` | symlink-each |
| `skills/common/`, `skills/claude/` | `~/.agents/skills/`, `~/.claude/skills/`, `~/.codex/skills/` | one directory symlink per skill, via `mise run deploy-skills` (not a mise `[dotfiles]` entry) |

### Mise tools

`mise install` installs these versioned tools. They are also declared in `~/.config/mise/conf.d/dotfiles-tools.toml` so mise shims resolve them outside this repo.

- Atuin `18.19.0`
- kubectl `1.36.2`
- kubectx `0.11.0`
- kubens `0.11.0`
- fnox `latest`
- uv `0.11.14`

### Bootstrap packages

`mise bootstrap packages apply` installs these Arch/AUR host packages:

- `google-cloud-cli`
- `google-cloud-cli-component-gke-gcloud-auth-plugin`
- `cloud-sql-proxy-bin`
- `age`
- `rbw`

AUR support requires a mise release that includes [jdx/mise#12718](https://github.com/jdx/mise/pull/12718). AUR packages require `yay` or `paru`; Omarchy includes `yay`.

## Daily use

```sh
cd ~/.dotfiles
$EDITOR .config/git/config      # edits are live via the symlink
git add …
git commit -m "…"
git push
```

You only need `mise bootstrap dotfiles apply` after adding/removing dotfile entries or when applying this repo on a new machine.

## New machine

```sh
git clone git@github.com:golgor/dotfiles.git ~/.dotfiles
cd ~/.dotfiles
mise trust
mise bootstrap --dry-run
mise bootstrap packages status --missing
mise bootstrap packages apply
mise bootstrap
mise bootstrap dotfiles status
```

If real files already exist where symlinks should go, mise refuses to clobber them. Prefer:

```sh
mise bootstrap dotfiles add ~/.config/git/config ~/.config/atuin/config.toml ~/.config/herdr/config.toml
mise bootstrap dotfiles apply
```

Use `mise bootstrap dotfiles apply --force` only when replacing the existing files is intended.

## Secrets / fnox setup

The repo tracks `~/fnox.toml` as a shared fnox manifest. It lists Bitwarden references only; secret values and local encrypted sync cache stay out of git.

First-time setup on a machine:

```sh
mise bootstrap
mise run setup-fnox
```

If `rbw unlock` fails because Bitwarden is not configured yet, run:

```sh
rbw config set email <your-bitwarden-email>
rbw login
mise run setup-fnox
```

The tracked `~/.config/mise/conf.d/dotfiles-tools.toml` fragment makes shims such as `atuin`, `kubectl`, `kubectx`, `kubens`, and `fnox` work from new terminals outside `~/.dotfiles`.

The setup task creates machine-local files:

- `~/.config/fnox/age.txt` — private age key
- `~/.config/fnox/config.toml` — local `sync-age` provider
- `~/fnox.local.toml` — encrypted local sync cache

Normal resync after pulling a changed `fnox.toml`:

```sh
fs
```

`fs` is an alias in the tracked `.bashrc` and runs `cd ~ && rbw unlock && fnox sync --provider sync-age --local-file --force`. The machine-local parts (age key, sync-age provider) are created by `mise run setup-fnox`.

## Agent skills

`skills/common/` holds the skills shared by Pi, Codex, and Claude Code; `skills/claude/` holds Claude-only ones. `mise run deploy-skills` links each skill directory into `~/.agents/skills` (Pi), `~/.codex/skills` (Codex), and `~/.claude/skills` (Claude Code, both `common/` and `claude/`). Neighbours the harnesses or other installers own (`hey`, `omarchy`, `diagnose-crash`, Codex's `.system`) stay untouched.

Vendored skills are listed in manifests under `.mise/skills/*.toml` (such as `mattpocock.toml`). When upstream updates land:

```sh
mise run update-skills        # updates all manifests in .mise/skills/*.toml; never commits
mise run update-matt-skills   # updates only mattpocock.toml
git diff                      # review, then commit on a branch and open a PR
```

Vendored skills are immutable snapshots: the task refuses to overwrite one that has been edited locally. To customise a skill, copy it to a new name outside all manifests and leave the original vendored. To add or drop an upstream skill, edit the manifest's selection lists and rerun the task; dropping one leaves its directory behind for you to delete. To add a new upstream source, create `.mise/skills/<source>.toml` and run `mise run update-skills`.

## Python automation

Tasks with real logic are Python, in the `automation/` [uv](https://docs.astral.sh/uv/) project (one package, one subpackage per automation); bash file tasks under `.mise/tasks/` are kept for plain CLI glue. `update-skills` is the first: `mise.toml` runs `skills update` from that project.

```sh
mise run check                 # ruff, ruff format --check, ty (strict), pytest — all offline
cd automation && uv run pytest # or any tool directly
```

Conventions for adding an automation are in `AGENTS.md`.

## Kubernetes / GKE setup

The repo includes a manual task:

```sh
mise run setup-kube-contexts
```

It is intentionally **not** automatic bootstrap because it requires Google auth/network access and mutates `~/.kube/config`.

Requirements:

1. Bootstrap packages have installed the Google Cloud CLI packages:

   ```sh
   mise bootstrap packages apply
   ```

2. Mise Kubernetes tools are installed:

   ```sh
   mise install kubectl kubectx kubens
   ```

3. You are authenticated with Google Cloud:

   ```sh
   gcloud auth login
   ```

4. These gcloud configurations already exist and have the right `account` and `project` values:

   | Configuration | Project | Default zone | Default region |
   | --- | --- | --- | --- |
   | `toolsense` | `toolsense` | `europe-west1-b` | `europe-west1` |
   | `toolsense-dev` | `toolsense-dev` | `europe-west1-b` | `europe-west1` |
   | `toolsense-iot` | `toolsense-iot` | `europe-west1-b` | `europe-west1` |
   | `toolsense-iot-dev` | `toolsense-iot-dev` | `europe-west1-b` | `europe-west1` |

   For first-time setup, start with:

   ```sh
   gcloud init
   gcloud config configurations rename default --new-name=toolsense
   ```

   Then create the remaining configurations and set each one's project/zone/region. Repeat this with the project name matching each configuration name:

   ```sh
   gcloud config configurations create toolsense-dev
   gcloud config set project toolsense-dev
   gcloud config set compute/zone europe-west1-b
   gcloud config set compute/region europe-west1
   ```

   Check them with:

   ```sh
   gcloud config configurations list
   gcloud config configurations activate toolsense
   gcloud config list
   ```

Process:

```sh
mise run setup-kube-contexts
```

The task runs `gcloud container clusters get-credentials …` once for each configured gcloud configuration, then renames the long GKE context names to short local names such as `toolsense-dev`. Those short names are stored in `~/.kube/config`; kubectx does not maintain a separate alias dotfile.

You can run only part of it:

```sh
mise run setup-kube-contexts -- --credentials-only
mise run setup-kube-contexts -- --aliases-only
```

## Notes

- `git/config` contains name/email. No secrets belong in this repo.
- `~/.local/share/atuin/` contains Atuin key/session/database state and is intentionally not tracked.
- `~/.config/herdr/` contains Herdr runtime state; only `config.toml` is tracked.
- `~/fnox.local.toml`, `~/.config/fnox/age.txt`, and `~/.config/fnox/config.toml` are machine-local fnox state and are intentionally not tracked.
- `~/.config/hypr/` is tracked as a whole directory; validate Hyprland changes with `hyprctl reload` and `hyprctl configerrors`.
- `~/.config/nvim/lua/plugins/theme.lua` is Omarchy-managed current-theme state and is intentionally not tracked.
- Neovim runtime/plugin state lives under `~/.local/share/nvim/`, `~/.local/state/nvim/`, and `~/.cache/nvim/`; do not track it.
- If VS Code or Windsurf fails to save credentials with Gnome Keyring, add `{ "password-store": "gnome-libsecret" }` to `~/.vscode/argv.json` or `~/.windsurf/argv.json`.
- `~/.pi/agent/skills/` is not managed here; it holds Pi-only links to external research folders. Pi finds the shared skills through `~/.agents/skills`.
- Agent working notes: see `AGENTS.md`.
