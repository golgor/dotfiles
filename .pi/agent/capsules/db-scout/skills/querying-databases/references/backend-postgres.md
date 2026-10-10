# Backend Production Database (PostgreSQL)

Connection: **`Backend Production`**  
Engine: PostgreSQL 15+ (Google Cloud SQL)  
Database: **`backend`**  
Schema: **`public`**

## Databases on Instance

| Database | Purpose |
|---|---|
| `backend` | Primary Django database for the IoT Backend (`ToolSense/backend`). |
| `api_replica` | Internal replica of api-core MySQL data. |
| `n8n`, `n8n_beni` | Workflow automation database. |

## Primary Subsystems & Tables (`backend.public`)

### 1. Phoenix Dynamic Configuration (`dynamicconfig_*`)
Holds configuration profiles and assignments for Phoenix devices (R4/R5 hardware).

- `dynamicconfig_dynamicconfiguration`: Stored configuration profiles. Key columns: `id (PK)`, `config_name`, `config_data` (`jsonb`). **The highest `id` for a given `config_name` is always the active configuration version.**
- `dynamicconfig_assettypemapping`: Maps machine model `asset_type_id` to `config_name`.
- `dynamicconfig_modulemapping`: Maps specific device `imei` to `config_name`, with `override_config` (`boolean`).

#### Configuration Resolution Hierarchy
1. **Asset Type Mapping (`dynamicconfig_assettypemapping`):** The standard/baseline configuration. If a module's asset has an `asset_type_id` in Frontend MySQL, it receives this configuration by default. An IMEI does **not** need a row in `dynamicconfig_modulemapping` to have a valid active configuration!
2. **Module Override (`dynamicconfig_modulemapping`):** If an IMEI has an entry with `override_config = true`, its module mapping overrides the asset type configuration.

### 2. Over-The-Air Firmware (`ota_*`)
- **`ota_publishedversion`:** The catalog of available published firmware versions. **This is the ONLY active OTA table in this database.**
- **STALE TABLES:** `ota_imeicurrent` and `ota_imeidesired` are **stale and no longer used**. Do not query them for device firmware state. Check firmware versions via `telemetry.mqtt` (ver column) or `IoT Production` (`iot_fota`).

## Invariants & Gotchas

1. **Phoenix Config Lives Here:** Phoenix dynamic configurations live in `Backend Production`, not in `IoT Production`'s `iot_configurations`.
2. **Highest `id` is Active:** When joining `dynamicconfig_dynamicconfiguration`, always select the highest `id` for that `config_name` (e.g. `ORDER BY id DESC LIMIT 1` or join on `MAX(id)`).
3. **Asset Type Cross-DB Dependency:** Asset-type resolution requires the asset's `assetTypeId` from Frontend MySQL (`api.Asset`).

## Golden Query Patterns

### 1. Inspect Dynamic Configuration Assigned to an IMEI
Check both direct module mapping and configuration data:
```sql
SELECT
  mm.imei,
  mm.config_name,
  mm.override_config,
  dc.id AS config_version_id,
  dc.config_data
FROM dynamicconfig_modulemapping mm
JOIN dynamicconfig_dynamicconfiguration dc
  ON dc.id = (
    SELECT MAX(id)
    FROM dynamicconfig_dynamicconfiguration sub
    WHERE sub.config_name = mm.config_name
  )
WHERE mm.imei = '123456789012345'
LIMIT 1;
```

### 2. Check Configuration Assigned to an Asset Type
When an IMEI has no module override, its config comes from its machine asset type:
```sql
SELECT
  atm.asset_type_id,
  atm.config_name,
  dc.id AS config_version_id,
  dc.config_data
FROM dynamicconfig_assettypemapping atm
JOIN dynamicconfig_dynamicconfiguration dc
  ON dc.id = (
    SELECT MAX(id)
    FROM dynamicconfig_dynamicconfiguration sub
    WHERE sub.config_name = atm.config_name
  )
WHERE atm.asset_type_id = 1234
LIMIT 1;
```

### 3. Find Configurations with a Specific Parameter
Search inside the `toolsconfig` JSONB section:
```sql
SELECT
  config_name,
  id AS config_version_id,
  config_data->'toolsconfig'->>'log_interval' AS log_interval
FROM dynamicconfig_dynamicconfiguration
WHERE config_data->'toolsconfig' ? 'log_interval'
ORDER BY id DESC
LIMIT 50;
```

### 4. Check Published Firmware Versions
Query the active OTA published catalog:
```sql
SELECT
  id,
  version,
  device_id,
  variant_id,
  created_at
FROM ota_publishedversion
ORDER BY id DESC
LIMIT 50;
```
