# Frontend Production Database (MySQL)

Connection: **`Frontend Production`**  
Engine: MySQL 8.0.36 (Google Cloud SQL). The connection is read-only (`@@read_only = 1`), most likely a read replica.  
Schemas: **`api`** (platform data), **`telemetry`** (raw device messages)  
Timezone: UTC (`@@system_time_zone = UTC`, session `SYSTEM`).

## Size & Table Scale

Row counts are `information_schema.TABLES.TABLE_ROWS` estimates from 2026-10.

| Table | Est. Rows | Key Caution |
|---|---|---|
| `telemetry.mqtt` | ~379 M | Indexed **only** on `(data_ep, datetime)`, `ver`, and PK. |
| `telemetry.mqtt-ble` | ~280 M | Raw BLE advertisement logs. Same indexing caveats as `mqtt`. (Not re-verified.) |
| `api.AssetData` | ~252 M | Processed message history. Index on `(assetId, created)`. (Not re-verified.) |
| `api.Translation` | ~122 M | Only secondary index is `updated`. Look up strictly by primary key `id`. |
| `api.Asset` | ~1.38 M | Digital twins. Index on `(groupId, deleted, assetTypeId)` and `(created, deleted, isFake)`. |
| `api.Module` | ~321 k | Hardware modules. `imei` is `char(15)` with a non-unique index. **`created` is not indexed.** |
| `api.AssetModuleMapping` | ~111 k | Active module links. `UNIQUE (assetId, activeFlag)`, plus `idx_moduleId`. Filter `activeFlag = 1 AND deleted IS NULL`. |
| `api.LatestAssetData` | ~74 k | One latest JSON message per asset (`assetId` unique). Indexed on `imei` and `moduleTimestamp`. |
| `api.`Group`` | ~72.5 k | **Reserved keyword in MySQL.** Always quote as `` `Group` ``! Indexed on `treeRootId`, `rootGroupId`, `parentGroupId`. Not on `isRoot` or `name`. |
| `api.ModuleType` | 3 | Legacy: `1 HUMMINGBIRD`, `2 STANDARD`, `3 GOLDFINCH`. |

## Invariants & Circuit Breakers

1. **Quote `Group`:** `GROUP` is a reserved SQL keyword. Writing `FROM api.Group` causes a fatal syntax error. Always write `api.`Group``.
2. **Unkillable queries:** The DBX read-only user cannot execute `KILL QUERY`. Any runaway query must run to completion. Always verify `EXPLAIN` before running on non-catalog tables. `EXPLAIN` alone is zero-risk, and for an all-`const` single-asset lookup its plan already shows the resolved rows.
3. **Never join fleet trees into `telemetry.mqtt`:** A join from `Group` or `Asset` into `telemetry.mqtt` forces a massive dependent scan. Always break into two steps: extract IMEIs first (max 50), then query `telemetry.mqtt` with bounded `data_ep IN ('<imei1>', ...)` and an explicit `datetime` range.
4. **`Asset.moduleId` is mostly empty:** Do not rely on `Asset.moduleId`. Always resolve modules via `AssetModuleMapping` where `activeFlag = 1 AND deleted IS NULL`.
5. **Translation table scanning:** Never filter `api.Translation` on text or language columns. Look up translations strictly by primary key (`id = AssetType.nameId`). `de_de` can be an empty string; fall back to `en_us`.
6. **Soft deletes & active mappings:** Always filter `deleted IS NULL` on `` `Group` ``, `Asset`, and `AssetModuleMapping`. There is only one active module per asset at a given time (`activeFlag = 1 AND deleted IS NULL`).
7. **IMEI De-duplication:** If an IMEI was reassigned between assets, select the asset with the newest `LatestAssetData.moduleTimestamp` using `ROW_NUMBER()`.
8. **Counting modules by date scans the table:** `api.Module.created` has no index, so `WHERE created BETWEEN ...` is a full scan of ~321 k rows (`type=ALL`). `AssetModuleMapping.created` has no index either. It is bounded and acceptable on this table size: a one-month count ran in 446 ms (2026-10). Never apply the same pattern to `Asset`, `AssetData` or `telemetry.*`.

