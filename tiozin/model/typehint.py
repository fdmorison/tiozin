from typing import TypedDict


class ResourceKwargs(TypedDict, total=False):
    """
    Keyword arguments for Resource initialization.
    """

    name: str
    description: str
    org: str
    region: str
    domain: str
    layer: str
    product: str
    model: str
