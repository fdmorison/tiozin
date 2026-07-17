from __future__ import annotations

from typing import TYPE_CHECKING, TypeAlias

from tiozin.utils import slugify

from .dataset import Dataset

if TYPE_CHECKING:
    from .. import Batch, Input, Job, Output, Transform

    JobOrStepOrSlug: TypeAlias = Job | Transform | Input | Output | str


class RuntimeRecord:
    def __init__(self, key: str) -> None:
        self.key: str = key
        self.inputs: list[Dataset] = []
        self.output: Dataset | None = None
        self.backlog: list[Batch] = []


class RuntimeCatalog:
    """
    Registers runtime objects for jobs and steps.

    Each job or step has a record keyed by its slug. Records store objects such
    as input datasets, output datasets, and pending batches for later access
    during the execution.
    """

    def __init__(self) -> None:
        self._records: dict[str, RuntimeRecord] = {}

    def __repr__(self) -> str:
        return f"RuntimeCatalog(records={list(self._records.keys())})"

    def register(
        self,
        object: JobOrStepOrSlug,
        inputs: list[Dataset] = None,
        output: Dataset = None,
        backlog: list[Batch] = None,
    ) -> RuntimeRecord:
        key = slugify(object) if isinstance(object, str) else object.slug
        record = self._records.setdefault(key, RuntimeRecord(key))
        inputs = inputs or []

        if inputs:
            record.inputs.extend(Dataset.wrap(i) for i in inputs)

        if output is not None:
            dataset = Dataset.wrap(output)
            record.output = dataset if record.output is None else record.output.merge(dataset)

        if backlog is not None:
            record.backlog = backlog

        return record

    def get(self, object: JobOrStepOrSlug) -> RuntimeRecord | None:
        key = slugify(object) if isinstance(object, str) else object.slug
        return self._records.get(key)

    def get_records(self, objects: JobOrStepOrSlug | list[JobOrStepOrSlug]) -> list[RuntimeRecord]:
        objects = objects if isinstance(objects, list) else [objects]
        return [record for object in objects if (record := self.get(object))]

    def get_inputs(self, objects: JobOrStepOrSlug | list[JobOrStepOrSlug]) -> list[Dataset]:
        result = []
        for record in self.get_records(objects):
            result.extend(record.inputs)
        return result

    def get_outputs(self, objects: JobOrStepOrSlug | list[JobOrStepOrSlug]) -> list[Dataset]:
        result = []
        for record in self.get_records(objects):
            if record.output is not None:
                result.append(record.output)
        return result

    def get_backlog(self, object: JobOrStepOrSlug) -> list[Batch]:
        """
        Returns the memoized backlog of an object, or an empty list if none was registered.
        """
        record = self.get(object)
        return record.backlog if record else []
