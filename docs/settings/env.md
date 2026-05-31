# Environment Variable Reference

See the [settings guide](index.md) for a full walkthrough.

Tiozin reads configuration from environment variables at startup. Set them in your shell or a `.env` file. See [.env files](#env-files) for how Tiozin discovers them.

## General

| Variable | Description | Default |
|---|---|---|
| `TIO_JOB_NAMESPACE_TEMPLATE` | Jinja template used to derive `namespace` when not set on the job | `{{org}}.{{region}}.{{domain}}.{{subdomain}}` |

Available template variables for `TIO_JOB_NAMESPACE_TEMPLATE`: `org`, `region`, `domain`, `subdomain`, `layer`, `product`, `model`.

## Logging

| Variable | Description | Default |
|---|---|---|
| `LOG_LEVEL` | Log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`) | `INFO` |
| `TIO_LOG_DATE_FORMAT` | Timestamp format in log output | `iso` |
| `TIO_LOG_JSON` | Emit logs as JSON for log aggregation systems | `false` |
| `TIO_LOG_JSON_ENSURE_ASCII` | Force ASCII encoding in JSON logs | `false` |
| `TIO_LOG_SHOW_LOCALS` | Include local variables in exception tracebacks | `false` |
| `TIO_LOG_REDACT_MIN_LENGTH` | Minimum secret length to qualify for redaction in logs | `3` |

## Registry settings

<table>
  <thead>
    <tr><th>Registry</th><th>Variable</th><th>Description</th><th>Default</th></tr>
  </thead>
  <tbody>
    <tr><td rowspan="6">Setting</td><td><code>TIO_SETTING_REGISTRY_KIND</code></td><td>Plugin class name</td><td><code>tio_kernel:FileSettingRegistry</code></td></tr>
    <tr><td><code>TIO_SETTING_REGISTRY_LOCATION</code></td><td>Path or URL to the registry backend</td><td><code>null</code></td></tr>
    <tr><td><code>TIO_SETTING_REGISTRY_TIMEOUT</code></td><td>Request timeout in seconds</td><td><code>3</code></td></tr>
    <tr><td><code>TIO_SETTING_REGISTRY_READONLY</code></td><td>Reject write operations when set</td><td><code>false</code></td></tr>
    <tr><td><code>TIO_SETTING_REGISTRY_CACHE</code></td><td>Cache retrieved metadata in memory when set</td><td><code>false</code></td></tr>
    <tr><td><code>TIO_SETTING_REGISTRY_FAILFAST</code></td><td>Raise on missing metadata when set</td><td><code>true</code></td></tr>
    <tr><td rowspan="6">Job</td><td><code>TIO_JOB_REGISTRY_KIND</code></td><td>Plugin class name</td><td><code>tio_kernel:FileJobRegistry</code></td></tr>
    <tr><td><code>TIO_JOB_REGISTRY_LOCATION</code></td><td>Path or URL to the registry backend</td><td><code>null</code></td></tr>
    <tr><td><code>TIO_JOB_REGISTRY_TIMEOUT</code></td><td>Request timeout in seconds</td><td><code>3</code></td></tr>
    <tr><td><code>TIO_JOB_REGISTRY_READONLY</code></td><td>Reject write operations when set</td><td><code>false</code></td></tr>
    <tr><td><code>TIO_JOB_REGISTRY_CACHE</code></td><td>Cache retrieved metadata in memory when set</td><td><code>false</code></td></tr>
    <tr><td><code>TIO_JOB_REGISTRY_FAILFAST</code></td><td>Raise on missing metadata when set</td><td><code>true</code></td></tr>
    <tr><td rowspan="9">Schema</td><td><code>TIO_SCHEMA_REGISTRY_KIND</code></td><td>Plugin class name</td><td><code>tio_kernel:FileSchemaRegistry</code></td></tr>
    <tr><td><code>TIO_SCHEMA_REGISTRY_LOCATION</code></td><td>Path or URL to the registry backend</td><td><code>null</code></td></tr>
    <tr><td><code>TIO_SCHEMA_REGISTRY_TIMEOUT</code></td><td>Request timeout in seconds</td><td><code>3</code></td></tr>
    <tr><td><code>TIO_SCHEMA_REGISTRY_READONLY</code></td><td>Reject write operations when set</td><td><code>false</code></td></tr>
    <tr><td><code>TIO_SCHEMA_REGISTRY_CACHE</code></td><td>Cache retrieved metadata in memory when set</td><td><code>false</code></td></tr>
    <tr><td><code>TIO_SCHEMA_REGISTRY_FAILFAST</code></td><td>Raise on missing metadata when set</td><td><code>true</code></td></tr>
    <tr><td><code>TIO_SCHEMA_REGISTRY_SHOW_SCHEMA</code></td><td>Log schemas after retrieval</td><td><code>false</code></td></tr>
    <tr><td><code>TIO_SCHEMA_REGISTRY_SUBJECT_TEMPLATE</code></td><td>Jinja template used to derive the schema subject</td><td><code>{{org}}.{{region}}.{{domain}}.{{subdomain}}.{{layer}}.{{product}}.{{model}}</code></td></tr>
    <tr><td><code>TIO_SCHEMA_REGISTRY_DEFAULT_VERSION</code></td><td>Schema version used when not specified</td><td><code>latest</code></td></tr>
    <tr><td rowspan="6">Secret</td><td><code>TIO_SECRET_REGISTRY_KIND</code></td><td>Plugin class name</td><td><code>tio_kernel:EnvSecretRegistry</code></td></tr>
    <tr><td><code>TIO_SECRET_REGISTRY_LOCATION</code></td><td>Path or URL to the registry backend</td><td><code>null</code></td></tr>
    <tr><td><code>TIO_SECRET_REGISTRY_TIMEOUT</code></td><td>Request timeout in seconds</td><td><code>3</code></td></tr>
    <tr><td><code>TIO_SECRET_REGISTRY_READONLY</code></td><td>Reject write operations when set</td><td><code>false</code></td></tr>
    <tr><td><code>TIO_SECRET_REGISTRY_CACHE</code></td><td>Cache retrieved metadata in memory when set</td><td><code>false</code></td></tr>
    <tr><td><code>TIO_SECRET_REGISTRY_FAILFAST</code></td><td>Raise on missing metadata when set</td><td><code>true</code></td></tr>
    <tr><td rowspan="6">Transaction</td><td><code>TIO_TRANSACTION_REGISTRY_KIND</code></td><td>Plugin class name</td><td><code>tio_kernel:NoOpTransactionRegistry</code></td></tr>
    <tr><td><code>TIO_TRANSACTION_REGISTRY_LOCATION</code></td><td>Path or URL to the registry backend</td><td><code>null</code></td></tr>
    <tr><td><code>TIO_TRANSACTION_REGISTRY_TIMEOUT</code></td><td>Request timeout in seconds</td><td><code>3</code></td></tr>
    <tr><td><code>TIO_TRANSACTION_REGISTRY_READONLY</code></td><td>Reject write operations when set</td><td><code>false</code></td></tr>
    <tr><td><code>TIO_TRANSACTION_REGISTRY_CACHE</code></td><td>Cache retrieved metadata in memory when set</td><td><code>false</code></td></tr>
    <tr><td><code>TIO_TRANSACTION_REGISTRY_FAILFAST</code></td><td>Raise on missing metadata when set</td><td><code>true</code></td></tr>
    <tr><td rowspan="7">Lineage</td><td><code>TIO_LINEAGE_REGISTRY_KIND</code></td><td>Plugin class name</td><td><code>tio_kernel:NoOpLineageRegistry</code></td></tr>
    <tr><td><code>TIO_LINEAGE_REGISTRY_LOCATION</code></td><td>Path or URL to the registry backend</td><td><code>null</code></td></tr>
    <tr><td><code>TIO_LINEAGE_REGISTRY_TIMEOUT</code></td><td>Request timeout in seconds</td><td><code>3</code></td></tr>
    <tr><td><code>TIO_LINEAGE_REGISTRY_READONLY</code></td><td>Reject write operations when set</td><td><code>false</code></td></tr>
    <tr><td><code>TIO_LINEAGE_REGISTRY_CACHE</code></td><td>Cache retrieved metadata in memory when set</td><td><code>false</code></td></tr>
    <tr><td><code>TIO_LINEAGE_REGISTRY_FAILFAST</code></td><td>Raise on missing metadata when set</td><td><code>true</code></td></tr>
    <tr><td><code>TIO_LINEAGE_REGISTRY_EMIT_LEVEL</code></td><td>Granularity of lineage events emitted (<code>JOB</code>, <code>STEP</code>, <code>ALL</code>)</td><td><code>JOB</code></td></tr>
    <tr><td rowspan="6">Metric</td><td><code>TIO_METRIC_REGISTRY_KIND</code></td><td>Plugin class name</td><td><code>tio_kernel:NoOpMetricRegistry</code></td></tr>
    <tr><td><code>TIO_METRIC_REGISTRY_LOCATION</code></td><td>Path or URL to the registry backend</td><td><code>null</code></td></tr>
    <tr><td><code>TIO_METRIC_REGISTRY_TIMEOUT</code></td><td>Request timeout in seconds</td><td><code>3</code></td></tr>
    <tr><td><code>TIO_METRIC_REGISTRY_READONLY</code></td><td>Reject write operations when set</td><td><code>false</code></td></tr>
    <tr><td><code>TIO_METRIC_REGISTRY_CACHE</code></td><td>Cache retrieved metadata in memory when set</td><td><code>false</code></td></tr>
    <tr><td><code>TIO_METRIC_REGISTRY_FAILFAST</code></td><td>Raise on missing metadata when set</td><td><code>true</code></td></tr>
  </tbody>
</table>

## .env files

Tiozin loads `.env` files automatically from these locations, in order:

1. `/etc/tiozin/.env` (system-wide)
2. `~/.env`
3. `~/.config/tiozin/.env`
4. `/config/.env`
5. `/tiozin/.env`
6. `.env` in the current directory and all parent directories

Later files take precedence over earlier ones. A project `.env` overrides system defaults. Variables set directly in the shell always take precedence over `.env` files.

Copy `.env.example` from the project root to get started:

```bash
cp .env.example .env
```
