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
| `.config/mise/config.toml` | `~/.config/mise/config.toml` | symlink |
| `.config/starship.toml` | `~/.config/starship.toml` | symlink |
| `.config/zed/settings.json` | `~/.config/zed/settings.json` | symlink |
| `.config/zed/keymap.json` | `~/.config/zed/keymap.json` | symlink |
| `.config/nvim/` selected files | `~/.config/nvim/` | symlink |
| `.config/fnox/config.toml` | `~/.config/fnox/config.toml` | symlink |
| `.config/rbw/config.json` | `~/.config/rbw/config.json` | symlink |
| `.bash_completions.d/` | `~/.bash_completions.d/` | symlink-each |
| `skills/common/`, `skills/claude/` | `~/.agents/skills/`, `~/.claude/skills/`, `~/.codex/skills/` | one directory symlink per skill, via `mise run deploy-skills` (not a mise `[dotfiles]` entry) |

### Mise tools

The global mise config is tracked: `.config/mise/config.toml` is linked to `~/.config/mise/config.toml`, so both machines share one tool list and `mise install` installs it. Every tool is `latest`; a project that needs a specific version pins it in its own `mise.toml`. `mise up` (Omarchy alias `mup`) moves `latest` forward; nothing upgrades on its own.

- atuin, fnox, gh, ruff, uv
- kubectl, kubectx, kubens
- bun, go, node, python
- claude, codex, `npm:@earendil-works/pi-coding-agent`

This repo's own `mise.toml` has no `[tools]` table. Its tasks run after bootstrap has finished, so they use the global `uv`; a project pin inside `~/.dotfiles` would only shadow the global version there.

`mise use -g` writes through the symlink, so an ad-hoc global add shows up as a repo diff to commit or revert.

### Bootstrap packages

`mise bootstrap packages apply` installs these Arch/AUR host packages:

- `google-cloud-cli`
- `google-cloud-cli-component-gke-gcloud-auth-plugin`
- `cloud-sql-proxy-bin`
- `hyprmoncfg-bin`
- `rbw`
- `rbw-pinentry-keyring`
- `libsecret`

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
mise run deploy-skills
```

If real files already exist where symlinks should go, mise refuses to clobber them. Prefer:

```sh
mise bootstrap dotfiles add ~/.config/git/config ~/.config/atuin/config.toml ~/.config/herdr/config.toml
mise bootstrap dotfiles apply
```

Use `mise bootstrap dotfiles apply --force` only when replacing the existing files is intended.

`~/.config/mise/config.toml` always hits this: Omarchy's installer creates it (`mise use -g node`) before this repo is cloned. `dotfiles add` moves that machine's file over the repo copy and links it back, so `git diff` shows exactly what the machine had that the repo did not. Reconcile, commit, then `mise install`:

```sh
mise bootstrap dotfiles add ~/.config/mise/config.toml
git diff .config/mise/config.toml   # usually: drop the machine's node pin, keep "latest"
mise install
```

## Secrets / fnox setup

The repo tracks the fnox manifest at `~/.config/fnox/config.toml` and rbw's
account config at `~/.config/rbw/config.json` (both symlinks). fnox reads its
config from every directory, so the manifest lists Bitwarden references only —
no plaintext values, no age key, no sync cache. Secret values resolve at runtime
through rbw's offline vault, cached in fnox's in-memory `[daemon]`; rbw unlocks
silently via `rbw-pinentry-keyring`, which reads the master password from the
GNOME keyring.

First-time setup on a machine:

```sh
mise bootstrap        # installs rbw, rbw-pinentry-keyring, libsecret; links the configs
rbw login             # one master-password prompt, then silent
```

`rbw login` reads the master password through `rbw-pinentry-keyring`, so it caches
the password in the GNOME keyring on that first unlock and every later resolution
is silent. The keyring is plaintext-on-LUKS — the same at-rest tier as the removed
age key. The account email is already in the tracked `~/.config/rbw/config.json`;
if the account requires API-key device registration, run `rbw register` first.

Changing a secret reference in the manifest needs no resync step; the daemon
picks it up on the next resolution. The only machine-local rbw state is the
device_id and encrypted vault under `~/.local/share/rbw/`.

## Agent skills

`skills/common/` holds the skills shared by Pi, Codex, and Claude Code; `skills/claude/` holds Claude-only ones. `mise run deploy-skills` links each skill directory into `~/.agents/skills` (Pi), `~/.codex/skills` (Codex), and `~/.claude/skills` (Claude Code, both `common/` and `claude/`). Neighbours the harnesses or other installers own (`hey`, `omarchy`, `diagnose-crash`, Codex's `.system`) stay untouched.

**One-time migration on a machine that already ran the old `symlink-each` setup:** `mise bootstrap dotfiles apply` does not prune links for entries removed from `mise.toml`, so the old `symlink-each` directories under `~/.agents/skills` and `~/.claude/skills` are still sitting there as real directories full of file symlinks into `~/.dotfiles`. `mise run deploy-skills` will refuse to touch them, listing one conflict per leftover skill, until you delete those directories by hand. You can tell them apart from the harness-owned neighbours that must be kept (`hey`, `omarchy`, `diagnose-crash`, Codex's `.system/`, Claude's `synced/`): the leftovers are real directories whose contents are all symlinks pointing into `~/.dotfiles/skills`, while the kept ones are either real content owned by another tool or symlinks pointing elsewhere. Delete the leftovers, then rerun `mise run deploy-skills`.

Vendored skills are listed in manifests under `.mise/skills/*.toml` (such as `mattpocock.toml`). When upstream updates land:

```sh
mise run update-skills             # updates all manifests in .mise/skills/*.toml; never commits
mise run update-skills mattpocock  # updates only that manifest
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
- `~/.config/fnox/config.toml` and `~/.config/rbw/config.json` are now tracked; the only machine-local secret state is rbw's device_id and encrypted vault under `~/.local/share/rbw/`.
- `~/.config/hypr/` is tracked as a whole directory; validate Hyprland changes with `hyprctl reload` and `hyprctl configerrors`.
- `~/.config/nvim/lua/plugins/theme.lua` is Omarchy-managed current-theme state and is intentionally not tracked.
- Neovim runtime/plugin state lives under `~/.local/share/nvim/`, `~/.local/state/nvim/`, and `~/.cache/nvim/`; do not track it.
- If VS Code or Windsurf fails to save credentials with Gnome Keyring, add `{ "password-store": "gnome-libsecret" }` to `~/.vscode/argv.json` or `~/.windsurf/argv.json`.
- `~/.pi/agent/skills/` is not managed here; it holds Pi-only links to external research folders. Pi finds the shared skills through `~/.agents/skills`.
- Agent working notes: see `AGENTS.md`.
