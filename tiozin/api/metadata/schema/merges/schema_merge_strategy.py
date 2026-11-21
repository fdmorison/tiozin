from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..model import Schema


class SchemaMergeStrategy(ABC):
    """
    A way of merging a source schema into a target schema.

    The target schema is edited in place and returned. The source schema is
    only read.

    Examples:

        A strategy that adds the properties the target does not have yet:

        ```python
        class AddMissing(SchemaMergeStrategy):
            def merge(self, target: Schema, source: Schema) -> Schema:
                for property in source.properties or []:
                    if property.name not in target:
                        target.root.add(property.model_copy(deep=True))
                return target

        merged = AddMissing().merge(target, source)
        ```
    """

    @abstractmethod
    def merge(self, target: Schema, source: Schema) -> Schema:
        """
        Merges the source schema into the target schema and returns the
        target.
        """
