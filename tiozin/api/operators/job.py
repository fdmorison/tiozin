from typing import TYPE_CHECKING, Generic, TypeVar, Unpack

from tiozin.api import Input, Operator, OperatorKwargs, Output, Plugable, Runner, Transform
from tiozin.exceptions import InvalidInputError

if TYPE_CHECKING:
    from tiozin.assembly.builder import JobBuilder

TData = TypeVar("TData")


class Job(Plugable, Operator, Generic[TData]):
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
        name: str,
        description: str | None,
        *,
        runner: Runner,
        inputs: list[Input],
        transforms: list[Transform] | None,
        outputs: list[Output] | None,
        owner: str | None = None,
        maintainer: str | None = None,
        cost_center: str | None = None,
        labels: dict[str, str] | None = None,
        **options: Unpack[OperatorKwargs],
    ) -> None:
        super().__init__(name, description, **options)

        if not runner:
            raise InvalidInputError("Tiozin jobs should have a runner")

        if not inputs:
            raise InvalidInputError("Tiozin jobs should have at least one input step")

        self.maintainer = maintainer
        self.cost_center = cost_center
        self.owner = owner
        self.labels = labels or []
        self.runner = runner
        self.inputs = inputs
        self.transforms = transforms or []
        self.outputs = outputs or []

    @staticmethod
    def builder() -> "JobBuilder":
        from tiozin.assembly.builder import JobBuilder

        return JobBuilder()
