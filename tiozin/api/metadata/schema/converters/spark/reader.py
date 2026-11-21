from __future__ import annotations

from typing import Any

from ...exceptions import SchemaError
from ...model import Property, Schema
from ...utils import without_none
from . import constants as const
from .spark_type import SparkType


class SparkSchemaReader:
    """
    Reads a schema from a Spark struct type in JSON.

    The field comment becomes the description. A metadata key with the name of
    a property attribute sets that attribute. Any other metadata key becomes a
    custom property.

    The physical type is the Spark type exactly as written, such as
    "decimal(10,2)", and the JSON of a complex type. The
    precision and the scale of a decimal become the `precision` and `scale`
    custom properties every converter shares, and a timestamp gets the
    `timeUnit` micros. A custom property in the metadata wins over these. The
    length of a char or a
    varchar becomes the `maxLength` option, and whether a timestamp carries its
    timezone becomes the `timezone` option.

    The `metadata` key of the struct, when present, sets the schema attributes.

    Examples:

        ```python
        SparkSchemaReader().read(
            {
                "type": "struct",
                "fields": [
                    {
                        "name": "id",
                        "type": "long",
                        "nullable": False,
                        "metadata": {"comment": "User id", "owner": "crm"},
                    },
                ],
                "metadata": {"name": "users"},
            }
        ).model_dump(exclude_unset=True)
        # {
        #     "name": "users",
        #     "properties": [
        #         {
        #             "name": "id",
        #             "logicalType": "integer",
        #             "physicalType": "long",
        #             "description": "User id",
        #             "customProperties": [{"property": "owner", "value": "crm"}],
        #             "required": True,
        #         },
        #     ],
        # }
        ```
    """

    def read(self, struct: dict[str, Any]) -> Schema:
        """
        Reads a schema from a Spark struct type in JSON, as a dict.

        Raises SchemaError if the value is not a struct type.
        """
        SchemaError.raise_if(
            not isinstance(struct, dict) or struct.get("type") != "struct",
            "A Spark schema must be a struct type",
        )

        return Schema.model_validate(
            {
                **(struct.get("metadata") or {}),
                "properties": [self.to_property(field) for field in SparkType(struct).fields],
            }
        )

    def to_property(self, field: dict[str, Any]) -> Property:
        """
        Converts a Spark struct field to a property.

        Examples:

            ```python
            SparkSchemaReader().to_property(
                {
                    "name": "email",
                    "type": "string",
                    "nullable": True,
                    "metadata": {"comment": "Email", "classification": "pii"},
                }
            )
            # Property(
            #     name="email",
            #     logicalType="string",
            #     physicalType="string",
            #     description="Email",
            #     classification="pii",
            # )
            ```
        """
        metadata = dict(field.get("metadata") or {})
        description = metadata.pop(const.COMMENT_KEY, None)

        metadata_attributes = {
            key: metadata.pop(key) for key in list(metadata) if key in const.PROPERTY_ATTRIBUTE_KEYS
        }
        custom_properties = [
            *(metadata_attributes.pop(const.CUSTOM_PROPERTIES_KEY, None) or []),
            *({"property": key, "value": value} for key, value in metadata.items()),
        ]

        field_attributes = without_none(
            {
                "name": field["name"],
                "required": self.required(field.get("nullable", True)),
                "description": description,
                const.CUSTOM_PROPERTIES_KEY: custom_properties or None,
            }
        )

        return self.read_type(SparkType(field["type"]), field_attributes, metadata_attributes)

    def read_type(
        self,
        spark_type: SparkType,
        attributes: dict[str, Any],
        metadata_attributes: dict[str, Any],
    ) -> Property:
        """
        Builds a property of the given Spark type with the given attributes.

        Metadata attributes bring back what the Spark type cannot express, and
        win over what it implies.

        Examples:

            ```python
            SparkSchemaReader().read_type(
                SparkType("long"),
                {"name": "id"},
                {"classification": "pii"},
            )
            # Property(name="id", logicalType="integer", physicalType="long", classification="pii")
            ```
        """
        metadata_attributes = dict(metadata_attributes)
        items_attributes = metadata_attributes.pop("items", None) or {}
        map_attributes = metadata_attributes.pop("map", None) or {}

        declared_properties = attributes.get(const.CUSTOM_PROPERTIES_KEY, [])
        declared_names = {custom_property["property"] for custom_property in declared_properties}
        custom_properties = [
            *(
                parameter
                for parameter in spark_type.type_parameters
                if parameter["property"] not in declared_names
            ),
            *declared_properties,
        ]
        property_attributes = without_none(
            {
                "logicalType": spark_type.logical_type,
                "physicalType": spark_type.physical_type,
                "logicalTypeOptions": spark_type.logical_type_options,
                **attributes,
                const.CUSTOM_PROPERTIES_KEY: custom_properties or None,
            }
        )

        match spark_type.type_name:
            case "struct":
                property_attributes["properties"] = [
                    self.to_property(field) for field in spark_type.fields
                ]
            case "array":
                property_attributes["items"] = self.read_type(
                    spark_type.element_type,
                    without_none({"required": self.required(spark_type.contains_null)}),
                    items_attributes,
                )
            case "map":
                property_attributes["map"] = {
                    "key": self.read_type(
                        spark_type.key_type,
                        {},
                        map_attributes.get("key") or {},
                    ),
                    "value": self.read_type(
                        spark_type.value_type,
                        without_none({"required": self.required(spark_type.value_contains_null)}),
                        map_attributes.get("value") or {},
                    ),
                }

        return Property.model_validate({**property_attributes, **metadata_attributes})

    @staticmethod
    def required(nullable: bool) -> bool | None:
        """
        The `required` attribute for a Spark nullable flag: True when nulls
        are not allowed, None otherwise.

        Examples:

            ```python
            SparkSchemaReader.required(False)  # True
            SparkSchemaReader.required(True)  # None
            ```
        """
        return None if nullable else True
