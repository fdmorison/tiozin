from typing import TypedDict


class Taxonomy(TypedDict, total=False):
    org: str
    region: str
    domain: str
    layer: str
    product: str
    model: str