## Timestamps

- `LatestAssetData` time columns are `TIMESTAMP` (UTC). It has **no `datetime` column**.
  - `moduleTimestamp` (indexed) = device time, equal to the message's epoch `ts`.
  - `receivedDate`, `locTimestamp`, `interpolatedTimestamp`, `created`, `updated` also exist.
- `telemetry.mqtt.datetime` is `DATETIME` (no zone) holding the **server insert time** in UTC. It can lag the device `ts` by ~30 min or more. Filter windows on `datetime`, but report device time from `ts` in `data`.

## Core Relationships

```text
api.`Group` (customer hierarchy; treeRootId / rootGroupId = customer root)
  │ treeRootId (groups in customer tree)
  ▼
api.Asset (groupId, serial, assetTypeId)
  │
  ├── api.AssetType (assetTypeId; make) ──► api.Translation (nameId = id; en_us, de_de)
  ├── api.LatestAssetData (assetId unique, imei, moduleTimestamp) [1 row per asset, JSON data]
  └── api.AssetModuleMapping (assetId, activeFlag=1, deleted IS NULL)
        ▼
      api.Module (imei, moduleRevision, created)
        │ imei
        ▼
      telemetry.mqtt (data_ep = imei, datetime = server insert time)
```

## Golden Query Patterns

### 1. Customer Root Group Discovery [Discovery Pattern]
Discover the customer's root group ID by name. `isRoot` (int) and `name` are not indexed, so this scans `Group` (~72.5 k rows), which is acceptable:
```sql
SELECT id, name, treeRootId
FROM api.`Group`
WHERE isRoot = 1 AND deleted IS NULL AND name LIKE '%Numatic%'
LIMIT 10;
```

### 2. Customer Fleet IMEIs with De-duplication & Pagination [Production Pattern]
Given customer `treeRootId = 149`, retrieve unique active IMEIs. De-duplicates any reassigned modules by keeping the mapping with the latest device timestamp, and applies deterministic ordering for pagination:
```sql
WITH ranked_mappings AS (
  SELECT
    a.id AS asset_id,
    a.serial,
    m.imei,
    m.moduleRevision,
    g.name AS group_name,
    lad.moduleTimestamp AS last_seen,
    ROW_NUMBER() OVER (
      PARTITION BY m.imei
      ORDER BY lad.moduleTimestamp DESC, a.id DESC
    ) AS rn
  FROM api.`Group` g
  JOIN api.Asset a
    ON a.groupId = g.id AND a.deleted IS NULL
  JOIN api.AssetModuleMapping amm
    ON amm.assetId = a.id AND amm.activeFlag = 1 AND amm.deleted IS NULL
  JOIN api.Module m
    ON m.id = amm.moduleId
  LEFT JOIN api.LatestAssetData lad
    ON lad.assetId = a.id
  WHERE g.treeRootId = 149 AND g.deleted IS NULL
)
SELECT
  asset_id,
  serial,
  imei,
  moduleRevision,
  group_name,
  last_seen
FROM ranked_mappings
WHERE rn = 1
ORDER BY asset_id ASC
LIMIT 50;
```

To get the total count for the customer fleet first:
```sql
SELECT COUNT(DISTINCT m.imei) AS total_active_modules
FROM api.`Group` g
JOIN api.Asset a
  ON a.groupId = g.id AND a.deleted IS NULL
JOIN api.AssetModuleMapping amm
  ON amm.assetId = a.id AND amm.activeFlag = 1 AND amm.deleted IS NULL
JOIN api.Module m
  ON m.id = amm.moduleId
WHERE g.treeRootId = 149 AND g.deleted IS NULL
LIMIT 1;
```

