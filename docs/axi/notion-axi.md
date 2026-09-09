# notion-axi

Notion CLI for agents. Wraps the official Notion CLI (`ntn`) with TOON output,
next-step hints, and structured errors.

- Source: <https://github.com/maximebrmd/notion-axi>
- npm: [`notion-axi`](https://www.npmjs.com/package/notion-axi)
- Command: `notion-axi`

## Requirements

- Node 20+.
- The official Notion CLI **`ntn`** — notion-axi shells out to it and delegates
  all auth. It is published to npm (maintainer `jclem-ntn`, a Notion engineer), so
  it is tracked here via the mise npm backend alongside notion-axi:

  ```toml
  # .config/mise/config.toml
  "npm:ntn" = "latest"
  ```

  This is preferred over the upstream `curl -fsSL https://ntn.dev | bash`
  installer, which appends to the symlinked `~/.bashrc` and drops an untracked
  binary. After `mise install`, log in once per machine:

  ```sh
  ntn login        # opens a browser; token stored in the OS keychain
  ```

  `ntn login` acts as you and can already see everything you can — no
  page-sharing step.

## Install

Tracked via the mise npm backend:

```toml
# .config/mise/config.toml
"npm:notion-axi" = "latest"
```

```sh
mise install
notion-axi          # recently edited pages & databases
```

## Auth

- Interactive: `ntn login` (keychain). Recommended.
- Headless/CI: `export NOTION_API_TOKEN=ntn_…` (takes precedence over the keychain).
  Never commit this token to the repo.

## Notes

- Listing workspace users needs elevated permissions; `notion-axi users` is often `RESTRICTED_RESOURCE`.

## Hooks

`notion-axi setup hooks` loads a compact Notion workspace view (recently edited pages and databases) at the start of each agent session. Opt-in, idempotent, machine-local (Claude Code / Codex / OpenCode); restart the agent after. Shared hook caveats: the hooks notes in this folder's `README.md`.
</content>
