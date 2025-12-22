from ..registry import Registry


class TransactionRegistry(Registry):
    """
    Tracks transaction states and commit logs.

    Storage-agnostic contract for transaction backends (like databases or key/value stores).
    Records pending, running, committed, and failed states for consistent tracking and auditing.
    Available in Context for custom inspection in Transforms, Inputs, and Outputs.
    """

    def __init__(self) -> None:
        super().__init__()
