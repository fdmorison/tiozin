# AwsParameterStoreSecretRegistry

Reads and writes secrets backed by [AWS Systems Manager Parameter Store](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html).

```yaml
registries:
  secret:
    kind: tio_kernel:AwsParameterStoreSecretRegistry
    region_name: us-east-1
```

Each secret identifier maps directly to a Parameter Store name. The retrieved value is wrapped in a `Secret` object that masks itself in logs and reprs, keeping credentials out of output even when injected into connection strings or other values.

## Parameters

| Property | Description | Default |
|---|---|---|
| `location` | Endpoint URL for the SSM client (for example, `http://localhost:4566` for [LocalStack](https://docs.localstack.cloud/)). When unset, boto3 uses the default AWS endpoint. | |
| `region_name` | AWS region name (for example, `us-east-1`). When unset, [boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html) resolves the region from the environment or AWS config. | |

Credentials are resolved through the standard [AWS credential chain](https://docs.aws.amazon.com/sdkref/latest/guide/standardized-credentials.html) (environment variables, `~/.aws/credentials`, IAM role, and so on).

## How it works

When a job or plugin calls `secret.get("/prod/db/password")`, the registry calls `ssm.get_parameter` with `WithDecryption=True` and returns a `Secret`. If the parameter does not exist, it raises `SecretNotFoundError`.

```python
from tiozin import Input


class PostgresInput(Input[list]):
    def read(self) -> list:
        password = self.context.registries.secret.get("/prod/db/password")
        conn = connect(host="db.internal", password=password)
        return conn.execute(self.query).fetchall()
```

Registering a secret calls `ssm.put_parameter` with `Type="SecureString"` and `Overwrite=True`, replacing the existing value if the parameter already exists.

Secrets injected into job YAML via `{{ SECRET.name }}` go through the same registry. The masked repr ensures they do not appear in logs:

```yaml
runner:
  kind: SparkRunner
  url: jdbc:postgresql://host:5432/db?password={{ SECRET["/prod/db/password"] }}
  # logged as: jdbc:postgresql://host:5432/db?password=***
```

## When to use it

Use `AwsParameterStoreSecretRegistry` when secrets live in AWS Parameter Store and the runtime has access to AWS credentials: workloads running on EC2, ECS, EKS, or Lambda with an IAM role, or local development against [LocalStack](https://docs.localstack.cloud/).

For secrets stored in environment variables, use [EnvSecretRegistry](env-secret-registry.md). For other vaults or secret managers (HashiCorp Vault, AWS Secrets Manager, GCP Secret Manager), implement a custom `SecretRegistry`. See [Creating Pluggable Tiozins](../extending/tiozins.md).
