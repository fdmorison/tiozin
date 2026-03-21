# Templates Reference

Tiozin uses [Jinja2](https://jinja.palletsprojects.com/) to render dynamic values in your job YAML files.
Any string value in a job definition can contain template expressions using `{{ }}` syntax.

## The basics

Use `{{ }}` to insert a value:

```yaml
outputs:
  - kind: SparkFileOutput
    path: .output/lake-{{domain}}-{{layer}}/{{product}}
```

Use filters with `|` to transform a value:

```yaml
path: .output/ids/{{run_id | nodash}}
```

## Job metadata variables

These come from the job definition itself and are always available:

| Variable | Example value |
|---|---|
| `name` | `"ecommerce_orders_ingestion"` |
| `slug` | `"ecommerce-orders-ingestion"` |
| `org` | `"tiozin"` |
| `region` | `"latam"` |
| `domain` | `"ecommerce"` |
| `subdomain` | `"retail"` |
| `layer` | `"raw"` |
| `product` | `"orders"` |
| `model` | `"orders"` |
| `owner` | `"data@tiozin.com"` |
| `maintainer` | `"tiozin"` |
| `cost_center` | `"tio_scrooge"` |
| `run_id` | `"a1b2c3d4"` |
| `run_attempt` | `1` |

Use them freely:

```yaml
path: .output/lake-{{domain}}-{{layer}}/{{product}}/{{model}}
```

## Environment variables

Use `ENV.<VAR_NAME>` to read environment variables at runtime:

```yaml
runner:
  kind: SparkRunner
  log_level: "{{ ENV.LOG_LEVEL }}"
```

If the variable is not set, Tiozin raises an error at render time. Use `| default()` to make a variable optional:

```yaml
log_level: "{{ ENV.LOG_LEVEL | default('INFO') }}"
```

## Secrets

Use `SECRET.<name>` to fetch a secret from the configured `SecretRegistry` at render time:

```yaml
runner:
  kind: SparkRunner
  url: jdbc:postgresql://host:5432/db?password={{ SECRET.DB_PASSWORD }}
```

Item access also works:

```yaml
url: jdbc:postgresql://host:5432/db?password={{ SECRET["DB_PASSWORD"] }}
```

The retrieved value is a `Secret` object. It behaves as a plain string in all contexts (Jinja templates, Pydantic models, connection libraries) but masks itself in logs and reprs:

```yaml
url: jdbc:postgresql://host:5432/db?password={{ SECRET.DB_PASSWORD }}
# rendered value: jdbc:postgresql://host:5432/db?password=mypassword
# logged as:      jdbc:postgresql://host:5432/db?password=***
```

If the secret is not found, Tiozin raises `SecretNotFoundError` at render time.

The default registry reads secrets from environment variables. To use a different backend (Vault, AWS Secrets Manager, etc.), configure `registries.secret` in `tiozin.yaml`. See [Settings Reference](settings.md) and [EnvSecretRegistry](tio_kernel/env-secret-registry.md).

## Date variables

Tiozin injects a **`TemplateDate`** object anchored to the current time at render,
available as `DAY`:

```yaml
# Just prints the date: 2026-01-17
path: .output/lake/date={{ DAY }}

# Navigate: yesterday
path: .output/lake/date={{ DAY[-1] }}

# 7 days ahead
path: .output/lake/date={{ DAY[7] }}
```

### Navigating relative to today

`DAY[n]` moves `n` days from the nominal time:

```yaml
{{ DAY[0] }}   → 2026-01-17   (today)
{{ DAY[-1] }}  → 2026-01-16   (yesterday)
{{ DAY[1] }}   → 2026-01-18   (tomorrow)
{{ DAY[-7] }}  → 2026-01-10   (last week)
```

### Chaining formats

Use a format property to control the output:

```yaml
{{ DAY[-1].iso }}          → 2026-01-16T10:30:45+00:00
{{ DAY[-1].flat_date }}    → 2026-01-16
{{ DAY[-1].deep_date }}    → year=2026/month=01/day=16
```

Chaining is order-independent: format and navigation can come in any order:

```yaml
{{ DAY[-1].flat_hour }}   ==   {{ DAY.flat_hour.yesterday }}
```

### Convenience shortcuts

These are also available directly (without `D`), as shortcuts for `D[0].<property>`:

```yaml
{{ today }}       → 2026-01-17
{{ yesterday }}   → 2026-01-16
{{ tomorrow }}    → 2026-01-18
{{ iso }}         → 2026-01-17T10:30:45+00:00
{{ flat_date }}   → 2026-01-17
{{ deep_date }}   → year=2026/month=01/day=17
```

## Pinning to a specific hour

Use `.at<HH>` to jump to a specific hour of the day:

```yaml
{{ D[0].at09 }}            → 2026-01-17T09:00:00+00:00
{{ D[-1].at00.flat_hour }} → 2026-01-16T00
{{ D[0].midnight }}        → 2026-01-17T00:00:00+00:00
{{ D[0].noon }}            → 2026-01-17T12:00:00+00:00
```

## Common patterns

### Lake path with partition by date

```yaml
path: .output/lake-{{domain}}-{{layer}}/{{product}}/date={{ DAY[-1] }}
```

### Deep Hive-style partitioning

```yaml
path: .output/lake/{{product}}/{{ DAY[-1].deep_date }}
# → .output/lake/orders/year=2026/month=01/day=16
```

### Hourly partitioning

```yaml
path: .output/lake/{{product}}/{{ DAY[0].at06.deep_hour }}
# → .output/lake/orders/year=2026/month=01/day=17/hour=06
```

### Filesystem-safe timestamps

```yaml
path: .output/archive/{{ DAY[0].flat_ts }}
# → .output/archive/2026-01-17T10-30-45
```

### Run ID in path

```yaml
path: .output/{{domain}}/{{run_id | nodash}}
# → .output/ecommerce/a1b2c3d4
```

## String filters

Filters transform string values. Apply with `|`:

| Filter | Description | Example output |
|---|---|---|
| `nodash` | Remove all dashes | `"2026-01-14"` → `"20260114"` |
| `notz` | Remove timezone suffix | `"2026-01-14T10:00:00+00:00"` → `"2026-01-14T10:00:00"` |
| `compact` | Remove all non-alphanumeric characters | `"2026-01-14T01:59"` → `"20260114T0159"` |
| `fs_safe` | Make filesystem-safe (colons → dashes, spaces → underscores) | `"2026-01-14 10:59"` → `"2026-01-14_10-59"` |

You can also use standard Jinja2 filters like `upper`, `lower`, `replace`, `default`, etc.

```yaml
path: ./data/{{ domain | upper }}         → ./data/ECOMMERCE
name: {{ product | replace("_", "-") }}   → orders-v2
```

## Full date property reference

All properties are chainable. When used as standalone variables, they resolve for `D[0]` (today's nominal time).

### Navigation

| Property / Syntax | Description | Example output |
|---|---|---|
| `D[n]` | Navigate `n` days (negative = past) | `D[-1]` → `2026-01-16` |
| `.today` | Same day (no-op) | `2026-01-17` |
| `.yesterday` | Previous day | `2026-01-16` |
| `.tomorrow` | Next day | `2026-01-18` |
| `.start_of_year` | Jan 1st of current year | `2026-01-01` |
| `.start_of_month` | 1st of current month | `2026-01-01` |
| `.start_of_day` | Midnight of current day | `2026-01-17` |
| `.start_of_week` | Monday of current week | `2026-01-12` |
| `.start_of_hour` | Start of current hour (chain with format) | `D[0].start_of_hour.flat_hour` → `2026-01-17T10` |
| `.start_of_minute` | Start of current minute (chain with format) | `D[0].start_of_minute.flat_minute` → `2026-01-17T10-30` |
| `.midnight` | This day at 00:00:00 | `2026-01-17T00:00:00+00:00` |
| `.noon` | This day at 12:00:00 | `2026-01-17T12:00:00+00:00` |
| `.at00` to `.at23` | This day at HH:00:00 | `D[0].at09` → `2026-01-17T09:00:00+00:00` |

### ISO / datetime formats

| Property | Description | Example output |
|---|---|---|
| `.iso` | ISO 8601, seconds precision | `2026-01-17T10:30:45+00:00` |
| `.iso_ms` | ISO 8601 with milliseconds | `2026-01-17T10:30:45.000+00:00` |
| `.iso_micro` | ISO 8601 with microseconds | `2026-01-17T10:30:45.000000+00:00` |
| `.ts_naive` | ISO 8601 without timezone | `2026-01-17T10:30:45` |
| `.sql_datetime` | SQL datetime | `2026-01-17 10:30:45` |
| `.date` | Date only | `2026-01-17` |
| `.time` | Time only | `10:30:45` |

### Airflow-compatible formats

| Property | Description | Example output |
|---|---|---|
| `.ds` | Date string | `2026-01-17` |
| `.ts` | Timestamp ISO 8601 | `2026-01-17T10:30:45+00:00` |
| `.prev_ds` | Previous day date string | `2026-01-16` |
| `.next_ds` | Next day date string | `2026-01-18` |
| `.execution_date` | ISO 8601 datetime | `2026-01-17T10:30:45+00:00` |
| `.logical_date` | ISO 8601 datetime | `2026-01-17T10:30:45+00:00` |
| `.data_interval_start` | ISO 8601 datetime | `2026-01-17T10:30:45+00:00` |
| `.data_interval_end` | Next day ISO 8601 datetime | `2026-01-18T10:30:45+00:00` |

### Flat filesystem paths

Safe for filenames: dashes instead of colons, no spaces.

| Property | Description | Example output |
|---|---|---|
| `.flat_year` | Year | `2026` |
| `.flat_month` | Year and month | `2026-01` |
| `.flat_date` / `.flat_day` | Full date | `2026-01-17` |
| `.flat_hour` | Date and hour | `2026-01-17T10` |
| `.flat_minute` | Date, hour, and minute | `2026-01-17T10-30` |
| `.flat_second` / `.flat_ts` | Date and full time | `2026-01-17T10-30-45` |

### Deep (Hive-style) partitioned paths

| Property | Description | Example output |
|---|---|---|
| `.deep_year` | Year partition | `year=2026` |
| `.deep_month` | Year and month partitions | `year=2026/month=01` |
| `.deep_date` / `.deep_day` | Year, month, and day partitions | `year=2026/month=01/day=17` |
| `.deep_hour` | Year through hour partitions | `year=2026/month=01/day=17/hour=10` |
| `.deep_minute` | Year through minute partitions | `year=2026/month=01/day=17/hour=10/min=30` |
| `.deep_second` / `.deep_ts` | Year through second partitions | `year=2026/month=01/day=17/hour=10/min=30/sec=45` |

### Individual date/time parts

| Property | Description | Example output |
|---|---|---|
| `.YYYY` | Year (4 digits) | `2026` |
| `.MM` | Month (2 digits) | `01` |
| `.DD` | Day of month (2 digits) | `17` |
| `.DDD` | Day of year (3 digits, zero-padded) | `017` |
| `.HH` | Hour (24h, 2 digits) | `10` |
| `.mm` | Minute (2 digits) | `30` |
| `.ss` | Second (2 digits) | `45` |
| `.Z` | Timezone offset with colon | `+00:00` |
| `.ZZ` | Timezone offset without colon | `+0000` |
| `.z` / `.zz` | Timezone name | `UTC` |

### Unix timestamps

| Property | Description | Example output |
|---|---|---|
| `.unix` | Unix timestamp (integer seconds) | `1768370397` |
| `.unix_float` | Unix timestamp (float) | `1768370397.0` |
