from abc import abstractmethod

from ..registry import Registry
from .model import JobManifest


class JobRegistry(Registry[JobManifest]):
    """
    Retrieves and stores job manifests.

    Storage-agnostic contract for job backends (like DynamoDB, Consul, or Postgres).
    Used internally by Tiozin to resolve jobs from commands like `tiozin run job.yaml`.
    """

    @abstractmethod
    def get(self, identifier: str) -> JobManifest:
        """
        Retrieve a job manifest by identifier.

        Raises:
            NotFoundException: When not found and `failfast=True`.
        """

    @abstractmethod
    def register(self, identifier: str, value: JobManifest) -> None:
        """Register a job manifest in the registry."""
