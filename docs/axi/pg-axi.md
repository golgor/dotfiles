# pg-axi

Agent-facing PostgreSQL operations: discover, create, inspect, query, back up,
restore, and maintain databases. Read-only/dry-run by default; mutations need
`--execute`, destructive ops also need `--confirm <exact-name>`. Redacts
passwords, URLs, tokens, and secret-like columns.

- Source: <https://github.com/thatdudealso/pg-axi>
- npm: [`pg-axi`](https://www.npmjs.com/package/pg-axi)
- Command: `pg-axi`

Unlike its sibling `kubernetes-axi`, pg-axi **is** published to npm, so it uses
the mise npm backend like the rest.

## Requirements

- Node 20+.
- The standard PostgreSQL client tools it shells out to: `psql`, `createdb`,
  `dropdb`, `pg_dump`, `pg_restore`. These are **not** in the mise config; install
  them per machine (Arch: `sudo pacman -S postgresql` for the client binaries).
- A reachable Postgres (connection URL, host/port/user flags, or a service file).

## Install

Tracked via the mise npm backend:

```toml
# .config/mise/config.toml
"npm:pg-axi" = "latest"
```

```sh
mise install
pg-axi doctor       # connection + tool readiness
pg-axi discover     # live Postgres context
```

## Connection

Pass a URL or host/port/user/database flags, or use a Postgres service file.
Managed Postgres (Supabase, Neon, RDS) and local Docker Compose services are
detected. Keep connection secrets out of this repo.

## Notes

- Mutations are dry-run until `--execute`; review the generated SQL first.
  Destructive ops also require `--confirm <exact-name>`.
- Optional ambient context: `pg-axi hooks install --agent all --scope project --execute`
  (machine-local, not tracked here).
</content>
