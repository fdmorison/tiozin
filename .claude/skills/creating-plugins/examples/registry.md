# Registry

Registries are metadata services (secrets, settings, schemas, jobs, metrics, lineage). They start before the first job runs and stop at shutdown.

**Base classes:** `SecretRegistry`, `SettingRegistry`, `SchemaRegistry`, `JobRegistry`, `LineageRegistry`

Required methods vary by base class:

| Base | Must implement |
|------|----------------|
| `SecretRegistry` | `get(identifier: str) -> Secret`, `register(identifier: str, value: Secret)` |
| `SettingRegistry` | `get() -> SettingsManifest` |
| `SchemaRegistry` | `get(subject: str, version: str = None) -> Schema`, `register(subject: str, value: Schema)` |
| `JobRegistry` | `get(identifier: str) -> JobManifest`, `register(identifier: str, value: JobManifest)` |
| `LineageRegistry` | `emit(event: LineageEvent)` |

**SecretRegistry**

```python
from tiozin import Secret, SecretRegistry
from tiozin.exceptions import SecretNotFoundError


class AcmeSecretRegistry(SecretRegistry):
    def __init__(self, location: str = None, **options) -> None:
        super().__init__(location=location, **options)
        self._client = None

    def setup(self) -> None:
        self._client = AcmeSecretClient(endpoint=self.location)

    def get(self, identifier: str) -> Secret:
        try:
            return Secret(self._client.fetch(identifier))
        except AcmeSecretNotFoundError:
            raise SecretNotFoundError(identifier)

    def register(self, identifier: str, value: Secret) -> None:
        self._client.store(identifier, str(value))
```

**SettingRegistry**

```python
from tiozin import SettingsManifest, SettingRegistry
from tiozin.exceptions import SettingsNotFoundError


class AcmeSettingRegistry(SettingRegistry):
    def __init__(self, location: str = None, **options) -> None:
        super().__init__(location=location, **options)
        self._client = None

    def setup(self) -> None:
        self._client = AcmeSettingClient(endpoint=self.location)

    def get(self) -> SettingsManifest:
        data = self._client.fetch_all()
        if data is None:
            raise SettingsNotFoundError()
        return SettingsManifest(**data)
```

**SchemaRegistry**

```python
from tiozin import Schema, SchemaRegistry
from tiozin.exceptions import SchemaNotFoundError


class AcmeSchemaRegistry(SchemaRegistry):
    def __init__(self, location: str = None, **options) -> None:
        super().__init__(location=location, **options)
        self._client = None

    def setup(self) -> None:
        self._client = AcmeSchemaClient(endpoint=self.location)

    def get(self, subject: str, version: str = None) -> Schema:
        try:
            return self._client.fetch(subject, version or self.default_version)
        except AcmeSchemaNotFoundError:
            raise SchemaNotFoundError(subject)

    def register(self, subject: str, value: Schema) -> None:
        self._client.store(subject, value)
```

**JobRegistry**

```python
from tiozin import JobManifest, JobRegistry
from tiozin.exceptions import JobNotFoundError


class AcmeJobRegistry(JobRegistry):
    def __init__(self, location: str = None, **options) -> None:
        super().__init__(location=location, **options)
        self._client = None

    def setup(self) -> None:
        self._client = AcmeJobClient(endpoint=self.location)

    def get(self, identifier: str) -> JobManifest:
        try:
            return self._client.fetch(identifier)
        except AcmeJobNotFoundError:
            raise JobNotFoundError(identifier)

    def register(self, identifier: str, value: JobManifest) -> None:
        self._client.store(identifier, value)
```

**LineageRegistry**

```python
from tiozin import LineageEvent, LineageRegistry


class AcmeLineageRegistry(LineageRegistry):
    def __init__(self, location: str = None, **options) -> None:
        super().__init__(location=location, **options)
        self._client = None

    def setup(self) -> None:
        self._client = AcmeLineageClient(endpoint=self.location)

    def emit(self, event: LineageEvent) -> None:
        self._client.send(event)
```

**MetricRegistry** and **BatchRegistry** are reserved for future use and have no defined contract yet. Reject any request to implement these registry types.

When `get()` raises a not-found error, do not implement `failfast` logic. The Tiozin core handles that automatically.
