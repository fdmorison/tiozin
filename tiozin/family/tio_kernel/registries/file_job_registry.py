from tiozin.api import JobRegistry
from tiozin.api.metadata.job_manifest import JobManifest
from tiozin.exceptions import JobNotFoundError
from tiozin.utils.io import read_text, write_text


class FileJobRegistry(JobRegistry):
    """
    File-based job manifest storage.

    Reads and writes manifests from any path or URI supported by fsspec,
    including local paths, object storage (``s3://``, ``gs://``, ``az://``),
    and remote protocols (``http://``, ``https://``, ``ftp://``, ``sftp://``).

    Supported formats: YAML (.yaml, .yml) and JSON (.json).
    """

    def __init__(self, location: str = None, **options):
        super().__init__(location=location, **options)

    def get(self, identifier: str, version: str = None) -> JobManifest:
        """
        Retrieve a job manifest from the filesystem or object storage.

        Args:
            identifier: File path or URI with extension (.yaml, .yml, or .json).
                Accepts any scheme supported by fsspec: local paths,
                ``s3://``, ``gs://``, ``az://``, ``http://``, ``https://``, ``ftp://``, ``sftp://``.
            version: Not used in this implementation.

        Returns:
            Validated JobManifest instance.

        Raises:
            FileNotFoundError: If the file does not exist.
            ManifestError: If the file contains invalid YAML/JSON or validation fails.
        """
        try:
            self.info(f"Reading job manifest from {identifier}")
            content = read_text(identifier, **self.options)
            return JobManifest.from_yaml_or_json(content)
        except FileNotFoundError as e:
            raise JobNotFoundError("No job found at path `{name}`", name=identifier) from e

    def register(self, identifier: str, value: JobManifest) -> None:
        """
        Register a job manifest to the filesystem or object storage.

        Args:
            identifier: File path or URI with extension (.yaml, .yml, or .json).
            value: JobManifest instance to serialize and save.

        Raises:
            ValueError: If the file extension is not supported.
        """
        self.info(f"Writing job manifest to {identifier}")

        if identifier.endswith((".yaml", ".yml")):
            data = value.to_yaml()
        elif identifier.endswith(".json"):
            data = value.to_json()
        else:
            raise ValueError(f"Unsupported manifest format: {identifier}")

        write_text(identifier, data, **self.options)
