from __future__ import annotations

from typing import TYPE_CHECKING

from .schema_merge_strategy import SchemaMergeStrategy

if TYPE_CHECKING:
    from ..model import Property, Schema

CONSTRAINT_ATTRIBUTES = {
    "primaryKey",
    "primaryKeyPosition",
    "unique",
    "partitioned",
    "partitionKeyPosition",
}


class BackwardCompatibleEvolution(SchemaMergeStrategy):
    """
    Evolves a contract schema, the target, with an observed schema, the
    source, keeping backward compatibility.

    - Properties in both schemas keep the target definition.
    - Properties only in the source schema are added as optional, without key,
      uniqueness or partitioning constraints.
    - Properties only in the target schema are kept.

    The same rules apply to nested properties. Names are case sensitive.

    Schema.evolve applies this strategy.

    Examples:

        ```python
        contract = Schema(name="users").integer("id", required=True, primaryKey=True)
        observed = Schema(name="users").integer("id").string("email", unique=True)

        BackwardCompatibleEvolution().merge(contract, observed)
        # Same as contract.evolve(observed)

        contract.model_dump(exclude_unset=True)
        # {
        #     "name": "users",
        #     "properties": [
        #         {"name": "id", "logicalType": "integer", "required": True, "primaryKey": True},
        #         {"name": "email", "logicalType": "string", "required": False},
        #     ],
        # }
        ```
    """

    def merge(self, target: Schema, source: Schema) -> Schema:
        self.evolve(target.root, source.root)
        return target

    def evolve(self, target: Property, source: Property) -> Property:
        """
        Evolves the target property with the source property, when both have
        the same structure. Otherwise the target is returned unchanged.

        Examples:

            ```python
            target = Property(name="profile", logicalType="object", properties=[])
            source = Property(
                name="profile",
                logicalType="object",
                properties=[{"name": "age", "logicalType": "integer"}],
            )

            BackwardCompatibleEvolution().evolve(target, source)
            # target now has an optional "age" property
            ```
        """
        from ..model import Map, Property

        match target, source:
            case (
                Property(items=Property() as target_items),
                Property(items=Property() as source_items),
            ):
                self.evolve(target_items, source_items)
                return target
            case (
                Property(map=Map(value=Property() as target_value)),
                Property(map=Map(value=Property() as source_value)),
            ):
                self.evolve(target_value, source_value)
                return target

        same_structure = (
            target.is_composite()
            and source.is_composite()
            and target.effective_type() == source.effective_type()
        )

        if not same_structure:
            return target

        for source_child in source.children():
            target_child = next(
                (child for child in target.children() if child.name == source_child.name),
                None,
            )

            if target_child is None:
                target.add(self.as_added(source_child))
                continue

            self.evolve(target_child, source_child)

        return target

    def as_added(self, property: Property) -> Property:
        """
        A copy of the property as it enters the target schema: optional and
        without constraints, at every level.

        Examples:

            ```python
            property = Property(name="id", logicalType="integer", required=True, primaryKey=True)

            BackwardCompatibleEvolution().as_added(property)
            # Property(name="id", logicalType="integer", required=False)
            ```
        """
        attributes = property.model_dump(
            exclude_unset=True,
            exclude=CONSTRAINT_ATTRIBUTES,
        )
        added = type(property).model_validate({**attributes, "required": False})

        children = added.children()
        children[:] = [self.as_added(child) for child in children]

        return added
