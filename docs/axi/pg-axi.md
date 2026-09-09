# pg-axi

A read-only PostgreSQL CLI shaped for agents: token-efficient schema summary,
per-table detail, capped queries, name search, index stats, and query plans in
TOON output. Connects directly and never prompts for credentials.

- Source: <https://github.com/Abdul-Rehman6/pg-axi>
- npm: [`pg-axi`](https://www.npmjs.com/package/pg-axi)
- Command: `pg-axi`

> **Name note:** the npm `pg-axi` is Abdul Rehman's project. It is **not** the
> `pg-axi` in the AXI catalog (thatdudealso) — see "Alternative" below.

## Requirements

- Node 20+.
- A reachable PostgreSQL. Connection resolves from `--url`, then `DATABASE_URL`,
  then `PGHOST`/`PGPORT`/`PGUSER`/`PGPASSWORD`/`PGDATABASE`. No external client
  tools (`psql`, `pg_dump`) needed — it connects directly. Keep connection
  secrets out of this repo.

## Install

Tracked via the mise npm backend:

```toml
# .config/mise/config.toml
"npm:pg-axi" = "latest"
```

```sh
mise install
pg-axi                       # schema summary: every table, row + column counts
```

## Usage

```sh
pg-axi                            # schema summary
pg-axi table users                # one table: columns, keys, FKs both ways, indexes
pg-axi query "select now()"       # run SQL, capped at 20 rows (--full / --limit to widen)
pg-axi search order               # tables/columns whose name matches
pg-axi indexes users              # index sizes + scan counts
pg-axi explain "select ..."       # condensed plan (--analyze to really run, rolled back)
```

Read-oriented: `query` is capped and there are no mutation/backup/restore
commands. `--json` swaps TOON for JSON.

## Hooks

None — pg-axi has no `setup hooks` / agent-hook command.

## Alternative: thatdudealso/pg-axi

The AXI catalog's `pg-axi` is a different, broader project:
<https://github.com/thatdudealso/pg-axi> — discover/plan/apply, backup/restore,
mutation guards (`--execute` / `--confirm`), and its own `hooks install` and
skill. It is **not published to npm** (clone-only, like `kubernetes-axi`), so it
is not mise-tracked here. Consider it if you outgrow read-only inspection.
</content>
