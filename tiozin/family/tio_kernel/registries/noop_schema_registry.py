from tiozin.api import Schema, SchemaRegistry


class NoOpSchemaRegistry(SchemaRegistry):
    """
    No-op schema registry.

    Does nothing. Returns None for all operations.
    Useful for testing or when schema validation is disabled.
    """

    def __init__(self, location: str = None, **options) -> None:
        super().__init__(location=location or self.tiozin_uri, **options)

    def get(self, subject: str, version: str = None) -> Schema:
        return None

    def register(self, subject: str, value: Schema) -> None:
        return None
