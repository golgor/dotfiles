# IoT Production Database (PostgreSQL)

Connection: **`IoT Production`**  
Engine: PostgreSQL 18.1 (Google Cloud SQL primary, instance `postgres-production`; no read replica). TimeZone = UTC  
Architecture: **One database per service** (always specify `database` parameter in DBX).

## Databases & Service Owners

Sizes are from `pg_database_size`, checked 2026-10.

| Database | Service Owner | What it holds |
|---|---|---|
| **`iot_sim_governance`** (2.8 GB) | SIM Governance | SIM cards, ICCID-to-IMEI mappings, carrier states (Onomondo, Truphone, T-Mobile), consumption records, daily SIM snapshots. **1NCE tables and all `erpnext_*` billing reconciliation tables are empty.** |
| **`iot_fota`** (8 MB) | FOTA Service | Firmware release catalog, product lines, tenant eligibility, per-device desired/actual state (`devices`), groups, configurations. **Currently empty**: 0 product lines, 0 releases, the only tenant is `ToolSense`. |
| **`iot_configurations`** (68 MB) | IoT Configurator | Non-Phoenix device configurations, configuration sets, device sync requests, tasks and attempts, FOTA batch jobs. |
| **`iot_api_test`** | Test API | `devices`, `readings`. |
| `iot_collector` | IoT Collector | Not inspected. |
| `openbao` | OpenBao Vault | Encrypted secrets backend storage. |
| `authentik`, `backstage`, `grafana`, `headscale`, `n8n` | Platform Tools | Internal platform state. |
| `kestrel_fota`, `iot_flespi_edge`, `iot_fleet_health` | Placeholders | Reported to have no tables in `public` (not re-verified). |
| `cloudsqladmin`, `postgres`, `template0`, `template1` | System | Never query. |

## Subsystems & Golden Queries

### 1. SIM Governance (`iot_sim_governance`)
Maps hardware IMEIs to physical SIMs and carriers, and tracks data consumption.

| Table | Est. Rows | Notes |
|---|---|---|
| `snapshots_simsnapshot` | ~3.8 M | Daily snapshot per SIM with consumption, forecast and customer fields. UNIQUE `(iccid, snapshot_date)`. |
| `provider_truphone_simstate` | ~2.0 M | UNIQUE `(iccid, snapshot_date, provider_account)`. |
| `provider_onomondo_simstate` | ~1.5 M | Only `sim_status`; use `snapshots_simsnapshot` for contract/consumption. |
| `provider_truphone_consumptiondailyrecord` | ~1.3 M | UNIQUE `(iccid, date)`. |
| `provider_tmobile_simstate` | ~189 k | Cost, binding period, `contract_active`. |
| `sim_fleet_iccidimeimapping` | ~30 k | Indexed on `iccid` and `imei`. Active mapping: `valid_to IS NULL` (partial UNIQUE on `iccid`). |

- `sim_fleet_iccidimeimapping.provider` ∈ `onomondo`, `truphone_direct`, `truphone_teltonika`, `tmobile` (no `1nce`). `source` is always `provider_api`.
- `sim_status` values: Onomondo and Truphone use `active`/`suspended`; T-Mobile uses `active`/`retired`.

#### Find SIM & Carrier Details by IMEI [Production Pattern]
```sql
-- database: iot_sim_governance
SELECT
  m.imei,
  m.iccid,
  m.provider,
  m.valid_from,
  m.valid_to
FROM sim_fleet_iccidimeimapping m
WHERE m.imei IN ('123456789012345', '123456789012346')
  AND m.valid_to IS NULL
ORDER BY m.discovered_at DESC
LIMIT 50;
```
Drop `AND m.valid_to IS NULL` to see the SIM history of a device.

#### Check Carrier State for an Onomondo SIM [Production Pattern]
```sql
-- database: iot_sim_governance
SELECT
  iccid,
  imei,
  sim_status,
  snapshot_date
FROM provider_onomondo_simstate
WHERE iccid = '89457300000010841545'
ORDER BY snapshot_date DESC
LIMIT 1;
```

#### Check Carrier State for a T-Mobile SIM [Production Pattern]
```sql
-- database: iot_sim_governance
SELECT iccid, imei, sim_status, contract_active, binding_period_end,
       recurring_monthly_cost_eur, snapshot_date
FROM provider_tmobile_simstate
WHERE iccid = '<iccid>'
ORDER BY snapshot_date DESC
LIMIT 1;
```

#### Check Carrier State for a Truphone SIM [Production Pattern]
```sql
-- database: iot_sim_governance
SELECT iccid, imei, sim_status, provider_account, renewal_intent,
       contract_end, data_allowance_kb, snapshot_date
FROM provider_truphone_simstate
WHERE iccid = '<iccid>'
ORDER BY snapshot_date DESC
LIMIT 1;
```

#### Check Carrier State for a 1NCE SIM [Production Pattern, table currently empty]
```sql
-- database: iot_sim_governance
SELECT
  iccid,
  imei,
  sim_status,
  renewal_intent,
  data_allowance_kb,
  remaining_data_kb,
  contract_end
FROM provider_1nce_simstate
WHERE iccid = '8988303000000000000'
ORDER BY snapshot_date DESC
LIMIT 1;
```

### 2. Firmware Updates (`iot_fota`)
Manages firmware releases, target device compatibility, and tenant rollout rules. **The catalog is empty today**; the queries below are schema-correct but return 0 rows.

