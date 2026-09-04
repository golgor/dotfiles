# dotfiles

Personal dotfiles managed with [mise](https://mise.jdx.dev/dotfiles.html) using plain symlinks. Migrated off chezmoi — keep config here, keep runtime state and secrets out.

## What's here

### Dotfiles

| Path | Deploys to | Mode |
| --- | --- | --- |
| `.config/git/config` | `~/.config/git/config` | symlink |
| `.config/atuin/config.toml` | `~/.config/atuin/config.toml` | symlink |
| `.config/herdr/config.toml` | `~/.config/herdr/config.toml` | symlink |
| `.config/starship.toml` | `~/.config/starship.toml` | symlink |
| `.config/nvim/` selected files | `~/.config/nvim/` | symlink |
| `.bash_completions.d/` | `~/.bash_completions.d/` | symlink-each |

### Mise tools

`mise install` installs these versioned tools:

- Atuin `18.19.0`
- kubectl `1.36.2`
- kubectx `0.11.0`
- kubens `0.11.0`

### Bootstrap packages

`mise bootstrap packages apply` installs these Arch/AUR host packages:

- `google-cloud-cli`
- `google-cloud-cli-component-gke-gcloud-auth-plugin`
- `cloud-sql-proxy-bin`

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
- `~/.config/nvim/lua/plugins/theme.lua` is Omarchy-managed current-theme state and is intentionally not tracked.
- Neovim runtime/plugin state lives under `~/.local/share/nvim/`, `~/.local/state/nvim/`, and `~/.cache/nvim/`; do not track it.
- If VS Code or Windsurf fails to save credentials with Gnome Keyring, add `{ "password-store": "gnome-libsecret" }` to `~/.vscode/argv.json` or `~/.windsurf/argv.json`.
- Agent working notes: see `AGENTS.md`.
