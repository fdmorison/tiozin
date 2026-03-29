from __future__ import annotations

from typing import TYPE_CHECKING

from open_data_contract_standard.model import SchemaProperty
from openlineage.client.generated.schema_dataset import SchemaDatasetFacet, SchemaDatasetFacetFields

from .converter import SchemaConverter

if TYPE_CHECKING:
    from ..model import Schema


class OpenLineageConverter(SchemaConverter[SchemaDatasetFacet]):
    def export(self, schema: Schema) -> SchemaDatasetFacet:
        return SchemaDatasetFacet(fields=self.flatten(schema.properties or [], prefix=""))

    def import_(self, schema: SchemaDatasetFacet) -> Schema:
        raise NotImplementedError("OpenLineage schema import is not supported")

    def flatten(
        self, properties: list[SchemaProperty], prefix: str
    ) -> list[SchemaDatasetFacetFields]:
        fields: list[SchemaDatasetFacetFields] = []
        for field in properties:
            name = f"{prefix}.{field.name}" if prefix else field.name
            # Array of objects
            if field.items and field.items.properties:
                fields.append(
                    SchemaDatasetFacetFields(
                        name=name,
                        type=field.logicalType or "array<struct>",
                        description=field.description,
                    )
                )
                fields.extend(self.flatten(field.items.properties, prefix=f"{name}[]"))
            # Array of primitives
            elif field.items:
                fields.append(
                    SchemaDatasetFacetFields(
                        name=name,
                        type=f"array<{field.items.logicalType or 'string'}>",
                        description=field.description,
                    )
                )
            # Nested object
            elif field.properties:
                fields.append(
                    SchemaDatasetFacetFields(
                        name=name,
                        type=field.logicalType or "struct",
                        description=field.description,
                    )
                )
                fields.extend(self.flatten(field.properties, prefix=name))
            # Primitive field
            else:
                fields.append(
                    SchemaDatasetFacetFields(
                        name=name,
                        type=field.logicalType or "unknown",
                        description=field.description,
                    )
                )
        return fields
