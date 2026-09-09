# gws-axi

Google Workspace CLI for agents: Gmail, Calendar, Docs, Drive, Slides, Sheets
behind one command. TOON output, idempotent mutations, multi-account write
safety. Gmail `send` is intentionally out of scope — it drafts, never sends.

- Source: <https://github.com/JarvusInnovations/gws-axi>
- npm: [`gws-axi`](https://www.npmjs.com/package/gws-axi)
- Command: `gws-axi`

## Requirements

- Node 20+.
- A Google account (personal or Workspace).
- Your own Google Cloud project with an OAuth client — the **bring-your-own OAuth
  client** model. `gcloud` CLI is optional (speeds setup only).

This is the heaviest setup of the batch: ~10 min for a fresh Cloud project, ~3 min
reusing one.

## Install

Tracked via the mise npm backend:

```toml
# .config/mise/config.toml
"npm:gws-axi" = "latest"
```

```sh
mise install
gws-axi doctor      # prerequisites + live API health
```

## Auth (per machine)

`gws-axi` is designed to be driven by an agent through a progressive flow:

```sh
gws-axi auth setup           # emits next-step instructions + a setup.html helper
gws-axi auth login --account you@example.com
gws-axi auth publish         # Testing → Production, retires the 7-day token expiry
```

You create the Cloud project, enable Workspace APIs, configure the consent screen,
and add accounts as test users. Tokens live locally at `~/.config/gws-axi/` — never
in this repo.

## Notes

- Multi-account: with 2+ accounts authenticated, writes require `--account <email>`.
  Pin one with `export GWS_AXI_ACCOUNT=<email>` (accident boundary, not a security one).
- Optional ambient context: `gws-axi setup hooks` (machine-local, not tracked here).
- If you keep other Google MCP servers/skills, disable them to avoid tool ambiguity.
</content>
