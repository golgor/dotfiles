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

- `dynamicconfig_dynamicconfiguration`: One row per configuration version. Key column: `config_data` (`jsonb`).
- `dynamicconfig_modulemapping`: Per-IMEI assignment: `imei`, `config_name`, `override_config`.
- `dynamicconfig_assettypemapping`: Per-machine-model assignment: `asset_type_id`, `config_name`.

### 2. Over-The-Air Firmware (`ota_*`)
Tracks firmware versions and target device mappings for Phoenix.

- `ota_device`: Registered devices.
- `ota_imeicurrent`: Currently reported firmware version per IMEI.
- `ota_imeidesired`: Desired firmware version targeted per IMEI.
- `ota_publishedversion`: Catalog of available firmware builds.

### 3. Onboarding & Connectors (`onboard_*`, `connector_*`)
- `onboard_frontendconfig`, `onboard_servicedefaultdb`: Provisioning defaults.
- `connector_modulemessage`: Queue/state of incoming device messages.

## Invariants & Gotchas

1. **Phoenix Config Boundary:** Phoenix dynamic configurations live **here**, not in the IoT Production database `iot_configurations`. If asked about Phoenix device configuration parameters or overrides, check this database.
2. **Asset Type Resolution:** The backend resolves machine asset types by querying the Frontend MySQL database (`rollout_db`) at runtime. It does not replicate asset metadata locally.
3. **JSONB Comparison:** To inspect configuration differences, compare jsonb objects with `IS DISTINCT FROM` or `jsonb_object_keys`.

## Golden Query Patterns

### 1. Inspect Dynamic Configuration Assigned to an IMEI
```sql
SELECT
  mm.imei,
  mm.config_name,
  mm.override_config,
  dc.config_data
FROM dynamicconfig_modulemapping mm
LEFT JOIN dynamicconfig_dynamicconfiguration dc
  ON dc.config_name = mm.config_name
WHERE mm.imei = '123456789012345';
```

### 2. Find Devices with a Specific Configuration Parameter
Search inside the `toolsconfig` JSONB section:
```sql
SELECT
  config_name,
  config_data->'toolsconfig'->>'log_interval' AS log_interval
FROM dynamicconfig_dynamicconfiguration
WHERE config_data->'toolsconfig' ? 'log_interval'
LIMIT 50;
```

### 3. Check Current vs Desired Firmware for IMEIs
```sql
SELECT
  c.imei,
  c.version AS current_version,
  d.version AS desired_version
FROM ota_imeicurrent c
LEFT JOIN ota_imeidesired d
  ON d.imei = c.imei
WHERE c.imei IN ('123456789012345', '123456789012346')
LIMIT 50;
```
