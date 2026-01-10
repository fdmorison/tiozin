from pathlib import Path

from tiozin.api import JobRegistry
from tiozin.api.metadata.job_manifest import JobManifest


class FileJobRegistry(JobRegistry):
    """
    File-based job manifest storage.

    Reads and writes manifests from filesystem, GCS, or S3.
    Default JobRegistry implementation. Supports YAML and JSON formats.
    """

    def get(self, name: str, version: str = None) -> JobManifest:
        """
        Retrieve a job manifest from the filesystem.

        Args:
            name: File path to the manifest file. Supports .yaml, .yml, or .json extensions.
            version: Not used in this implementation (filesystem is version-agnostic).

        Returns:
            Validated JobManifest instance loaded from the file.

        Raises:
            FileNotFoundError: If the file does not exist.
            ManifestError: If the file contains invalid YAML/JSON or validation fails.
        """
        data = Path(name).read_text(encoding="utf-8")
        return JobManifest.from_yaml_or_json(data)

    def register(self, name: str, value: JobManifest) -> None:
        """
        Register a job manifest to the filesystem.

        Args:
            name: File path where the manifest will be saved.
                  Must include extension (.yaml, .yml, or .json) to determine format.
            value: JobManifest instance to serialize and save.

        Raises:
            ValueError: If the file extension is not supported.
        """
        path = Path(name)

        if path.suffix in {".yaml", ".yml"}:
            data = value.to_yaml()
        elif path.suffix == ".json":
            data = value.to_json()
        else:
            raise ValueError(f"Unsupported manifest format: {path.suffix}")

        path.write_text(data, encoding="utf-8")
