from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING

from .schema_merge_strategy import SchemaMergeStrategy

if TYPE_CHECKING:
    from ..model import Property, Schema

DOCUMENTATION_ATTRIBUTES = (
    "description",
    "businessName",
    "tags",
    "synonyms",
    "authoritativeDefinitions",
    "classification",
    "examples",
    "criticalDataElement",
)


class DocumentationMerge(SchemaMergeStrategy):
    """
    Copies documentation from a contract schema, the source, into an observed
    schema, the target, without touching its structure or types.

    Where the source schema has documentation, it replaces the documentation
    of the target schema. This applies to the schema and to every property
    with the same name.

    Schema.document_from applies this strategy.

    Examples:

        ```python
        contract = Schema(name="users", description="App users").integer(
            "id", description="User id"
        )
        observed = Schema(name="users").integer("id").string("email")

        DocumentationMerge().merge(observed, contract)
        # Same as observed.document_from(contract)

        observed.model_dump(exclude_unset=True)
        # {
        #     "name": "users",
        #     "description": "App users",
        #     "properties": [
        #         {"name": "id", "logicalType": "integer", "description": "User id"},
        #         {"name": "email", "logicalType": "string"},
        #     ],
        # }
        ```
    """

    def merge(self, target: Schema, source: Schema) -> Schema:
        self.copy_documentation(target, source)
        self.document_from(target.root, source.root)
        return target

    def document_from(self, target: Property, source: Property) -> Property:
        """
        Copies the documentation of the source property into the target
        property, at every level.

        Examples:

            ```python
            target = Property(name="id", logicalType="integer")
            source = Property(name="id", description="User id")

            DocumentationMerge().document_from(target, source)
            # Property(name="id", logicalType="integer", description="User id")
            ```
        """
        from ..model import Map, Property

        self.copy_documentation(target, source)

        match target, source:
            case (
                Property(map=Map(key=Property() as target_key)),
                Property(map=Map(key=Property() as source_key)),
            ):
                self.document_from(target_key, source_key)

        match target, source:
            case (
                Property(items=Property() as target_items),
                Property(items=Property() as source_items),
            ):
                self.document_from(target_items, source_items)
                return target
            case (
                Property(map=Map(value=Property() as target_value)),
                Property(map=Map(value=Property() as source_value)),
            ):
                self.document_from(target_value, source_value)
                return target

        for target_child in target.children():
            source_child = source.child(target_child.name)

            if source_child is not None:
                self.document_from(target_child, source_child)

        return target

    def copy_documentation(self, target: Schema | Property, source: Schema | Property) -> None:
        """
        Copies into the target every documentation attribute that the source
        has, such as description, tags or classification. Nested properties
        are not visited.

        Examples:

            ```python
            target = Property(name="email", logicalType="string")
            source = Property(name="email", classification="pii", tags=["contact"])

            DocumentationMerge().copy_documentation(target, source)
            # target.classification == "pii", target.tags == ["contact"]
            ```
        """
        for attribute in DOCUMENTATION_ATTRIBUTES:
            value = getattr(source, attribute, None)
            was_set = attribute in source.model_fields_set

            if was_set and value is not None and attribute in type(target).model_fields:
                setattr(target, attribute, deepcopy(value))
