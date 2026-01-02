from abc import abstractmethod
from typing import TYPE_CHECKING, Generic, TypeVar, Unpack

from tiozin.api import (
    Context,
    Input,
    Output,
    Plugable,
    Processor,
    ProcessorKwargs,
    Runner,
    Transform,
)
from tiozin.exceptions import RequiredArgumentError

if TYPE_CHECKING:
    from tiozin.assembly.job_builder import JobBuilder

TData = TypeVar("TData")


class Job(Plugable, Processor, Generic[TData]):
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
        owner: str = None,
        maintainer: str = None,
        cost_center: str = None,
        labels: dict[str, str] = None,
        runner: Runner = None,
        inputs: list[Input] = None,
        transforms: list[Transform] = None,
        outputs: list[Output] = None,
        **options: Unpack[ProcessorKwargs],
    ) -> None:
        super().__init__(**options)

        RequiredArgumentError.raise_if_missing(
            runner=runner,
            inputs=inputs,
        ).raise_if_missing(
            org=self.org,
            region=self.region,
            domain=self.domain,
            layer=self.layer,
            product=self.product,
            model=self.model,
        )
        self.maintainer = maintainer
        self.cost_center = cost_center
        self.owner = owner
        self.labels = labels or {}
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

    def execute(self, context: Context) -> TData:
        """Template method that delegates to run()."""
        return self.run(context)
