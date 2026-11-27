from __future__ import annotations

from typing import Any

from tiozin import config
from tiozin.api.loggable import Loggable
from tiozin.utils import default

from ...exceptions import SchemaError
from ...model import CustomProperty, LogicalType, Map, Property, Schema
from . import constants as const
from .spark_type import SparkType


class SparkSchemaWriter(Loggable):
    """
    Writes a schema as a Spark struct type in JSON.

    The Spark type comes from the logical type, the logical type options and
    the custom properties every converter shares, never from the physical
    type:

    - An integer is byte, short, integer or long, and a number is float or
      double, by its `format` option, long and double by default.
    - A number with `precision` and `scale` is a decimal.
    - A `binary` string is binary. A string with a `maxLength` option is a
      char when its `minLength` is the same, otherwise a varchar.
    - A timestamp is timestamp_ntz when its `timezone` option is false,
      otherwise timestamp.
    - A time is written as the type `time_type` names, and the field metadata
      keeps the `time` logical type when the Spark type implies another one.
      A time in nanos written as time or timestamp_ntz gets the finest
      precision Spark has, micros, with a warning.

    The type carries everything that defines it, because Spark drops field
    metadata easily, such as in `withColumn`.

    The description becomes the field comment. Every other attribute that the
    Spark type cannot express goes to the field metadata, so reading the result
    back restores the properties exactly. A custom property with only a name
    and a value becomes a metadata key of its own.

    Schema-level attributes, such as the name, go to a `metadata` key on the
    struct. Spark itself has no place for them and drops that key when the JSON
    goes through `StructType.fromJson()`.

    Attributes:
        time_type: Spark type of a time, because no single Spark type reads a
            time from every source. One of "time" (time(3) in millis, time(6)
            otherwise, Spark 4.1 and later), "timestamp_ntz", "long" or
            "string". Defaults to "timestamp_ntz".

    Examples:

        ```python
        schema = (
            Schema(name="users")
            .integer("id", physicalType="long", required=True)
            .string("email", physicalType="string", description="Email", classification="pii")
        )

        SparkSchemaWriter().write(schema)
        # {
        #     "type": "struct",
        #     "fields": [
        #         {"name": "id", "type": "long", "nullable": False, "metadata": {}},
        #         {
        #             "name": "email",
        #             "type": "string",
        #             "nullable": True,
        #             "metadata": {"comment": "Email", "classification": "pii"},
        #         },
        #     ],
        #     "metadata": {"name": "users"},
        # }
        ```
    """

    def __init__(self, time_type: str = None) -> None:
        time_type = default(time_type, const.DEFAULT_TIME_TYPE)

        SchemaError.raise_if_not_in(
            time_type,
            const.TIME_TYPES,
        )

        self.time_type = time_type

    def write(self, schema: Schema) -> dict[str, Any]:
        """
        Writes the schema as a Spark struct type in JSON, as a dict.
        """
        schema_attributes = schema.model_dump(
            mode="json",
            by_alias=True,
            exclude_unset=True,
            exclude_none=True,
            exclude={"properties"},
        )

        struct = {
            "type": "struct",
            "fields": [self.to_struct_field(property) for property in schema.properties or []],
            "metadata": schema_attributes,
        }

        return struct

    def to_struct_field(self, property: Property) -> dict[str, Any]:
        """
        Converts a property to a Spark struct field.

        Examples:

            ```python
            SparkSchemaWriter().to_struct_field(
                Property(
                    name="email",
                    logicalType="string",
                    physicalType="string",
                    description="Email",
                    required=True,
                )
            )
            # {
            #     "name": "email",
            #     "type": "string",
            #     "nullable": False,
            #     "metadata": {"comment": "Email"},
            # }
            ```
        """
        spark_type = self.to_spark_type(property)

        metadata_attributes = self.metadata_attributes(property, spark_type)
        metadata_attributes.pop("name", None)
        metadata_attributes.pop(const.CUSTOM_PROPERTIES_KEY, None)

        description = metadata_attributes.pop("description", None)
        comment = {const.COMMENT_KEY: description} if description is not None else {}

        return {
            "name": property.name,
            "type": spark_type.json_value,
            "nullable": not property.required,
            "metadata": {
                **comment,
                **metadata_attributes,
                **self.custom_metadata(property, spark_type),
            },
        }

    def to_spark_type(self, property: Property) -> SparkType:
        """
        The Spark type of a property.

        Raises SchemaError if the property has no type Spark can represent.

        Examples:

            ```python
            writer = SparkSchemaWriter()

            writer.to_spark_type(Property(name="id", logicalType="integer")).json_value
            # "long"

            writer.to_spark_type(
                Property(
                    name="price",
                    logicalType="number",
                    customProperties=[
                        {"property": "precision", "value": 10},
                        {"property": "scale", "value": 2},
                    ],
                )
            ).json_value
            # "decimal(10,2)"

            writer.to_spark_type(
                Property(name="tags", logicalType="array", items={"logicalType": "string"})
            ).json_value
            # {"type": "array", "elementType": "string", "containsNull": True}
            ```
        """
        match property:
            case Property(items=Property() as items):
                return SparkType(
                    {
                        "type": "array",
                        "elementType": self.to_spark_type(items).json_value,
                        "containsNull": not items.required,
                    }
                )
            case Property(map=Map(key=Property() as key, value=Property() as value)):
                return SparkType(
                    {
                        "type": "map",
                        "keyType": self.to_spark_type(key).json_value,
                        "valueType": self.to_spark_type(value).json_value,
                        "valueContainsNull": not value.required,
                    }
                )
            case Property(map=Map()):
                raise SchemaError(
                    f"Map property `{property.name}` needs both a key and a value definition"
                )
            case Property(properties=list()) | Property(logicalType=LogicalType.OBJECT):
                return SparkType(
                    {
                        "type": "struct",
                        "fields": [
                            self.to_struct_field(child) for child in property.properties or []
                        ],
                    }
                )
            case Property(logicalType=LogicalType.NUMBER, precision=int() as precision):
                scale = default(property.scale, const.DEFAULT_DECIMAL_SCALE)
                return SparkType(f"decimal({precision},{scale})")
            case Property(logicalType=LogicalType.STRING, binary=True):
                return SparkType(const.SPARK_BINARY_TYPE)
            case Property(logicalType=LogicalType.STRING) if isinstance(
                self.option_value(property, "maxLength"), int
            ):
                return SparkType(self.to_string_type_name(property))
            case Property(logicalType=LogicalType.TIME):
                return SparkType(self.to_time_type_name(property))
            case Property(logicalType=LogicalType.TIMESTAMP) if (
                self.option_value(property, "timezone") is False
            ):
                return SparkType(const.SPARK_TIMESTAMP_WITHOUT_TIMEZONE)
            case Property(logicalType=LogicalType.INTEGER):
                return SparkType(
                    self.to_sized_type_name(
                        property,
                        const.SPARK_INTEGER_BY_FORMAT,
                        config.default_schema_integer_format,
                    )
                )
            case Property(logicalType=LogicalType.NUMBER):
                return SparkType(
                    self.to_sized_type_name(
                        property, const.SPARK_NUMBER_BY_FORMAT, config.default_schema_number_format
                    )
                )
            case Property(logicalType=logical_type) if logical_type in const.LOGICAL_TO_SPARK:
                return SparkType(const.LOGICAL_TO_SPARK[logical_type])
            case _:
                raise SchemaError(f"Property `{property.name}` has no type Spark can represent")

    def to_time_type_name(self, property: Property) -> str:
        """
        The Spark type of a time, chosen by `time_type`.

        Spark keeps at most micros, so a time in nanos written as "time" or
        "timestamp_ntz" logs a warning.

        Examples:

            ```python
            time = Property(name="starts_at", logicalType="time")

            SparkSchemaWriter().to_time_type_name(time)
            # "timestamp_ntz"

            SparkSchemaWriter("time").to_time_type_name(time)
            # "time(6)"

            SparkSchemaWriter("long").to_time_type_name(time)
            # "long"
            ```
        """
        time_unit = default(property.timeUnit, config.default_schema_time_unit)

        if (
            self.time_type in const.MICROS_TIME_TYPES
            and time_unit not in const.SPARK_TIME_PRECISION_BY_UNIT
        ):
            self.warning(
                f"Property `{property.name}` is a time in {time_unit}, but Spark times go up "
                "to micros, so Spark truncates its values when it reads the data"
            )

        if self.time_type != const.TIME_AS_TIME:
            return self.time_type

        precision = const.SPARK_TIME_PRECISION_BY_UNIT.get(
            time_unit, const.SPARK_MAX_TIME_PRECISION
        )

        return f"time({precision})"

    def to_string_type_name(self, property: Property) -> str:
        """
        The Spark type of a string with a `maxLength` option: char when its
        `minLength` is the same, so every value has that length, otherwise
        varchar.
        """
        max_length = self.option_value(property, "maxLength")
        fixed_length = self.option_value(property, "minLength") == max_length
        type_name = (
            const.SPARK_FIXED_LENGTH_TYPE if fixed_length else const.SPARK_VARIABLE_LENGTH_TYPE
        )

        return f"{type_name}({max_length})"

    def to_sized_type_name(
        self,
        property: Property,
        types_by_format: dict[str, str],
        default_format: str,
    ) -> str:
        """
        The Spark type for the size of an integer or a number, given by the
        `format` option, or the default format when it has none.

        Raises SchemaError when Spark has no type of that size.
        """
        size_format = default(self.option_value(property, "format"), default_format)

        SchemaError.raise_if(
            size_format not in types_by_format,
            f"Property `{property.name}` has no Spark type for format `{size_format}`",
        )

        return types_by_format[size_format]

    def metadata_attributes(
        self,
        property: Property,
        spark_type: SparkType,
        tracks_nullability: bool = None,
    ) -> dict[str, Any]:
        """
        The attributes of the property that the Spark type cannot express.

        Pass `tracks_nullability=False` for map keys. Spark has no nullable
        flag for them, so `required` is always kept.

        Examples:

            ```python
            property = Property(
                name="email",
                logicalType="string",
                physicalType="string",
                description="Email",
                classification="pii",
            )
            writer = SparkSchemaWriter()

            writer.metadata_attributes(property, writer.to_spark_type(property))
            # {"name": "email", "description": "Email", "classification": "pii"}
            ```
        """
        tracks_nullability = default(tracks_nullability, True)
        required_was_set = "required" in property.model_fields_set

        metadata_attributes = property.model_dump(
            mode="json",
            by_alias=True,
            exclude_unset=True,
            exclude_none=True,
            exclude=const.STRUCTURAL_ATTRIBUTES | {"physicalType"},
        )

        if metadata_attributes.get("logicalType") == spark_type.logical_type:
            metadata_attributes.pop("logicalType")

        if metadata_attributes.get("logicalTypeOptions") == spark_type.logical_type_options:
            metadata_attributes.pop("logicalTypeOptions", None)

        custom_properties = [
            custom_property
            for custom_property in metadata_attributes.pop(const.CUSTOM_PROPERTIES_KEY, [])
            if custom_property not in spark_type.type_parameters
        ]

        if custom_properties:
            metadata_attributes[const.CUSTOM_PROPERTIES_KEY] = custom_properties

        if tracks_nullability and required_was_set and property.required is False:
            metadata_attributes["required"] = False

        if not tracks_nullability and required_was_set:
            metadata_attributes["required"] = property.required

        if property.items is not None:
            items_attributes = self.metadata_attributes(property.items, spark_type.element_type)

            if items_attributes:
                metadata_attributes["items"] = items_attributes

        if property.map is not None:
            map_attributes = {
                "key": self.metadata_attributes(
                    property.map.key,
                    spark_type.key_type,
                    tracks_nullability=False,
                ),
                "value": self.metadata_attributes(property.map.value, spark_type.value_type),
            }
            map_attributes = {entry: value for entry, value in map_attributes.items() if value}

            if map_attributes:
                metadata_attributes["map"] = map_attributes

        return metadata_attributes

    def custom_metadata(self, property: Property, spark_type: SparkType) -> dict[str, Any]:
        """
        The custom properties as field metadata: one key each when all of them
        are plain, otherwise the whole list under `customProperties`. Those the
        Spark type already holds, such as the precision of a decimal, are left
        out.

        Examples:

            ```python
            writer = SparkSchemaWriter()

            writer.custom_metadata(
                Property(name="id", customProperties=[{"property": "owner", "value": "crm"}]),
                SparkType("long"),
            )
            # {"owner": "crm"}

            writer.custom_metadata(
                Property(
                    name="id",
                    customProperties=[{"property": "owner", "value": "crm", "vendor": "acme"}],
                ),
                SparkType("long"),
            )
            # {"customProperties": [{"property": "owner", "value": "crm", "vendor": "acme"}]}
            ```
        """
        declared = property.model_dump(
            mode="json", include={"customProperties"}, exclude_unset=True
        )
        custom_properties = [
            CustomProperty.model_validate(custom_property)
            for custom_property in declared.get(const.CUSTOM_PROPERTIES_KEY) or []
            if custom_property not in spark_type.type_parameters
        ]

        if all(self.is_plain(custom_property) for custom_property in custom_properties):
            return {
                custom_property.property: custom_property.value
                for custom_property in custom_properties
            }

        return {
            const.CUSTOM_PROPERTIES_KEY: [
                custom_property.model_dump(mode="json", exclude_unset=True)
                for custom_property in custom_properties
            ]
        }

    @staticmethod
    def option_value(property: Property, name: str) -> Any:
        """
        The value of the logical type option with the given name, or None when
        the option is not set.
        """
        options = property.logicalTypeOptions

        if options is None or name not in options.model_fields_set:
            return None

        return getattr(options, name)

    @staticmethod
    def is_plain(custom_property: CustomProperty) -> bool:
        """
        Whether the custom property has only a name and a value, and its name
        is not the name of a property attribute.

        Examples:

            ```python
            SparkSchemaWriter.is_plain(CustomProperty(property="owner", value="crm"))
            # True

            SparkSchemaWriter.is_plain(CustomProperty(property="required", value="yes"))
            # False
            ```
        """
        return (
            custom_property.id is None
            and custom_property.description is None
            and custom_property.vendor is None
            and isinstance(custom_property.property, str)
            and custom_property.property not in const.PROPERTY_ATTRIBUTE_KEYS | {const.COMMENT_KEY}
        )
