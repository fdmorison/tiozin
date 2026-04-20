from tiozin import JobManifest, JobRegistry
from tiozin.exceptions import JobNotFoundError
from tiozin.utils import join_path


class FileJobRegistry(JobRegistry):
    """
    File-based job manifest storage.

    Resolves job manifest locations and delegates reading and writing to
    the model layer.

    Supports local paths and remote URIs via fsspec, including:
    s3://, gs://, az://, http://, https://, ftp://, and sftp://.

    Supported formats: YAML (.yaml, .yml) and JSON (.json).

    Attributes:
        location: Root path or URI where job manifests are stored.
    """

    def __init__(self, location: str = None, **options):
        super().__init__(location=location, **options)

    def get(self, identifier: str) -> JobManifest:
        try:
            path = join_path(self.location, identifier)
            self.info(f"Reading job from {path}")
            return JobManifest.from_file(path, **self.options)
        except FileNotFoundError as e:
            raise JobNotFoundError("No job found at path `{name}`", name=path) from e

    def register(self, identifier: str, value: JobManifest) -> None:
        path = join_path(self.location, identifier)
        self.info(f"Writing job to {path}")
        value.to_file(path, **self.options)
