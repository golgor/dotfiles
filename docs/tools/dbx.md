# DBX MCP

Agents reach internal databases (Postgres, MySQL) through the DBX MCP server, read-only.
The DBX CLI and its agent skill are deliberately not used.

- Source: <https://github.com/t8y2/dbx>
- MCP server: `npm:@dbx-app/mcp-server` (global mise config) → `dbx-mcp-server`
- Desktop: `aur:dbx-bin` (bootstrap package) — needed only to manage connections and the MCP policy
- Harness entry: `dbx` in `.pi/agent/mcp.json` (Pi and OMP)

## Why MCP, not the CLI

The MCP server enforces the policy saved in **DBX → Settings → MCP** on every request; the agent cannot widen it.
The CLI's write gate is the agent's own `--allow-writes` flag, so it is not a limit.

## Safety layers

1. **Database role** — the real boundary. Agent connections use a read-only role, routed by cloud-sql-proxy to read replicas.
2. **DBX policy** — mode *Read only*, plus an explicit connection allowlist. Never allowlist a read-write connection.
3. **Connection flags** — mark each agent connection read-only (and production where it applies) in DBX.
4. **`DBX_MCP_ALLOW_WRITES=0`** in `mcp.json` — an unsaved DBX policy defaults to `read_only: false`; this env keeps MCP read-only until the policy is saved, and cannot widen it afterwards.

DBX's SQL risk classifier is defence in depth, not a security boundary.

## Query resource bounds

DBX MCP, not the agent prompt, supplies SQL result and execution controls:

- `dbx_execute_query` defaults to 100 returned rows and clamps `max_rows` to 1–1000. This bounds row count, not payload bytes or scanned rows.
- MCP policy `query_timeout_secs` takes precedence over the connection's effective query timeout. Keep a finite connection timeout (60 seconds for agent connections); zero disables it. Verify this on each machine.
- Agent `LIMIT`, indexed filters, and `EXPLAIN` are query-planning precautions, not enforced resource limits. Aggregation and sorting can still scan large tables with a small result limit.
- A configured execution timeout does not establish database-side cancellation for every driver. For a hard workload boundary, verify cancellation and configure database-side statement limits with the database operator.

Verified implementation reference: [DBX MCP package 0.4.114](https://github.com/t8y2/dbx/tree/packages-v0.4.114), `crates/dbx-mcp/src/server.rs` (`execute_query` row clamp and policy timeout) and `crates/dbx-core/src/ai/agent_tools.rs` (`agent_query_timeout_secs` and execution options).

## Machine-local state

Connections, credentials, and the policy live in `~/.local/share/com.dbx.app/dbx.db`; secrets are encrypted with a key from the Secret Service keyring.
None of it is tracked here. Each machine is set up in the DBX desktop; copying `dbx.db` between machines is unsupported — use DBX's encrypted export/import.

## Setup per machine

1. `mise bootstrap packages apply` (installs `dbx-bin`) and `mise install` (installs the MCP server).
2. Start the cloud-sql-proxy tunnels for the replicas.
3. In DBX, add one connection per replica (`127.0.0.1:<proxy port>`, read-only DB user) and flag it read-only. Set its query timeout to 60 seconds; check that any MCP timeout override is finite too.
4. Settings → MCP: mode *Read only*, allowlist those connections, save.
5. Restart the agent session; ask it to list DBX connections.
