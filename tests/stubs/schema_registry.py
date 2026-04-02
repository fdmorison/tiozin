from tests import env
from tiozin.api.metadata.schema.registry import SchemaRegistry


class SchemaRegistryStub(SchemaRegistry):
    def __init__(self):
        super().__init__(
            location="stub://schema",
            subject_template=env.TIO_SCHEMA_REGISTRY_SUBJECT_TEMPLATE,
            default_version=env.TIO_SCHEMA_REGISTRY_DEFAULT_VERSION,
        )

    def get(self, identifier: str = None, version: str = None) -> None:
        return None

    def register(self, identifier: str, value: object) -> None:
        pass


class FailingSchemaRegistryStub(SchemaRegistry):
    def __init__(self):
        super().__init__(location="stub://schema")

    def get(self, identifier: str = None, version: str = None) -> None:
        raise RuntimeError("schema registry unavailable")

    def register(self, identifier: str, value: object) -> None:
        pass


class FileNotFoundSchemaRegistryStub(SchemaRegistry):
    def __init__(self):
        super().__init__(location="stub://schema")

    def get(self, identifier: str = None, version: str = None) -> None:
        raise FileNotFoundError(identifier)

    def register(self, identifier: str, value: object) -> None:
        pass
