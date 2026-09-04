# CONTEXT.md

Domain model for this repo: the vocabulary, the durable decisions, and what is
deliberately out of scope. `AGENTS.md` carries the operational conventions;
this file carries the *why* and the *words*.

## Glossary

- **entry** — one line in `mise.toml` under `[dotfiles]`, mapping a path in `~`
  to a file in this repo. The set of entries defines what the repo owns.
- **capture / add** — `mise bootstrap dotfiles add <path>`: moves the live file
  into this repo, writes the entry, and symlinks it back. The opposite of
  hand-placing files; always prefer capturing the real file.
- **apply** — `mise bootstrap dotfiles apply`: converges symlinks to match the
  entry set. Needed only when the *set* changes, never for content edits.
- **symlink model** — every deployed file in `~` points into this checkout, so
  editing a file here is live immediately and syncing machines is a plain
  `git pull`. Contrast: copy-based dotfile managers need an apply step per edit.
- **manifest** — `fnox.toml` (deployed to `~/fnox.toml`): the tracked list of
  secret *references* (env var name → Bitwarden item/field). Contains no
  values, so it is safe to commit; the names themselves are still public.
- **local cache** — `~/fnox.local.toml`: the age-encrypted store of the actual
  secret values, produced by fnox sync. Machine-local, never tracked.
  Contrast with the manifest: manifest says *what*, cache holds *the values*.
- **sync-age provider** — the machine-local fnox provider (in
  `~/.config/fnox/config.toml`) that encrypts the local cache with this
  machine's age key (`~/.config/fnox/age.txt`).
- **machine-local state** — files that must exist on each machine but never in
  this repo: the age key, fnox provider config and cache, kubeconfig, gcloud
  auth, Bitwarden session.
- **config vs runtime state** — config is the portable intent (a
  `config.toml`); runtime state is what the app writes while running (caches,
  sessions, plugin trees, locks). Only config is tracked. herdr, atuin, and
  Neovim are the canonical examples.
- **Omarchy-managed state** — files Omarchy owns and rewrites, such as
  `~/.config/nvim/lua/plugins/theme.lua` (current theme). Intentionally
  untracked even though they sit inside tracked config directories.
- **host package vs mise tool** — host packages (`[bootstrap.packages]`) are
  pacman/AUR system packages like `age` and `rbw`; mise tools (`[tools]`) are
  versioned per-user CLIs like `kubectl`. Rule of thumb: if it needs system
  integration or is a build dependency, it is a host package.
- **local vs global mise config** — this repo's `mise.toml` is active only
  inside `~/.dotfiles`; `.config/mise/conf.d/dotfiles-tools.toml` (deployed to
  `~/.config/mise/conf.d/`) makes the same tools resolve from any directory.
  Both must list the same versions.
- **shim** — mise's PATH stub for a tool. A shim without an active version for
  the current directory fails with "No version is set for shim" — the symptom
  of a tool declared locally but not globally.
- **manual task** — a task under `.mise/tasks/` that is deliberately *not* part
  of `mise bootstrap` because it needs interactive auth or mutates
  machine-local state: `setup-fnox`, `setup-kube-contexts`.
- **`fs`** — an alias provided by the tracked `.bashrc`:
  `cd ~ && rbw unlock && fnox sync --provider sync-age --local-file --force`.
  `setup-fnox` creates the machine-local age key and sync-age provider; it does
  not edit shell config. Run `fs` after any manifest change.

## Decisions

- **mise, not chezmoi.** The old chezmoi repo was mostly legacy/broken and its
  copy-based model needs an apply step per edit. mise symlinks make edits live
  and machine sync a plain `git pull`, and mise already manages tools and
  bootstrap here.
- **One flat repo, no mise `-E` profiles.** The stationary machine needs both
  work and personal config (home office); the laptop is ~99% work but carries
  personal config harmlessly. Work secrets or kube contexts present on the
  personal machine are a feature, not a leak. Do not propose profile splits.
- **`.local/bin` scripts are out.** Pruned deliberately during migration; do
  not re-add them without an explicit request.
- **`~/.config/hypr` is tracked wholesale.** The live config was cleaned up
  first; the whole directory is one symlink entry. Old chezmoi Hypr content
  was not migrated.
- **`theme.lua` is untracked.** Omarchy owns the current-theme state inside the
  otherwise-tracked Neovim config; tracking it would fight Omarchy's theme
  switching.
- **Manual tasks stay out of bootstrap.** `setup-fnox` and
  `setup-kube-contexts` need Bitwarden/gcloud interaction and create
  machine-local secret material, so they must be run knowingly, not as a
  bootstrap side effect.
- **fnox manifest is tracked, everything else fnox is local.** The manifest
  contains only references; the age key, provider config, and encrypted cache
  are per-machine.

If this section outgrows a screenful, move entries to `docs/adr/`.

## Non-goals

- Desktop/theming owned by Omarchy (themes, current-theme state).
- System provisioning beyond the listed host packages — this is not full OS
  config management.
- Auth/credential state: kube tokens, gcloud auth, Bitwarden session, age key.
- Runtime state of any application.
- `.local/bin` scripts.

## Typical sessions

Sessions here are short and explicit. The usual intents, roughly by frequency:
editing tracked config content (Hyprland, Neovim, git), capturing a new config
file, adding or bumping a tool/package, changing a secret in the manifest, and
occasionally machine setup or symlink repair. There is no strong default —
read the request rather than assuming.
