from .. import JobManifest, Registry


class JobRegistry(Registry[JobManifest]):
    """
    Retrieves and stores job manifests.

    Storage-agnostic contract for job backends (like DynamoDB, Consul, or Postgres).
    Used internally by Tiozin to resolve jobs from commands like `tiozin run job.yaml`.
    """
