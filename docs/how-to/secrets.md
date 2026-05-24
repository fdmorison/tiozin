# How to Use Secrets in Jobs

Keep credentials out of your job files by reading them from a secret registry at runtime. Tiozin masks secret values in all logs and reprs, so they never appear in output even when embedded in connection strings.

## The basics

`EnvSecretRegistry` is the default secret registry. It reads secrets from environment variables and works out of the box. You do not need to declare it in `tiozin.yaml`. If you want to be explicit:

```yaml
# tiozin.yaml
registries:
  secret:
    kind: tio_kernel:EnvSecretRegistry
```

Set the secret in your environment:

```bash
export DB_PASSWORD=supersecret
```

Reference it in any job step field with `{{ SECRET.name }}`:

```yaml
runner:
  kind: DuckdbRunner
  url: "postgres://user:{{ SECRET.DB_PASSWORD }}@host:5432/dbname"
  # logged as: postgres://user:***@host:5432/dbname
```

Two syntaxes are supported:

- `{{ SECRET.NAME }}`: for simple identifiers like environment variable names
- `{{ SECRET["path/name"] }}`: for identifiers that contain slashes, such as Vault paths

Both look up the identifier in the registry at job startup, wrap the value in a `Secret`, and substitute it into the string. The surrounding string also becomes a `Secret`, so the full connection URL is masked in logs.

## Use secrets in plugin code

Access the secret registry from any step via `self.context.registries.secret`:

```python
from tiozin import Input


class PostgresInput(Input[list]):
    def read(self) -> list:
        password = self.context.registries.secret.get("DB_PASSWORD")
        conn = connect(host="db.internal", password=password)
        return conn.execute(self.query).fetchall()
```

By default (`failfast: false`), `get()` returns `None` when the secret is not found. With `failfast: true`, it raises `SecretNotFoundError`. When the secret is optional, check the return value:

```python
api_token = self.context.registries.secret.get("API_TOKEN")
if api_token:
    headers["Authorization"] = f"Bearer {api_token}"
```

## How masking works

`Secret` is a `str` subtype. It is accepted anywhere a plain string is expected: Jinja templates, Pydantic models, connection libraries. No explicit conversion needed.

When you concatenate a `Secret` with a plain string, the result is a new `Secret` where only the sensitive segment is masked:

```python
secret = Secret("mypassword")
url = "postgres://host/db?password=" + secret

str(url)   # → "postgres://host/db?password=mypassword"
repr(url)  # → "postgres://host/db?password=***"
```

Tiozin also registers each retrieved secret with the log sanitizer, so even if a secret value leaks into a log line through a third-party library, it is replaced with `***`.

## Local development with a .env file

Create a `.env` file at the project root:

```bash
DB_PASSWORD=local_dev_password
API_TOKEN=dev_token_abc123
```

Tiozin loads `.env` files automatically at startup. Do not commit `.env` to version control.

## Implement a custom secret registry

For secrets stored in a vault or cloud secret manager, extend `SecretRegistry`:

```python
from tiozin import SecretRegistry, Secret


class VaultSecretRegistry(SecretRegistry):
    def get(self, identifier: str) -> Secret | None:
        value = vault_client.read_secret(identifier)
        if value is None:
            return None
        return Secret(value)

    def register(self, identifier: str, value: Secret) -> None:
        vault_client.write_secret(identifier, str(value))
```

To use it, the registry must belong to a registered Tiozin Family. See [Creating a Provider Family](../extending/families.md).

## All parameters

`EnvSecretRegistry` has no required parameters beyond the common registry fields:

| Property | Description | Example output |
|---|---|---|
| `kind` | Plugin class name | `tio_kernel:EnvSecretRegistry` |
| `readonly` | Reject write operations | `false` |
| `cache` | Cache retrieved secrets in memory | `false` |
| `failfast` | When `true`, raises when the secret is not found; when `false`, returns `None` | `false` |
| `name` | Display name for this registry instance | |
| `description` | Human-readable description | |
