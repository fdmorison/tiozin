"""
Ways of merging a source schema into a target schema.

Examples:

    ```python
    contract.evolve(observed)        # BackwardCompatibleEvolution
    observed.document_from(contract) # DocumentationMerge
    ```
"""

from .backward_compatible_evolution import BackwardCompatibleEvolution
from .documentation_merge import DocumentationMerge
from .schema_merge_strategy import SchemaMergeStrategy

__all__ = [
    "BackwardCompatibleEvolution",
    "DocumentationMerge",
    "SchemaMergeStrategy",
]
