from ...model.registry import Registry


class LineageRegistry(Registry):
    """
    Tracks data lineage following the Open Lineage standard (https://openlineage.io/).

    Storage-agnostic implementation for lineage events and relationships.
    Used internally by Tiozin during pipeline execution.
    """

    def __init__(self) -> None:
        super().__init__()
