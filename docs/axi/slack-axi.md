# slack-axi

Slack CLI for agents: read, search, sweep, and safely draft. Long-lived user
token (works headless), human date ranges, inlined threads, citable permalinks.
Drafts never post without an explicit `draft send`.

- Source: <https://github.com/JarvusInnovations/slack-axi>
- npm: [`slack-axi`](https://www.npmjs.com/package/slack-axi)
- Command: `slack-axi`

## Requirements

- Node 20+.
- A Slack app with a user (`xoxp-…`) token. `auth setup` generates the app
  manifest with the required scopes pre-filled.

## Install

Tracked via the mise npm backend:

```toml
# .config/mise/config.toml
"npm:slack-axi" = "latest"
```

```sh
mise install
slack-axi auth setup     # create the app from a manifest, then paste the token
slack-axi doctor         # verify auth + scope coverage
```

## Auth

`auth setup` walks you through creating and installing the Slack app, then stores
the long-lived `xoxp` token (resolvable from env). Keep the token out of this repo.

## Notes

- `slack-axi channels` lists all conversation types you belong to, including
  private channels and group DMs.

## Hooks

`slack-axi setup hooks` opens each agent session with the slack-axi home view (active workspace + channel count) as ambient context. Opt-in, idempotent, machine-local (Claude Code / Codex / OpenCode); restart the agent after. Shared hook caveats: the hooks notes in this folder's `README.md`.
</content>
