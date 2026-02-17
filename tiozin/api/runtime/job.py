from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Generic, TypeVar

from tiozin.api import (
    Input,
    Output,
    Runner,
    Tiozin,
    Transform,
)
from tiozin.compose import JobProxy, tioproxy
from tiozin.exceptions import RequiredArgumentError

if TYPE_CHECKING:
    from tiozin.compose import JobBuilder

TData = TypeVar("TData")


@tioproxy(JobProxy)
class Job(Tiozin, Generic[TData]):
    """
    Defines a complete data pipeline.

    Composes Inputs, Transforms, Outputs, and a Runner into a declarative
    unit that describes how data should be read, processed, and written.
    Jobs represent the complete pipeline and produce data products following
    Data Mesh principles.

    Jobs interact with registries to look up or register metadata required
    for pipeline definition and execution, such as schemas, settings, or
    runtime configuration.

    Execution behavior emerges from the interaction between pipeline components,
    registries, and the Runner, enabling eager or lazy execution depending on
    the providers involved.

    Jobs are typically built from YAML, JSON, or Python manifests and executed
    by the TiozinApp.

    Attributes:
        name: Unique name for the job (not the execution ID).
        description: Short description of the pipeline.
        owner: Team that required the job.
        maintainer: Team that maintains this job.
        cost_center: Team that pays for this job.
        labels: Additional metadata as key-value pairs.
        org: Organization producing the data product.
        region: Business region of the domain team.
        domain: Domain team following the Data Mesh concept.
        product: Data product being produced.
        model: Data model being produced (e.g., table, topic, collection).
        layer: Data layer this job represents (e.g., raw, trusted, refined).
        runner: Runtime environment where the job runs.
        inputs: Sources that provide data to the job.
        transforms: Steps that modify the data.
        outputs: Destinations where data is written.
    """

    def __init__(
        self,
        name: str = None,
        description: str = None,
        owner: str = None,
        maintainer: str = None,
        cost_center: str = None,
        labels: dict[str, str] = None,
        org: str = None,
        region: str = None,
        domain: str = None,
        layer: str = None,
        product: str = None,
        model: str = None,
        runner: Runner = None,
        inputs: list[Input] = None,
        transforms: list[Transform] = None,
        outputs: list[Output] = None,
        **options,
    ) -> None:
        super().__init__(name, description, **options)

        RequiredArgumentError.raise_if_missing(
            name=name,
            runner=runner,
            inputs=inputs,
            org=org,
            region=region,
            domain=domain,
            layer=layer,
            product=product,
            model=model,
        )

        self.maintainer = maintainer
        self.cost_center = cost_center
        self.owner = owner
        self.labels = labels or {}

        self.org = org
        self.region = region
        self.domain = domain
        self.layer = layer
        self.product = product
        self.model = model

        self.runner = runner
        self.inputs = inputs or []
        self.transforms = transforms or []
        self.outputs = outputs or []
        self.steps = self.inputs + self.transforms + self.outputs

        tiozins: list[Tiozin] = [self, self.runner, *self.steps]
        self.tios: frozenset[str] = frozenset(t.tiozin_provider for t in tiozins)

    @staticmethod
    def builder() -> JobBuilder:
        from tiozin.compose import JobBuilder

        return JobBuilder()

    def setup(self) -> None:
        return None

    @abstractmethod
    def submit(self) -> TData:
        pass

    def teardown(self) -> None:
        return None
