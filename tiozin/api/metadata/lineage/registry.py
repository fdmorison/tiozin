from tiozin.api import Registry


class LineageRegistry(Registry[object]):
    """
    Tracks data lineage following the Open Lineage standard (https://openlineage.io/).

    Storage-agnostic implementation for lineage events and relationships.
    Used internally by Tiozin during pipeline execution.
    """
