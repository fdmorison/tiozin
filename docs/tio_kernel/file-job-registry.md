# FileJobRegistry

Loads and saves job manifests from any path or URI supported by fsspec.

```yaml
registries:
  job:
    kind: tio_kernel:FileJobRegistry
    location: jobs/
```

## Parameters

| Property | Description | Default |
|---|---|---|
| `location` | Root path or URI where job manifests are stored | |
| `**options` | fsspec storage options (credentials, region, etc.) | |

## location

When `location` is set, relative identifiers are resolved against it. Set it to a local folder, an S3 prefix, or an HTTP base URL and load jobs by name instead of full path:

```bash
tiozin run my_pipeline.yaml  # loads jobs/my_pipeline.yaml
```

Absolute paths and URIs passed directly to `tiozin run` are used as-is regardless of `location`.

## Supported URI schemes

| Scheme | Example |
|---|---|
| Local path | `jobs/` |
| Amazon S3 | `s3://my-bucket/jobs/` |
| Google Cloud Storage | `gs://my-bucket/jobs/` |
| Azure Blob Storage | `az://my-container/jobs/` |
| HTTP / HTTPS | `https://example.com/jobs/` |
| FTP | `ftp://host/jobs/` |
| SFTP | `sftp://host/jobs/` |

## Storage options

Use `**options` to pass credentials and configuration to fsspec. The accepted keys depend on the storage backend.

```yaml
registries:
  job:
    kind: tio_kernel:FileJobRegistry
    location: s3://my-bucket/jobs/
    key: AKIAIOSFODNN7EXAMPLE
    secret: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
    client_kwargs:
      region_name: us-east-1
```

For the full list of options per backend, see the [fsspec documentation](https://filesystem-spec.readthedocs.io/en/latest/).
