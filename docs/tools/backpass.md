# backpass

[backpass](https://github.com/kunchenguid/backpass) reads past agent session transcripts (Claude Code, Codex, Pi, and others) and proposes small, evidence-backed edits to `AGENTS.md` / `CLAUDE.md` and skills. Analysis never writes; `backpass apply` is the only writing command, and it asks before each edit.

## Installation & Updates

Tracked globally in `.config/mise/config.toml`, next to its runtime dependency:

```toml
[tools]
"npm:acpx" = "latest"      # ACP client; every backpass model call goes through it
"npm:backpass" = "latest"
```

backpass has no API keys of its own. It drives a harness you are already logged in to (for example `claude` or `codex`) through `acpx`. It needs Node >= 22.5, which the global `node = "latest"` covers.

```sh
mise install        # or: mup
backpass --version
```

## Project scope (default)

Run inside a repo to tune that repo's `AGENTS.md` and skills:

```sh
cd your-repo
backpass init       # writes .backpassrc.json, excludes .backpass/ via .git/info/exclude
backpass            # analyse sessions and propose edits (never writes)
backpass apply      # review each edit, accept or reject, then write
```

Run state lives in `.backpass/` in the repo. `init` keeps that directory out of git, so it never reaches this public repo.

## User scope

`--scope user` tunes the always-loaded user file and user-level skills, using sessions from all projects:

```sh
backpass init --scope user
backpass --scope user
backpass apply --scope user
```

State lives in `~/.config/backpass/user/`, which this repo does not track. Two things to know on this setup:

- backpass writes to the first of these files that exists: `~/.agents/AGENTS.md`, `~/.claude/CLAUDE.md`, `~/.codex/AGENTS.md`. Neither agent file exists here, but `~/.claude/CLAUDE.md` does (it is empty), so user-scope edits go there.
- New skills go to `~/.agents/skills`, next to the symlinks that `mise run deploy-skills` manages. A skill that backpass creates there is a real directory outside the repo. Move it into `skills/common/`, then run `mise run deploy-skills` so both machines get it. See `skills/AGENTS.md`. backpass may also warn that `~/.claude/skills` is a real directory. That is expected: the deployer puts one symlink per skill inside it.

## Sessions from the other machine

backpass can also fetch sessions from other machines over SSH. List the hosts in `~/.config/backpass/config.json` (personal config, not tracked), or pass `--host <dest>` for a single run. See the upstream README for the format.
