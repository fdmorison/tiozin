import fsspec

from tiozin.api import JobRegistry
from tiozin.api.metadata.job_manifest import JobManifest
from tiozin.exceptions import JobNotFoundError


class FileJobRegistry(JobRegistry):
    """
    File-based job manifest storage.

    Reads and writes manifests from filesystem or object storage
    via fsspec (e.g. local paths, s3://, gs://, az://).

    Supported formats: YAML (.yaml, .yml) and JSON (.json).
    """

    def __init__(self, **options):
        super().__init__(**options)

    def get(self, identifier: str, version: str = None) -> JobManifest:
        """
        Retrieve a job manifest from the filesystem or object storage.

        Args:
            identifier: File path or URI with extension (.yaml, .yml, or .json).
            version: Not used in this implementation.

        Returns:
            Validated JobManifest instance.

        Raises:
            FileNotFoundError: If the file does not exist.
            ManifestError: If the file contains invalid YAML/JSON or validation fails.
        """
        try:
            self.info(f"Reading job manifest from {identifier}")
            with fsspec.open(
                identifier,
                mode="r",
                **self.options,
            ) as f:
                return JobManifest.from_yaml_or_json(f.read())
        except FileNotFoundError as e:
            raise JobNotFoundError(identifier) from e

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

        with fsspec.open(
            identifier,
            mode="w",
            **self.options,
        ) as f:
            f.write(data)
