from ...model.registry import Registry


class JobRegistry(Registry):
    """
    Retrieves and stores job manifests.

    Storage-agnostic contract for job backends (like DynamoDB, Consul, or Postgres).
    Used internally by Tiozin to resolve jobs from commands like `tiozin run job.yaml`.
    """

    def __init__(self) -> None:
        super().__init__()
