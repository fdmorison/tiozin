from abc import ABC
import logging
from typing import Any

from uuid_utils import uuid7


class Resource(ABC):
    """
    Base class for all Tiozin ETL resources.

    Resources represent ETL components (Jobs, Inputs, Transforms, Outputs, Runners)
    with business metadata following Data Mesh principles.

    Attributes:
        kind: Resource class name.
        name: Resource name.
        run_id: Unique execution identifier (UUID7).
        logger: Logger scoped to resource name.
        org: Organization.
        region: Geographic region.
        domain: Business domain.
        layer: Data layer (raw, staging, refined, etc).
        product: Data product.
        model: Data model.
        description: Optional description.

    Example:
        class MyResource(Resource):
            pass

        resource = MyResource(
            name="etl_job",
            org="acme",
            region="us-east",
            domain="sales",
            layer="refined",
            product="analytics",
            model="revenue",
            description="Revenue ETL"
        )

        resource.logger.info(f"Resource URI: {resource.uri}")
    """

    def __init__(
        self,
        name: str,
        org: str,
        region: str,
        domain: str,
        layer: str,
        product: str,
        model: str,
        description: str = None,
    ) -> None:
        self.kind = type(self).__name__
        self.name = name
        self.run_id = str(uuid7())
        self.logger = logging.getLogger(self.name)
        self.org = org
        self.region = region
        self.domain = domain
        self.layer = layer
        self.product = product
        self.model = model
        self.description = description

    @property
    def uri(self) -> str:
        return f"{self.kind}:{self.name}"

    @property
    def execution_uri(self) -> str:
        return f"{self.uri}:{self.run_id}"

    def to_dict(self) -> dict[str, Any]:
        return vars(self).copy()

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f'"{self.name}"'

    def __hash__(self) -> int:
        return hash(self.run_id)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return self.run_id == other.run_id
