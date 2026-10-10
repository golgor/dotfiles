# Frontend Production Database (MySQL)

Connection: **`Frontend Production`**  
Engine: MySQL 8  
Schemas: **`api`** (platform data), **`telemetry`** (raw device messages)

## Size & Table Scale

| Table | Est. Rows | Key Caution |
|---|---|---|
| `telemetry.mqtt` | ~370 M | Indexed **only** on `(data_ep, datetime)`, `ver`, and PK. |
| `telemetry.mqtt-ble` | ~280 M | Raw BLE advertisement logs. Same indexing caveats as `mqtt`. |
| `api.AssetData` | ~252 M | Processed message history. Index on `(assetId, created)`. |
| `api.Translation` | ~149 M | **No secondary indexes.** Lookup only by primary key `id`. |
| `api.Asset` | ~1.2 M | Digital twins. Index on `(groupId, deleted, assetTypeId)`. |
| `api.AssetModuleMapping` | ~111 k | Active module links. Filter `activeFlag = 1 AND deleted IS NULL`. |
| `api.Module` | ~341 k | Hardware modules. Indexed on `imei`. |
| `api.LatestAssetData` | ~84 k | Exactly one latest JSON message per asset (`assetId` unique). |
| `api.`Group`` | ~65 k | **Reserved keyword in MySQL.** Always quote as `` `Group` ``! Indexed on `treeRootId`. |

## Invariants & Circuit Breakers

1. **Quote `Group`:** `GROUP` is a reserved SQL keyword. Writing `FROM api.Group` causes a fatal syntax error. Always write `api.`Group``.
2. **Unkillable queries:** The DBX read-only user cannot execute `KILL QUERY`. Any runaway query must run to completion. Always verify `EXPLAIN` before running on non-catalog tables.
3. **Never join fleet trees into `telemetry.mqtt`:** A join from `Group` or `Asset` into `telemetry.mqtt` forces a massive dependent scan. Always break into two steps: extract IMEIs first (max 50), then query `telemetry.mqtt` with bounded `data_ep IN ('<imei1>', ...)` and an explicit `datetime` range.
4. **`Asset.moduleId` is mostly empty:** Do not rely on `Asset.moduleId`. Always resolve modules via `AssetModuleMapping` where `activeFlag = 1 AND deleted IS NULL`.
5. **Translation table scanning:** Never filter `api.Translation` on text or language columns. Look up translations strictly by primary key (`id = AssetType.nameId`).
6. **Soft deletes & active mappings:** Always filter `deleted IS NULL` on `` `Group` ``, `Asset`, and `AssetModuleMapping`. There is only one active module per asset at a given time (`activeFlag = 1 AND deleted IS NULL`).

## Core Relationships

```text
api.`Group` (customer hierarchy)
  │ treeRootId (groups in customer tree)
  ▼
api.Asset (groupId)
  │
  ├── api.AssetType (assetTypeId) ──► api.Translation (nameId = id)
  ├── api.LatestAssetData (assetId) [1 row per asset, JSON data]
  └── api.AssetModuleMapping (assetId, activeFlag=1, deleted IS NULL)
        ▼
      api.Module (imei, moduleRevision, moduleTypeId)
        │ imei
        ▼
      telemetry.mqtt (data_ep = imei, datetime)
```

## Golden Query Patterns

### 1. Customer Root Group Discovery
Find the customer's root group by name (discovery query with explicit limit):
```sql
SELECT id, name, treeRootId
FROM api.`Group`
WHERE isRoot = 1 AND deleted IS NULL AND name LIKE '%Numatic%'
LIMIT 10;
```

### 2. Customer Fleet IMEIs & Pagination
Given customer `treeRootId = 149`, retrieve assets with deterministic ordering.
For large fleets, use cursor pagination on `a.id`:
```sql
SELECT
  a.id AS asset_id,
  a.name AS asset_name,
  m.imei,
  m.moduleRevision,
  g.name AS group_name
FROM api.`Group` g
JOIN api.Asset a
  ON a.groupId = g.id AND a.deleted IS NULL
JOIN api.AssetModuleMapping amm
  ON amm.assetId = a.id AND amm.activeFlag = 1 AND amm.deleted IS NULL
JOIN api.Module m
  ON m.id = amm.moduleId
WHERE g.treeRootId = 149 AND g.deleted IS NULL
  -- AND a.id > :last_seen_asset_id (for subsequent pages)
ORDER BY a.id ASC
LIMIT 50;
```

To get the total count for the customer fleet first:
```sql
SELECT COUNT(DISTINCT a.id) AS total_assets
FROM api.`Group` g
JOIN api.Asset a
  ON a.groupId = g.id AND a.deleted IS NULL
JOIN api.AssetModuleMapping amm
  ON amm.assetId = a.id AND amm.activeFlag = 1 AND amm.deleted IS NULL
WHERE g.treeRootId = 149 AND g.deleted IS NULL;
```

### 3. Read Latest Telemetry for Assets
Use `LatestAssetData` for fast single-row latest state:
```sql
SELECT
  assetId,
  imei,
  datetime,
  data
FROM api.LatestAssetData
WHERE assetId IN (1001, 1002, 1003)
LIMIT 50;
```

### 4. Query Raw Message History for IMEIs
Always pass explicit IMEIs and a bounded datetime filter:
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

## Hardware & Data Quirks

- `Module.moduleRevision`: Identifies hardware generation (`TSIOT-KITR4P` = Phoenix, `R5` = Phoenix+, `R3` = older). `ModuleType` (`HUMMINGBIRD`, `STANDARD`, `GOLDFINCH`) is a legacy classification; do not use it to filter modern models.
- De-duplication: If aggregating across time where an IMEI moved between assets, de-duplicate on `m.imei` and select the asset with the newest `LatestAssetData.datetime`.
- Firmware test builds: Devices running test firmware report `ver = '0.0.0'`. If querying test fleets, include `(ver LIKE '0.2.%' OR ver = '0.0.0')`.
