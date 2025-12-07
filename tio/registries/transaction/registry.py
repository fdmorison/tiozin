from ..registry import MetadataRegistry


class TransactionRegistry(MetadataRegistry):
    """
    Registry that tracks transactions and their state in Tio, creating and using
    a transaction log or commit log.

    Supports any storage backend for transaction metadata (e.g., databases,
    key/value stores), while keeping Tio agnostic to the storage details. Records
    pending, running, committed, and failed transactions, enabling consistent
    tracking and auditing across executions.

    Tio automatically updates transaction states during pipeline execution, but the
    TransactionRegistry is also available in the Context for custom inspection or
    manipulation by Transforms, Inputs, and Outputs.
    """

    def __init__(self) -> None:
        super().__init__()
