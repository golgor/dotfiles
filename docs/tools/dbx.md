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

## Machine-local state

Connections, credentials, and the policy live in `~/.local/share/com.dbx.app/dbx.db`; secrets are encrypted with a key from the Secret Service keyring.
None of it is tracked here. Each machine is set up in the DBX desktop; copying `dbx.db` between machines is unsupported — use DBX's encrypted export/import.

## Setup per machine

1. `mise bootstrap packages apply` (installs `dbx-bin`) and `mise install` (installs the MCP server).
2. Start the cloud-sql-proxy tunnels for the replicas.
3. In DBX, add one connection per replica (`127.0.0.1:<proxy port>`, read-only DB user) and flag it read-only.
4. Settings → MCP: mode *Read only*, allowlist those connections, save.
5. Restart the agent session; ask it to list DBX connections.
