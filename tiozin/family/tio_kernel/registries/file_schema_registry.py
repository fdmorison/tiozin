from open_data_contract_standard.model import SchemaObject

from tiozin.api import SchemaRegistry
from tiozin.api.metadata.schema.model import SchemaManifest
from tiozin.exceptions import SchemaNotFoundError
from tiozin.utils import join_path, read_yaml, write_yaml


class FileSchemaRegistry(SchemaRegistry):
    """
    File-based schema manifest storage.

    Reads and writes schemas from any path or URI supported by fsspec,
    including local paths, object storage (``s3://``, ``gs://``, ``az://``),
    and remote protocols (``http://``, ``https://``, ``ftp://``, ``sftp://``).

    Supported format: YAML.

    Attributes:
        location: Root path or URI where schema manifests are stored (e.g. a local folder,
            an S3 prefix, or an HTTP base URL).
    """

    def __init__(self, location: str = None, **options):
        super().__init__(location=location, **options)

    def get(self, identifier: str, version: str = None) -> SchemaManifest:
        """
        Retrieve a schema manifest from any fsspec-supported location.

        Args:
            identifier: File name, relative path, or absolute URI (.yaml or .yml).
            version: Not used in this implementation.

        Returns:
            Validated SchemaManifest instance.

        Raises:
            SchemaNotFoundError: If the file does not exist.
        """
        try:
            path = join_path(self.location, identifier)
            self.info(f"Reading schema manifest from {path}")
            data = read_yaml(path, **self.options)
            spec = SchemaObject(**data)
            return SchemaManifest(subject=spec.name, schema=spec)
        except FileNotFoundError as e:
            raise SchemaNotFoundError("No schema found at path `{name}`", name=path) from e

    def register(self, identifier: str, value: SchemaManifest) -> None:
        """
        Register a schema manifest to any fsspec-supported location.

        Args:
            identifier: File name, relative path, or absolute URI (.yaml or .yml).
            value: SchemaManifest instance to serialize and save.
        """
        path = join_path(self.location, identifier)
        self.info(f"Writing schema manifest to {path}")
        write_yaml(path, value.schema.model_dump(), **self.options)
