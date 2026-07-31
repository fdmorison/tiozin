# FileSchemaRegistry

Stores schemas as YAML files, one file per subject, on a local folder or any location fsspec can reach.

```yaml
registries:
  schema:
    kind: tio_kernel:FileSchemaRegistry
    location: examples/schemas
```

This is the default schema registry. Each file under `location` is a plain YAML representation of a single schema, and the filename without the `.yaml` extension is the subject.

## Parameters

| Property | Description | Default |
|---|---|---|
| `location` | Root path or URI where schema files are stored | |
| Any extra key | Any key that is not a named parameter is forwarded to [fsspec](https://filesystem-spec.readthedocs.io/en/latest/) as a storage option, such as credentials or region. Collected internally into `**options` | |

Subject resolution is shared by every schema registry and is configured with `subject_template`, `default_version`, and `show_schema`. See [How to Use Schemas in Jobs](../how-to/schemas.md).

## How Schemas Are Stored

A lookup for the subject `tiozin.eu.ecommerce.sales.raw.storefront.customers` reads a single file:

```text
examples/schemas/tiozin.eu.ecommerce.sales.raw.storefront.customers.yaml
# → <location>/<subject>.yaml
```

So a folder of schemas looks like this:

```text
examples/schemas/
  tiozin.eu.ecommerce.sales.raw.storefront.customers.yaml
  tiozin.eu.ecommerce.sales.raw.storefront.orders.yaml
  tiozin.latam.literature.classics.raw.shakespeare.shakespeare.yaml
```

When `location` is not set, the subject is used as the path, resolved relative to the working directory.

Registering a schema serializes it back to YAML and writes it to that same path, replacing the file when it already exists.

If no file matches the subject, the registry raises `SchemaNotFoundError`. With `failfast: false`, the framework logs a warning and returns `None` instead, and the step runs without a schema.

`FileSchemaRegistry` ignores the requested schema version, since each file holds exactly one schema. Backends that keep several versions of a subject use it to pick one.

## Remote Locations

`location` accepts any path or URI supported by [fsspec](https://filesystem-spec.readthedocs.io/en/latest/):

| Scheme | Example |
|---|---|
| Local path | `examples/schemas` |
| Amazon S3 | `s3://my-bucket/schemas` |
| Google Cloud Storage | `gs://my-bucket/schemas` |
| Azure Blob Storage | `az://my-container/schemas` |
| HTTP / HTTPS | `https://schemas.example.com/tiozin` |
| FTP | `ftp://host/schemas` |
| SFTP | `sftp://host/schemas` |

Remote backends need credentials and connection settings. Add each one as a key directly under `registries.schema`, and the registry forwards it unchanged to fsspec when it reads or writes a schema file. The accepted keys depend on the storage backend.

In the example below, `key`, `secret`, and `client_kwargs` are not named parameters, so they are collected into the registry's `**options` and forwarded to fsspec to authenticate against S3:

```yaml
registries:
  schema:
    kind: tio_kernel:FileSchemaRegistry
    location: s3://my-bucket/schemas
    key: AKIAIOSFODNN7EXAMPLE
    secret: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
    client_kwargs:
      region_name: us-east-1
```

For the full list of options per backend, see the [fsspec documentation](https://filesystem-spec.readthedocs.io/en/latest/).

## Shared Registry Options

Every registry accepts the same four options, and each one has a matching environment variable:

| Property | Description | Default | Environment variable |
|---|---|---|---|
| `readonly` | Reject write operations | `false` | `TIO_SCHEMA_REGISTRY_READONLY` |
| `cache` | Cache retrieved metadata in memory | `false` | `TIO_SCHEMA_REGISTRY_CACHE` |
| `timeout` | Request timeout in seconds | `3` | `TIO_SCHEMA_REGISTRY_TIMEOUT` |
| `failfast` | Raise when the schema is not found | `true` | `TIO_SCHEMA_REGISTRY_FAILFAST` |

A value set under `registries.schema` in `tiozin.yaml` takes precedence over the environment variable. See the [Environment Variable Reference](../settings/env.md) for the complete list.

## Related

- [How to Use Schemas in Jobs](../how-to/schemas.md)
- [FileJobRegistry](file-job-registry.md)
- [Working with Registries](../extending/registry.md)
