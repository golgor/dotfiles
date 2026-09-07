# .config/hypr/

Per-machine Hyprland config, tracked wholesale as one symlink entry (`~/.config/hypr`). Root `AGENTS.md` has the symlink/PR model; `../../CONTEXT.md` has the wider decision record. This file covers what is specific to Hyprland: the two machines share these exact files, so anything that must differ per machine branches at runtime.

Machines: `golgor-framework` (laptop) and the stationary (`golgor-pc`). `/etc/hostname` is the discriminator.

## Per-machine config: branch on hostname, do not template

The two machines get byte-identical files (symlink, not copy), and mise templating does not reach dotfile *contents* — only its own config/env/tasks. So a value that must differ per machine is chosen at runtime from the hostname, never by templating or by hand-editing the live file.

`host.lua` exports the one shared helper:

```lua
local hostname = require("hypr.host").hostname
```

Consumers so far:

- `input.lua` — keyboard layout order. First entry is the default Hyprland resets to on each unlock (there is no "remember last used"). Laptop defaults to `de`, stationary to `se`.
- `workspaces.lua` — workspace-to-monitor rules (see below).

Add a new per-machine value the same way: `require("hypr.host")`, branch on `hostname()`. Do not duplicate the `hostname()` body — reuse `host.lua`.

## Monitor + workspace layout is owned by hyprmoncfg

[hyprmoncfg](https://github.com/crmne/hyprmoncfg) manages monitor modes, positions, and workspace rules through saved profiles and a daemon. The split between what is tracked and what is not:

| Path | Tracked? | Role |
| --- | --- | --- |
| `../hyprmoncfg/profiles/*.json` | **yes** | Source of truth. One profile per machine, named after its hostname. |
| `../hyprmoncfg/profiles/*.lua` | yes | Human-readable export kept beside the JSON. |
| `../hyprmoncfg/profiles/*.conf` | **no** (gitignored) | Conf-format export hyprmoncfg regenerates on every save. Unused here (Hyprland loads the `.lua` path), so kept out of the repo. |
| `hyprmoncfg-monitors.lua` | **no** (gitignored) | Generated live config, rewritten by the daemon on apply. Per-machine artifact. |
| `hyprland.lua` loader line | yes | Guarded `dofile` of the generated file. Shared; safe when the file is absent. |
| `workspaces.lua` | yes | Bridge for machines not yet on hyprmoncfg (see below). |

Profiles live under `~/.config/hyprmoncfg/profiles`, symlinked from the repo (mise `[dotfiles]` entry). Name each profile after the machine's hostname (`golgor-framework`, `golgor-pc`). The daemon selects a profile by matching connected monitors to each profile's `match_key` — the name is cosmetic for auto-selection but is the id `hyprmoncfg apply <name>` takes. There is no stored "default profile" pointer to track. Untracked hyprmoncfg state is only ephemeral runtime files under `/run/user/<uid>/` (socket, writer lock).

### Load order decides the winner

`hyprland.lua` loads `hyprmoncfg-monitors.lua` **last**, after `workspaces.lua`. When both bind the same workspace, hyprmoncfg wins. On the laptop hyprmoncfg owns layout and `workspaces.lua` does nothing; `workspaces.lua` therefore branches to run only on machines hyprmoncfg does not yet manage. Delete `workspaces.lua` once the stationary also runs hyprmoncfg.

### Adding hyprmoncfg to a new machine

The loader line and the shared profiles arrive via `git pull`. On the machine: install hyprmoncfg, `mise bootstrap dotfiles apply` (links the profiles dir), `hyprmoncfg manage` (starts the daemon and writes the local generated file), arrange monitors, then `hyprmoncfg save` to write a profile into the tracked dir. Commit the new profile.

## Decisions

- **Keyboard layout default is per machine, via `input.lua` hostname branch.** Hyprland resets to the first `kb_layout` entry on each unlock and has no per-session memory, so the fix is to make the *default* correct per machine (laptop `de`, stationary `se`). `Left Alt + Right Alt` still toggles.
- **hyprmoncfg owns monitor + workspace layout; profiles are tracked, the generated file is not.** Profiles are portable plain files and the real config; the generated `hyprmoncfg-monitors.lua` is a machine-specific artifact the daemon rewrites, so it is gitignored. This keeps layout under version control without syncing one machine's monitor descriptions onto the other.
- **Profiles are named after the machine; only `.json`/`.lua` are tracked, `.conf` is gitignored.** hyprmoncfg writes three formats per profile on every save. Hyprland has moved to Lua config, so the `.conf` export is unused here and stays out of the repo. Deleting it does not stick — the next save regenerates it — so it is ignored, not removed.
- **`workspaces.lua` is a bridge, not the owner.** It predates hyprmoncfg and is overridden by it on the laptop. It stays only until the stationary adopts hyprmoncfg, then it goes.
- **`host.lua` holds the one `hostname()` helper.** Two files needed it; a shared module beats a duplicated body. It is the seam for any future per-machine Hyprland value.
