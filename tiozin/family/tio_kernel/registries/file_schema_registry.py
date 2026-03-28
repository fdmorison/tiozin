from tiozin.api import SchemaRegistry
from tiozin.api.metadata.schema.model import SchemaManifest
from tiozin.exceptions import SchemaNotFoundError
from tiozin.utils import join_path, write_text


class FileSchemaRegistry(SchemaRegistry):
    """
    File-based schema storage.

    Each file at `location` is a plain YAML representation of a schema.

    Supports local paths and remote URIs via fsspec:
    s3://, gs://, az://, http://, https://, ftp://, sftp://.

    Format: YAML (.yaml, .yml).

    Attributes:
        location: Root path or URI where schema files are stored.
    """

    def __init__(self, location: str = None, **options) -> None:
        super().__init__(location=location, **options)

    def get(self, identifier: str, version: str = None) -> SchemaManifest:
        try:
            path = join_path(self.location, f"{identifier}.yaml")
            self.info(f"Reading schema from {path}")
            return SchemaManifest.from_file(path, **self.options)
        except FileNotFoundError as e:
            raise SchemaNotFoundError(identifier) from e

    def register(self, identifier: str, value: SchemaManifest) -> None:
        path = join_path(self.location, f"{identifier}.yaml")
        self.info(f"Writing schema to {path}")
        write_text(path, value.to_yaml(), **self.options)
