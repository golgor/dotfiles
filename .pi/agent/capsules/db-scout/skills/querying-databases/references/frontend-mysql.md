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
| `api.Group` | ~65 k | Customer hierarchy tree. Indexed on `treeRootId`. |

## Invariants & Circuit Breakers

1. **Unkillable queries:** The DBX read-only user cannot execute `KILL QUERY`. Any runaway query must run to completion. Always verify `EXPLAIN` before running on non-catalog tables.
2. **Never join fleet trees into `telemetry.mqtt`:** A join from `Group` or `Asset` into `telemetry.mqtt` forces a massive dependent scan. Always break into two steps: extract IMEIs first, then query `telemetry.mqtt` with bounded `data_ep IN ('<imei1>', ...)` and an explicit `datetime` range.
3. **`Asset.moduleId` is mostly empty:** Do not rely on `Asset.moduleId`. Always resolve modules via `AssetModuleMapping` where `activeFlag = 1 AND deleted IS NULL`.
4. **Translation table scanning:** Never filter `api.Translation` on text or language columns. Look up translations strictly by primary key (`id = AssetType.nameId`).
5. **Soft deletes:** Always filter `deleted IS NULL` on `Group`, `Asset`, and `AssetModuleMapping`.

## Core Relationships

```text
Group (customer hierarchy)
  │ treeRootId (groups in customer tree)
  ▼
Asset (groupId)
  │
  ├── AssetType (assetTypeId) ──► Translation (nameId = id)
  ├── LatestAssetData (assetId) [1 row per asset, JSON data]
  └── AssetModuleMapping (assetId, activeFlag=1, deleted IS NULL)
        ▼
      Module (imei, moduleRevision, moduleTypeId)
        │ imei
        ▼
      telemetry.mqtt (data_ep = imei, datetime)
```

## Golden Query Patterns

### 1. Find Customer Root Group
Find the customer's root group by name:
```sql
SELECT id, name, treeRootId
FROM api.Group
WHERE isRoot = 1 AND deleted IS NULL AND name LIKE '%Numatic%'
LIMIT 10;
```

### 2. Find All Assets & IMEIs for a Customer
Given customer `treeRootId = 149`:
```sql
SELECT
  a.id AS asset_id,
  a.name AS asset_name,
  m.imei,
  m.moduleRevision,
  g.name AS group_name
FROM api.Group g
JOIN api.Asset a
  ON a.groupId = g.id AND a.deleted IS NULL
JOIN api.AssetModuleMapping amm
  ON amm.assetId = a.id AND amm.activeFlag = 1 AND amm.deleted IS NULL
JOIN api.Module m
  ON m.id = amm.moduleId
WHERE g.treeRootId = 149 AND g.deleted IS NULL
LIMIT 500;
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
WHERE assetId IN (1001, 1002, 1003);
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
LIMIT 100;
```

## Hardware & Data Quirks

- `Module.moduleRevision`: Identifies hardware generation (`TSIOT-KITR4P` = Phoenix, `R5` = Phoenix+, `R3` = older). `ModuleType` (`HUMMINGBIRD`, `STANDARD`, `GOLDFINCH`) is a legacy classification; do not use it to filter modern models.
- Multi-Asset IMEIs: An IMEI can occasionally have two historical mappings. De-duplicate on `m.imei` and select the asset with the newest `LatestAssetData.datetime`.
- Firmware test builds: Devices running test firmware report `ver = '0.0.0'`. If querying test fleets, include `(ver LIKE '0.2.%' OR ver = '0.0.0')`.
