---
name: querying-databases
description: >-
  Read-only inspection and querying of ToolSense production databases:
  Frontend (MySQL api/telemetry), Backend (PostgreSQL backend), and IoT (PostgreSQL per-service).
  Use when looking up customer assets, IMEIs, telemetry history, dynamic configuration, SIM cards, or firmware status.
user-invocable: true
---

# Querying ToolSense Databases

Read-only guide for querying ToolSense's three production database instances via DBX MCP tools.

## Domain Routing

Before querying, match the entity or question to its database connection and open the matching reference:

| Topic / Entity | Connection | Database / Schema | Reference |
|---|---|---|---|
| Customer groups, hierarchy, tree roots | `Frontend Production` | `api` (quote `` `Group` ``) | [references/frontend-mysql.md](references/frontend-mysql.md) |
| Assets, machine models, digital twins | `Frontend Production` | `api` | [references/frontend-mysql.md](references/frontend-mysql.md) |
| Hardware modules, active asset mappings, IMEIs | `Frontend Production` | `api` | [references/frontend-mysql.md](references/frontend-mysql.md) |
| Latest asset telemetry state (single row) | `Frontend Production` | `api` (`LatestAssetData`) | [references/frontend-mysql.md](references/frontend-mysql.md) |
| Raw sensor messages & telemetry history | `Frontend Production` | `telemetry` (`mqtt`) | [references/frontend-mysql.md](references/frontend-mysql.md) |
| Phoenix dynamic config, parameters, overrides | `Backend Production` | `backend.public` | [references/backend-postgres.md](references/backend-postgres.md) |
| Phoenix OTA published firmware catalog | `Backend Production` | `backend.public` (`ota_publishedversion`) | [references/backend-postgres.md](references/backend-postgres.md) |
| SIM cards, ICCID-to-IMEI mapping, carrier state | `IoT Production` | `iot_sim_governance` | [references/iot-postgres.md](references/iot-postgres.md) |
| Firmware releases, tenant eligibility, FOTA | `IoT Production` | `iot_fota` | [references/iot-postgres.md](references/iot-postgres.md) |
| Non-Phoenix device configurations & sync tasks | `IoT Production` | `iot_configurations` | [references/iot-postgres.md](references/iot-postgres.md) |

## Standard Query Lifecycle

Execute queries in five strict stages:

```text
1. Route Target ──► 2. Consult Reference ──► 3. Inspect Plan (EXPLAIN) ──► 4. Bounded Execute ──► 5. Format Output
```

### 1. Route Target
Identify the connection and exact database/schema using the routing table above.

### 2. Consult Reference
Read the specific reference file in `references/` for verified indexes, table sizes, resolution logic, and golden queries before touching DBX.

### 3. Inspect Plan (`EXPLAIN`)
On non-catalog tables, run `EXPLAIN` on the proposed query.
- Verify the query hits the intended index (check `key` in MySQL or `Index Scan` in Postgres).
- **Abort immediately** if the plan executes a sequential scan on a large table (`telemetry.mqtt`, `AssetData`, `Translation`).
- **Never run `EXPLAIN ANALYZE`** on large tables (it executes the query).

### 4. Bounded Execution
- Always include an explicit indexed filter (`WHERE ...`).
- Always specify an explicit `LIMIT` (default 50, maximum 100).
- If filtering by time on telemetry, bound both lower and upper bounds (`datetime >= NOW() - INTERVAL 7 DAY`).
- **DBX Tool `max_rows`:** DBX defaults to returning at most 100 rows. Always pass `max_rows` matching the query `LIMIT`, and report if the output reached the row limit.

### 5. Format Output
Report findings to the supervisor/caller:
- The SQL query executed.
- The raw data or counts returned.
- Label observed facts versus logical inferences explicitly.
- Never output raw passwords, tokens, or encryption keys.

---

## Staged Cross-Database Lookups

When a question spans multiple databases (e.g. *"Find firmware status for Numatic devices"*):
1. **Never perform cross-database Cartesian joins.**
2. **Stage 1 (Extract keys):** Query the primary database (e.g. Frontend MySQL) to retrieve a bounded list of target IDs or IMEIs (maximum 50 items).
3. **Key Validation:** Validate extracted keys against strict formats before interpolation:
   - IMEIs: validate regex `^[0-9]{15}$`.
   - IDs / Root Group IDs: validate positive integers.
   - Abort if any key contains unexpected non-numeric characters or quotes.
4. **Stage 2 (Filter target):** Switch to the secondary database (e.g. IoT Postgres) and pass the validated keys in an indexed `IN ('<key1>', '<key2>', ...)` clause with an explicit `LIMIT`.
5. **Attribution:** Clearly document which database provided which part of the response.

---

## Self-Improvement & Learning Loop

`db-scout` should actively contribute to maintaining its instructions:
- When a query errors due to a schema change, missing column, or stale table: do not hide the error.
- When a new high-value query pattern ("recipe") is discovered or an undocumented quirk is encountered:
  Include a dedicated section at the end of the report:
  ```markdown
  ## Discoveries & Instruction Updates
  - Table / Database: <name>
  - Issue / Discovery: <what was observed vs documented>
  - Proposed Update: <suggested exact change for references/*.md>
  ```
The main agent or captain can then review and apply the improvement to the capsule.

---

## Safety Invariants

- **Strict Read-Only:** Execute only `SELECT`, `EXPLAIN`, and catalog queries. Never run `INSERT`, `UPDATE`, `DELETE`, `ALTER`, `DROP`, or transaction commands.
- **MySQL Unkillable Queries:** DBX read-only credentials lack `KILL QUERY` privileges. Runaway queries cannot be stopped without external intervention.
- **Progressive Loading:** Read only the reference file needed for the immediate query task.
