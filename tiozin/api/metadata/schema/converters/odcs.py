from __future__ import annotations

from open_data_contract_standard.model import SchemaObject

from ..model import Schema
from .converter import SchemaConverter


class OdcsSchemaConverter(SchemaConverter[SchemaObject]):
    def export(self, schema: Schema) -> SchemaObject:
        return SchemaObject(**schema.model_dump())

    def import_(self, schema: SchemaObject) -> Schema:
        return Schema(**schema.model_dump())
