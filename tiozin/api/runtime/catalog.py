from __future__ import annotations

from typing import TYPE_CHECKING

from tiozin.utils import slugify

from .dataset import Dataset

if TYPE_CHECKING:
    from .input import Input
    from .output import Output
    from .transform import Transform

    Step = Transform | Input | Output


class StepRecord:
    def __init__(self, step: Step) -> None:
        self.step: Step = step
        self.inputs: list[Dataset] = []
        self.output: Dataset | None = None


class RuntimeCatalog:
    """
    Tracks datasets produced and consumed by steps during a job execution.

    Born with the job context and shared across all child step contexts, so every
    step's inputs and outputs are visible to the job when emitting lineage events.
    """

    def __init__(self) -> None:
        self._steps: dict[str, StepRecord] = {}

    def __repr__(self) -> str:
        return f"RuntimeCatalog(steps={list(self._steps.keys())})"

    def register(
        self,
        step: Step,
        inputs: list[Dataset] = None,
        output: Dataset = None,
    ) -> StepRecord:
        record = self._steps.setdefault(step.slug, StepRecord(step))
        inputs = inputs or []

        if inputs:
            record.inputs.extend(Dataset.wrap(i) for i in inputs)

        if output is not None:
            dataset = Dataset.wrap(output)
            record.output = dataset if record.output is None else record.output.merge(dataset)

        return record

    def get(self, step: Step | str) -> StepRecord | None:
        key = slugify(step) if isinstance(step, str) else step.slug
        return self._steps.get(key)

    def get_all(self, steps: list[Step | str]) -> list[StepRecord]:
        return [record for step in steps if (record := self.get(step))]

    def get_input_datasets(self, steps: list[Step | str]) -> list[Dataset]:
        result = []
        for record in self.get_all(steps):
            result.extend(record.inputs)
        return result

    def get_output_datasets(self, steps: list[Step | str]) -> list[Dataset]:
        result = []
        for record in self.get_all(steps):
            if record.output is not None:
                result.append(record.output)
        return result
