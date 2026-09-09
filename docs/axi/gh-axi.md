# gh-axi

GitHub CLI for agents. Wraps the official `gh` CLI with TOON output, next-step
hints, and structured errors.

- Source: <https://github.com/kunchenguid/gh-axi>
- npm: [`gh-axi`](https://www.npmjs.com/package/gh-axi)
- Command: `gh-axi`

## Requirements

- Node 20+ (global `node` is `latest`).
- [`gh`](https://cli.github.com/) installed and authenticated. `gh` is already in
  `.config/mise/config.toml`; authenticate per machine with `gh auth login`.
- Optional: `gh extension install github/gh-stack` for the `stack` commands.
- Optional: `gh >= 2.99.0` only for `--attach` on issue/PR create/edit/comment.

## Install

Tracked via the mise npm backend:

```toml
# .config/mise/config.toml
"npm:gh-axi" = "latest"
```

```sh
mise install        # deploy the global gh-axi
gh-axi              # dashboard: live repo state, no args
```

## Auth

Uses your existing `gh` auth — no separate token. For GitHub Enterprise or a
custom host, authenticate `gh` for that host and pass `--hostname <host>` or set
`GH_HOST`. Override the wrapped binary with `GH_BIN`. Projects (v2) commands need
the `project` / `read:project` scope: `gh auth refresh -s project`.

## Notes

- Secrets are read from piped stdin only (never argv): `echo -n "sk-..." | gh-axi secret set NAME`.
- Optional ambient context: `gh-axi setup hooks` (machine-local, not tracked here).
</content>
