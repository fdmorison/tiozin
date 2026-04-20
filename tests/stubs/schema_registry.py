from tiozin import Schema, SchemaRegistry


class SchemaRegistryStub(SchemaRegistry):
    def __init__(self):
        super().__init__(location="stub://schema")

    def get(self, subject: str, version: str = None) -> Schema:
        return None

    def register(self, subject: str, value: Schema) -> None:
        pass


class FailingSchemaRegistryStub(SchemaRegistry):
    def __init__(self):
        super().__init__(location="stub://schema")

    def get(self, subject: str, version: str = None) -> Schema:
        raise RuntimeError("schema registry unavailable")

    def register(self, subject: str, value: Schema) -> None:
        pass


class FileNotFoundSchemaRegistryStub(SchemaRegistry):
    def __init__(self):
        super().__init__(location="stub://schema")

    def get(self, subject: str, version: str = None) -> Schema:
        raise FileNotFoundError(subject)

    def register(self, subject: str, value: Schema) -> None:
        pass