### 3. Read Latest Data for Assets or IMEIs [Production Pattern]
Use `LatestAssetData` for fast single-row latest state. Filter on `assetId` (unique) or `imei` (indexed):
```sql
SELECT
  assetId,
  imei,
  moduleTimestamp,
  receivedDate,
  data
FROM api.LatestAssetData
WHERE assetId IN (1001, 1002, 1003)
LIMIT 50;
```

### 4. Query Raw Message History for IMEIs [Production Pattern]
Always pass explicit IMEIs and a bounded datetime filter (range scan on `data_ep_datetime`):
```sql
SELECT
  data_ep AS imei,
  datetime,
  ver,
  data
FROM telemetry.mqtt
WHERE data_ep IN ('123456789012345', '123456789012346')
  AND datetime >= NOW() - INTERVAL 7 DAY
ORDER BY datetime DESC
LIMIT 50;
```

### 5. Group and Customer of an IMEI [Production Pattern]
`Module.imei` (ref) → `idx_moduleId` → PK lookups. Every step is indexed:
```sql
SELECT
  m.imei,
  a.id AS asset_id,
  a.serial,
  g.id AS group_id,
  g.name AS group_name,
  tr.id AS tree_root_id,
  tr.name AS customer_name
FROM api.Module m
JOIN api.AssetModuleMapping amm
  ON amm.moduleId = m.id AND amm.activeFlag = 1 AND amm.deleted IS NULL
JOIN api.Asset a
  ON a.id = amm.assetId AND a.deleted IS NULL
LEFT JOIN api.`Group` g ON g.id = a.groupId
LEFT JOIN api.`Group` tr ON tr.id = g.treeRootId
WHERE m.imei = '353201359412050'
LIMIT 5;
```

### 6. Device Type of an Asset [Production Pattern]
Machine type name comes from `Translation` by `AssetType.nameId`; hardware comes from `Module.moduleRevision`. All joins are `const` lookups:
```sql
SELECT
  a.id AS asset_id,
  at.id AS asset_type_id,
  COALESCE(NULLIF(t.en_us, ''), NULLIF(t.de_de, '')) AS machine_type,
  at.make,
  m.imei,
  m.moduleRevision
FROM api.Asset a
JOIN api.AssetType at ON at.id = a.assetTypeId
LEFT JOIN api.Translation t ON t.id = at.nameId
LEFT JOIN api.AssetModuleMapping amm
  ON amm.assetId = a.id AND amm.activeFlag = 1 AND amm.deleted IS NULL
LEFT JOIN api.Module m ON m.id = amm.moduleId
WHERE a.id = 2226539
LIMIT 1;
```

### 7. Modules (IMEIs) Added in a Period [Bounded Scan Pattern]
`Module.created` is not indexed; this scans ~321 k rows (see invariant 8). Always bound both ends:
```sql
SELECT COUNT(*) AS added
FROM api.Module
WHERE created >= '2026-01-01' AND created < '2026-02-01'
  AND deleted IS NULL
  AND isFake = 0;
```

## Hardware & Data Quirks

- `Module.moduleRevision`: Identifies hardware generation (`TSIOT-KITR4P` = Phoenix, `R5` = Phoenix+, `R3` = older; `TSIOT-TTFT100-STD` also occurs). `moduleTypeId` is `NULL` on modern modules. `ModuleType` (`HUMMINGBIRD`, `STANDARD`, `GOLDFINCH`) is a legacy classification; do not use it to filter modern models.
- Firmware versions: Devices running test firmware report `ver = '0.0.0'`. If querying test fleets, include `(ver LIKE '0.2.%' OR ver = '0.0.0')`. Other version formats occur, such as `0.4.1+fl`.
- `Group.treeRootId` and `Group.rootGroupId` matched on the rows checked; it is not verified that they always match. Prefer `treeRootId`.
