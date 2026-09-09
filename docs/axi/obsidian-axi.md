# obsidian-axi

Read, search, write, and link Obsidian notes from the filesystem. No plugin, no
server, no API key; Obsidian need not be running.

- Source: <https://github.com/AndersHoffmann/obsidian-axi>
- npm: [`@andershoffmann/obsidian-axi`](https://www.npmjs.com/package/@andershoffmann/obsidian-axi)
- Command: `obsidian-axi`

## Requirements

- Node 20+.
- An Obsidian vault folder on disk. No auth of any kind.

## Install

Tracked via the mise npm backend:

```toml
# .config/mise/config.toml
"npm:@andershoffmann/obsidian-axi" = "latest"
```

```sh
mise install
obsidian-axi        # vault summary + recent notes
```

(Zero-install alternative: `npx -y @andershoffmann/obsidian-axi <command>`.)

## Vault selection

First match wins:

1. `--vault <name|path>` (flags go **after** the command)
2. `OBSIDIAN_VAULT=<name|path>`
3. a `.obsidian/` folder in the current directory or above
4. `defaultVault` in `~/.config/obsidian-axi/config.json`
5. the vault Obsidian has open, then the most recently opened

`obsidian-axi vault info` reports which rule applied.

## Notes

- Writes are atomic (temp file + rename); `rm` moves to `.trash` unless `--permanent`.
- With Obsidian Sync, save/close a note with unsaved edits before writing to it.

## Hooks

`obsidian-axi setup hooks` opens each agent session with your vault dashboard as ambient context. Needs a global install (nothing stable for the hook to point at via npx). Opt-in, idempotent, machine-local (Claude Code / Codex / OpenCode); restart the agent after. Shared hook caveats: the hooks notes in this folder's `README.md`.
</content>
