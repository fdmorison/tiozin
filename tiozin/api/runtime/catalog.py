from __future__ import annotations

from typing import TYPE_CHECKING

from tiozin.utils import slugify

from .dataset import Dataset

if TYPE_CHECKING:
    from .input import Input
    from .job import Job
    from .output import Output
    from .transform import Transform

    JobOrStep = Job | Transform | Input | Output
    JobOrStepOrStr = JobOrStep | str


class RunRecord:
    def __init__(self, slug: str) -> None:
        self.slug: str = slug
        self.inputs: list[Dataset] = []
        self.output: Dataset | None = None


class RunCatalog:
    """
    Tracks datasets produced and consumed by runtimes during a job execution.

    Born with the job context and shared across all child step contexts, so every
    step's inputs and outputs are visible to the job when emitting lineage events.
    """

    def __init__(self) -> None:
        self._records: dict[str, RunRecord] = {}

    def __repr__(self) -> str:
        return f"RunCatalog(records={list(self._records.keys())})"

    def register(
        self,
        runtime: JobOrStep,
        inputs: list[Dataset] = None,
        output: Dataset = None,
    ) -> RunRecord:
        record = self._records.setdefault(runtime.slug, RunRecord(runtime.slug))
        inputs = inputs or []

        if inputs:
            record.inputs.extend(Dataset.wrap(i) for i in inputs)

        if output is not None:
            dataset = Dataset.wrap(output)
            record.output = dataset if record.output is None else record.output.merge(dataset)

        return record

    def get(self, runtime: JobOrStepOrStr) -> RunRecord | None:
        key = slugify(runtime) if isinstance(runtime, str) else runtime.slug
        return self._records.get(key)

    def get_records(self, runtimes: JobOrStepOrStr | list[JobOrStepOrStr]) -> list[RunRecord]:
        runtimes = runtimes if isinstance(runtimes, list) else [runtimes]
        return [record for runtime in runtimes if (record := self.get(runtime))]

    def get_inputs(self, runtimes: JobOrStepOrStr | list[JobOrStepOrStr]) -> list[Dataset]:
        result = []
        for record in self.get_records(runtimes):
            result.extend(record.inputs)
        return result

    def get_outputs(self, runtimes: JobOrStepOrStr | list[JobOrStepOrStr]) -> list[Dataset]:
        result = []
        for record in self.get_records(runtimes):
            if record.output is not None:
                result.append(record.output)
        return result