- `firmware_releases.status` is enum `firmwarelifecyclestatus` = `DRAFT | RELEASED | DEPRECATED` (upper case).
- `product_lines.name` and `tenants.name` are UNIQUE: an exact-name filter uses the index, `ILIKE` scans (fine at this size).
- `devices` (imei UNIQUE) holds per-device desired vs actual firmware and config. *Inference:* the intended per-device FOTA state table.

#### Product Line Discovery [Discovery Pattern]
Find the product line UUID:
```sql
-- database: iot_fota
SELECT id, name
FROM product_lines
WHERE name ILIKE 'phoenix%'
LIMIT 5;
```

#### Check Firmware Releases for a Product Line [Production Pattern]
Use the discovered product line ID or exact name:
```sql
-- database: iot_fota
SELECT
  pl.name AS product_line,
  fr.version AS firmware_version,
  fr.status AS release_status,
  fr.is_globally_eligible,
  fr.created_at
FROM firmware_releases fr
JOIN product_lines pl
  ON pl.id = fr.product_line_id
WHERE pl.name = 'phoenix'
ORDER BY fr.created_at DESC
LIMIT 50;
```

#### Tenant Discovery [Discovery Pattern]
Find the tenant UUID by name:
```sql
-- database: iot_fota
SELECT id, name
FROM tenants
WHERE name ILIKE '%Numatic%'
LIMIT 5;
```

#### Check Firmware Eligibility for a Tenant [Production Pattern]
Use the discovered tenant UUID. `firmware_eligible_tenants` has no index that starts with `tenant_id` (only UNIQUE `(firmware_release_id, tenant_id)`); fine today, will not scale:
```sql
-- database: iot_fota
SELECT
  t.name AS tenant_name,
  fr.version AS firmware_version,
  fr.status AS release_status,
  fr.is_globally_eligible
FROM firmware_eligible_tenants fet
JOIN tenants t
  ON t.id = fet.tenant_id
JOIN firmware_releases fr
  ON fr.id = fet.firmware_release_id
WHERE fet.tenant_id = '00000000-0000-0000-0000-000000000000'
ORDER BY fr.created_at DESC
LIMIT 50;
```

### 3. IoT Configurator (`iot_configurations`)
Manages configuration sets and delivery sync tasks for non-Phoenix IoT devices.

- `device_configurations`: PK `imei`, `item_code` (→ `configuration_set.item_code`), `config` jsonb (GIN index), `device_type` (e.g. `FMC130`, `ROCBIRD2`, `TTFT100`, `FMB003`), `created_at`, `updated_at`. There are **no** `device_id`, `configuration_version` or `status` columns.
- Sync status lives in `device_sync_requests` → `device_sync_tasks` → `device_sync_task_attempts`, all indexed on `imei` (attempts on `sync_task_id`).
- `device_sync_tasks.platform` ∈ `digital_matter`, `fota`, `flespi`.
- Enums: `sync_request_status` = pending, running, succeeded, partially_succeeded, failed, cancelled; `sync_task_status` = pending, in_progress, succeeded, retryable_failed, permanent_failed, cancelled, awaiting_verification; `change_source_type` = erpnext, api, import, config_set.

#### Check Device Configuration [Production Pattern]
```sql
-- database: iot_configurations
SELECT dc.imei, dc.item_code, dc.device_type, dc.config, dc.created_at, dc.updated_at
FROM device_configurations dc
WHERE dc.imei = '355977253234975'
LIMIT 1;
```

#### Check Latest Sync Request and Task for a Device [Production Pattern]
```sql
-- database: iot_configurations
SELECT id, imei, request_type, status, change_source, task_count,
       succeeded_task_count, failed_task_count, created_at, completed_at
FROM device_sync_requests
WHERE imei = '355977253234975'
ORDER BY created_at DESC
LIMIT 1;

SELECT id, sync_request_id, platform, action, status, attempt_count,
       max_attempts, last_error_code, run_after, finished_at, created_at
FROM device_sync_tasks
WHERE imei = '355977253234975'
ORDER BY created_at DESC
LIMIT 5;
```

## Invariants & Gotchas

1. **Always name the target database:** There is no default database. Always pass `database: "iot_sim_governance"`, `"iot_fota"`, or `"iot_configurations"` when calling DBX.
2. **Phoenix configurations are NOT here:** Phoenix dynamic configurations live in `Backend Production` (`backend.dynamicconfig_*`), not in `iot_configurations`.
3. **Missing catalog statistics:** Many tables report `reltuples = -1` in `pg_class`. Here that coincides with never-analyzed tables that are empty or tiny. Check `pg_stat_user_tables.n_live_tup` instead, and still apply explicit filters and `LIMIT`.
4. **Never filter a carrier state table by IMEI:** `provider_*_simstate.imei` is not indexed, and a filter on it nearly scans the 1.5–2 M-row tables. Resolve IMEI → ICCID through `sim_fleet_iccidimeimapping` first, then query the carrier table by `iccid`.
5. **Timestamp types differ:** `iot_configurations` uses `timestamp without time zone`; `iot_sim_governance` and `iot_fota` use `timestamptz`. *Inference:* the naive values are UTC.
6. **Enum-like values without scanning:** read `pg_stats.most_common_vals` for the column. In DBX, `pg_class.relkind` shows as a number (`114` = `r`); cast with `relkind::text`.
