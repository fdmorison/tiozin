from tiozin.api import JobRegistry
from tiozin.api.metadata.job_manifest import JobManifest
from tiozin.exceptions import JobNotFoundError
from tiozin.utils import join_path, read_text, write_text


class FileJobRegistry(JobRegistry):
    """
    File-based job manifest storage.

    Reads and writes manifests from any path or URI supported by fsspec,
    including local paths, object storage (``s3://``, ``gs://``, ``az://``),
    and remote protocols (``http://``, ``https://``, ``ftp://``, ``sftp://``).

    Supported formats: YAML (.yaml, .yml) and JSON (.json).

    Attributes:
        location: Root path or URI where job manifests are stored (e.g. a local folder,
            an S3 prefix, or an HTTP base URL).
    """

    def __init__(self, location: str = None, **options):
        super().__init__(location=location, **options)

    def get(self, identifier: str, version: str = None) -> JobManifest:
        """
        Retrieve a job manifest from any fsspec-supported location.

        Args:
            identifier: File name, relative path, or absolute URI (.yaml, .yml, or .json).
            version: Not used in this implementation.

        Returns:
            Validated JobManifest instance.

        Raises:
            JobNotFoundError: If the file does not exist.
            ManifestError: If the file contains invalid YAML/JSON or validation fails.
        """
        try:
            path = join_path(self.location, identifier)
            self.info(f"Reading job manifest from {path}")
            content = read_text(path, **self.options)
            return JobManifest.from_yaml_or_json(content)
        except FileNotFoundError as e:
            raise JobNotFoundError("No job found at path `{name}`", name=path) from e

    def register(self, identifier: str, value: JobManifest) -> None:
        """
        Register a job manifest to any fsspec-supported location.

        Args:
            identifier: File name, relative path, or absolute URI (.yaml, .yml, or .json).
            value: JobManifest instance to serialize and save.

        Raises:
            ValueError: If the file extension is not supported.
        """
        path = join_path(self.location, identifier)
        self.info(f"Writing job manifest to {path}")

        if path.endswith((".yaml", ".yml")):
            data = value.to_yaml()
        elif path.endswith(".json"):
            data = value.to_json()
        else:
            raise ValueError(f"Unsupported manifest format: {path}")

        write_text(path, data, **self.options)
