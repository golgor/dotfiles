# IoT Production Database (PostgreSQL)

Connection: **`IoT Production`**  
Engine: PostgreSQL 15+ (Google Cloud SQL)  
Architecture: **One database per service** (always specify `database` parameter in DBX).

## Databases & Service Owners

| Database | Service Owner | What it holds |
|---|---|---|
| **`iot_sim_governance`** | SIM Governance | SIM cards, ICCID-to-IMEI mappings, carrier states (1NCE, Onomondo, Truphone, T-Mobile), consumption snapshots, ERPNext billing reconciliation. |
| **`iot_fota`** | FOTA Service | Firmware release catalog, target product lines, tenant eligibility, device firmware revision states. |
| **`iot_configurations`** | IoT Configurator | Non-Phoenix device configurations, configuration sets, device sync requests and task attempts, FOTA batch jobs. |
| **`iot_api_test`** | Test API | `devices`, `readings`. |
| `openbao` | OpenBao Vault | Encrypted secrets backend storage. |
| `authentik`, `backstage`, `grafana` | Platform Tools | Internal platform state. |
| `kestrel_fota`, `iot_flespi_edge`, `iot_fleet_health` | Placeholders | Currently have no tables in `public` schema. |

## Subsystems & Golden Queries

### 1. SIM Governance (`iot_sim_governance`)
Maps hardware IMEIs to physical SIMs and carriers, and tracks data consumption.

#### Find SIM & Carrier Details by IMEI
```sql
-- database: iot_sim_governance
SELECT
  m.imei,
  m.iccid,
  m.provider,
  m.source,
  m.valid_from,
  m.valid_to
FROM sim_fleet_iccidimeimapping m
WHERE m.imei IN ('123456789012345', '123456789012346')
ORDER BY m.discovered_at DESC
LIMIT 50;
```

#### Check Carrier State for a 1NCE SIM
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

#### Check Carrier State for an Onomondo SIM
```sql
-- database: iot_sim_governance
SELECT
  iccid,
  imei,
  sim_status,
  snapshot_date
FROM provider_onomondo_simstate
WHERE iccid = '8988303000000000001'
ORDER BY snapshot_date DESC
LIMIT 1;
```

### 2. Firmware Updates (`iot_fota`)
Manages firmware releases, target device compatibility, and tenant rollout rules.

#### Check Firmware Releases for a Product Line
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
WHERE pl.name ILIKE 'phoenix%'
ORDER BY fr.created_at DESC
LIMIT 50;
```

#### Check Firmware Eligibility for a Tenant
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
WHERE t.name ILIKE '%Numatic%'
ORDER BY fr.created_at DESC
LIMIT 50;
```

### 3. IoT Configurator (`iot_configurations`)
Manages configuration sets and delivery sync tasks for IoT devices.

#### Check Device Configuration & Sync Status
```sql
-- database: iot_configurations
SELECT
  dc.device_id,
  dc.configuration_version,
  dc.status,
  dc.updated_at
FROM device_configurations dc
WHERE dc.device_id = '123456789012345'
LIMIT 1;
```

## Invariants & Gotchas

1. **Always name the target database:** There is no default database. Always pass `database: "iot_sim_governance"`, `"iot_fota"`, or `"iot_configurations"` when calling DBX.
2. **Phoenix configurations are NOT here:** Phoenix dynamic configurations live in `Backend Production` (`backend.dynamicconfig_*`), not in `iot_configurations`.
3. **Missing catalog statistics:** Many tables report `reltuples = -1` in `pg_class`. Always apply explicit filters and `LIMIT` rather than trusting catalog row counts.
