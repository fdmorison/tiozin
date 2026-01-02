from abc import abstractmethod
from typing import TYPE_CHECKING, Generic, TypeVar

from tiozin.api import (
    Context,
    Executable,
    Input,
    Output,
    Plugable,
    Resource,
    Runner,
    Transform,
)
from tiozin.exceptions import RequiredArgumentError

if TYPE_CHECKING:
    from tiozin.assembly.job_builder import JobBuilder

T = TypeVar("TData")


class Job(Plugable, Executable, Resource, Generic[T]):
    """
    A Job represents a complete pipeline definition.

    It composes Inputs, Transforms, Outputs, and a Runner into a single,
    declarative unit that describes how data should be read, processed, and
    written, without prescribing a specific execution model.

    A Job may also interact with registries to look up or register metadata
    required for pipeline definition and execution, such as schemas, settings,
    or runtime configuration.

    The execution behavior of a Job emerges from the interaction between its
    operators, registries, and the Runner, allowing eager or lazy execution
    depending on the providers involved.

    Jobs are typically built from YAML, JSON, or Python manifests and executed
    by the TiozinApp.
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

    @staticmethod
    def builder() -> "JobBuilder":
        from tiozin.assembly.job_builder import JobBuilder

        return JobBuilder()

    @abstractmethod
    def run(self, context: Context) -> None:
        pass

    def execute(self, context: Context) -> T:
        """Template method that delegates to run()."""
        return self.run(context)

    def setup(self) -> None:
        return None

    def teardown(self) -> None:
        return None
