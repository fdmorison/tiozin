from __future__ import annotations

from collections.abc import Iterable
from typing import Any, ClassVar, Self

import pydantic as pyd

from tiozin import config
from tiozin.utils import default

from ..exceptions import PropertyNotFoundError, SchemaError
from .element import Element
from .enum_value import EnumValue
from .enums import (
    Case,
    IntegerFormat,
    LogicalType,
    NumberFormat,
    SemanticType,
    TiozinCustomProperty,
    TiozinLogicalType,
    TiozinTimeUnit,
    TypeField,
    TypeName,
)
from .map import Map
from .options import (
    ArrayOptions,
    DateOptions,
    IntegerOptions,
    LogicalTypeOptions,
    NumberOptions,
    ObjectOptions,
    StringOptions,
    TimestampOptions,
    VectorOptions,
)
from .path import PATH_SEPARATOR, PropertyPath
from .relationship import Relationship

NO_POSITION = -1

TYPE_NAMES = (*LogicalType, *TiozinLogicalType)

OPTIONS_BY_LOGICAL_TYPE = {
    LogicalType.STRING: StringOptions,
    LogicalType.DATE: DateOptions,
    LogicalType.TIMESTAMP: TimestampOptions,
    LogicalType.TIME: TimestampOptions,
    LogicalType.INTEGER: IntegerOptions,
    LogicalType.NUMBER: NumberOptions,
    LogicalType.OBJECT: ObjectOptions,
    LogicalType.ARRAY: ArrayOptions,
    LogicalType.VECTOR: VectorOptions,
}


class Property(Element):
    """
    A property of an Open Data Contract Standard schema.

    Nested properties live in `properties` for objects, in `items` for arrays
    and in `map.value` for maps. Navigation goes through arrays and maps, so
    the children of an array of objects are the properties of its elements.

    Names ignore case, and siblings cannot share a name.

    Editing methods change the property in place and return it, so calls can
    be chained.

    Find nested properties with a dotted path, as in a schema.

    Examples:

        ```python
        address = Property(
            name="address",
            logicalType="object",
            properties=[
                Property(name="city", logicalType="string", required=True),
                Property(name="zip_code", logicalType="string"),
            ],
        )

        friends = Property(
            name="friends",
            logicalType="array",
            items=Property(
                logicalType="object",
                properties=[Property(name="name", logicalType="string")],
            ),
        )
        friends["name"].logicalType
        # 'string'

        "CITY" in address
        # True
        ```
    """

    custom_fields: ClassVar[tuple[str, ...]] = (
        *Element.custom_fields,
        TiozinCustomProperty.BINARY,
        TiozinCustomProperty.PRECISION,
        TiozinCustomProperty.SCALE,
        TiozinCustomProperty.TYPE_SIZE,
        TiozinCustomProperty.TIME_UNIT,
    )

    logicalTypeOptions: pyd.SerializeAsAny[LogicalTypeOptions] | None = pyd.Field(
        None,
        description="Extra details about the logical type, such as a length or a range.",
    )
    required: bool = pyd.Field(
        False,
        description="Whether the property must always have a value.",
    )
    unique: bool = pyd.Field(
        False,
        description="Whether every value of the property is different from the others.",
    )
    primaryKey: bool | None = pyd.Field(
        None,
        description="Whether the property is part of the primary key.",
    )
    primaryKeyPosition: int = pyd.Field(
        NO_POSITION,
        description="Position of the property in the primary key, starting at 1.",
    )
    partitioned: bool = pyd.Field(
        False,
        description="Whether the data is partitioned by the property.",
    )
    partitionKeyPosition: int = pyd.Field(
        NO_POSITION,
        description="Position of the property in the partition key, starting at 1.",
    )
    semanticType: SemanticType = pyd.Field(
        SemanticType.COLUMN,
        description="Role of the property in the data model: column, measure or dimension.",
    )
    classification: str | None = pyd.Field(
        None,
        description="How sensitive the property is, such as public, restricted or pii.",
    )
    criticalDataElement: bool = pyd.Field(
        False,
        description="Whether the property is a critical data element.",
    )
    encryptedName: str | None = pyd.Field(
        None,
        description="Name of the property that holds the encrypted value of this one.",
    )
    transformSourceObjects: list[str] | None = pyd.Field(
        None,
        description="Objects the property is computed from.",
    )
    transformLogic: str | None = pyd.Field(
        None,
        description="Logic that computes the property.",
    )
    transformDescription: str | None = pyd.Field(
        None,
        description="What the logic that computes the property does.",
    )
    examples: list[Any] | None = pyd.Field(
        None,
        description="Sample values of the property.",
    )
    enum: list[EnumValue] | None = pyd.Field(
        None,
        min_length=1,
        description="Values the property is allowed to have.",
    )
    properties: list[Property] | None = pyd.Field(
        None,
        description="Nested properties of an object.",
    )
    items: Property | None = pyd.Field(
        None,
        description="Definition of the items of an array.",
    )
    map: Map | None = pyd.Field(
        None,
        description="Definition of the keys and the values of a map.",
    )
    binary: bool | None = pyd.Field(
        None,
        exclude=True,
        description=(
            "Whether a string holds raw bytes, which the standard has no logical type for. "
            "A Tiozin convention, written as the `binary` custom property, and left out "
            "when not set."
        ),
    )
    precision: int | None = pyd.Field(
        None,
        ge=1,
        exclude=True,
        description=(
            "Number of digits of a decimal number. A Tiozin convention, written as the "
            "`precision` custom property, and left out when not set."
        ),
    )
    scale: int | None = pyd.Field(
        None,
        ge=0,
        exclude=True,
        description=(
            "Number of digits after the point of a decimal number. A Tiozin convention, "
            "written as the `scale` custom property, and left out when not set."
        ),
    )
    typeSize: int | None = pyd.Field(
        None,
        ge=1,
        exclude=True,
        description=(
            "Size in bytes of a fixed-size binary type. A Tiozin convention, written as "
            "the `typeSize` custom property, and left out when not set."
        ),
    )
    timeUnit: TiozinTimeUnit | None = pyd.Field(
        None,
        exclude=True,
        description=(
            "Unit of a timestamp or a time. A Tiozin convention, written as the "
            "`timeUnit` custom property, and left out when not set."
        ),
    )

    def effective_type(self) -> str | None:
        """
        The logical type, taken from the structure when it is not set.

        Examples:

            ```python
            Property(name="age", logicalType="integer").effective_type()
            # 'integer'

            Property(name="tags", items=Property(logicalType="string")).effective_type()
            # 'array'

            Property(name="address", properties=[]).effective_type()
            # 'object'

            Property(name="unknown").effective_type()
            # None
            ```
        """
        match self:
            case Property(logicalType=str() as logical_type):
                return logical_type
            case Property(items=Property()):
                return LogicalType.ARRAY
            case Property(map=Map()):
                return LogicalType.MAP
            case Property(properties=list()):
                return LogicalType.OBJECT
            case _:
                return None

    def is_composite(self) -> bool:
        """
        Whether this property is an object, or an array or map of objects.
        Only composite properties hold nested properties.

        Examples:

            ```python
            schema = Schema(name="users").array("tags", of="string").array("friends", of="object")

            schema["tags"].is_composite()
            # False

            schema["friends"].is_composite()
            # True
            ```
        """
        match self:
            case Property(items=Property() as items):
                return items.is_composite()
            case Property(map=Map(value=Property() as value)):
                return value.is_composite()
            case _:
                return self.effective_type() == LogicalType.OBJECT

    def children(self) -> list[Property]:
        """
        The properties nested directly in this one, going through arrays and maps.
        Empty when there are none.

        Examples:

            ```python
            schema = Schema(name="users").array("friends", of="object").string("friends.name")

            [child.name for child in schema["friends"].children()]
            # ['name']
            ```
        """
        match self:
            case Property(items=Property() as items):
                return items.children()
            case Property(map=Map(value=Property() as value)):
                return value.children()
            case _:
                return self.properties or []

    def child(self, name: str) -> Property | None:
        """
        The child with the given name, ignoring case, or None.

        The name is a single name, not a path. Use `property["a.b"]` for paths.

        Examples:

            ```python
            address.child("CITY").name
            # 'city'

            address.child("country")
            # None
            ```
        """
        wanted_name = name.casefold()
        return next(
            (child for child in self.children() if child.name.casefold() == wanted_name),
            None,
        )

    def add(self, child: Property) -> Self:
        """
        Adds a child to this property, going through arrays and maps.

        Raises SchemaError when this property is not composite, or when the
        child has no name or shares its name with a sibling.

        Examples:

            ```python
            address.add(Property(name="country", logicalType="string"))

            schema["friends"].add(Property(name="age", logicalType="integer"))
            schema["friends.age"].logicalType
            # 'integer'

            address.add(Property(name="CITY", logicalType="string"))
            # SchemaError: Duplicate property `CITY`
            ```
        """
        match self:
            case Property(items=Property() as items):
                items.add(child)
                return self
            case Property(map=Map(value=Property() as value)):
                value.add(child)
                return self

        SchemaError.raise_if(
            not self.is_composite(),
            f"Property `{self.name}` cannot hold nested properties",
        )

        self.has_unique_names([*self.children(), child])

        if self.properties is None:
            self.properties = []

        self.properties.append(child)
        return self

    def remove(self, name: str) -> Self:
        """
        Removes the child with the given name, ignoring case.

        Raises PropertyNotFoundError when there is no such child.

        Examples:

            ```python
            address.remove("zip_code")

            address.remove("country")
            # PropertyNotFoundError: Property `country` not found.
            ```
        """
        child = self.child(name)

        PropertyNotFoundError.raise_if(
            child is None,
            name,
        )

        self.children().remove(child)
        return self

    def cast(self, logical_type: LogicalType | str) -> Self:
        """
        Changes the logical type of this property. The physical type is
        dropped, because it belonged to the old type.

        Raises SchemaError when the logical type does not exist.

        Examples:

            ```python
            property = Property(name="id", logicalType="integer", physicalType="bigint")
            property.cast("string")
            property.logicalType, property.physicalType
            # ('string', None)

            property.cast("text")
            # SchemaError: Invalid value 'text'. Must be one of: array, boolean, ...
            ```
        """
        SchemaError.raise_if_not_in(
            logical_type,
            list(LogicalType),
        )

        self.logicalType = LogicalType(logical_type)
        self.physicalType = None
        self.model_fields_set.discard("physicalType")
        return self

    def retype(
        self,
        type: TypeName,
        precision: int = None,
        scale: int = None,
        length: int = None,
        size: int = None,
        time_unit: TiozinTimeUnit | str = None,
        of: TypeName = None,
        key: TypeName = None,
        value: TypeName = None,
    ) -> Self:
        """
        Forces the logical type of this property, without checking
        compatibility. Documentation and constraints are kept.

        Args:
            type:
                An Open Data Contract Standard logical type, such as "integer",
                or a Tiozin logical type, such as "int32" or "decimal".
            precision:
                Number of digits of a decimal.
            scale:
                Number of digits after the point of a decimal.
            length:
                Maximum length of a varchar.
            size:
                Size in bytes of a fixed type.
            time_unit:
                Unit of a time or a timestamp.
            of:
                Type of the items of an array.
            key:
                Type of the keys of a map.
            value:
                Type of the values of a map.

        Raises:
            SchemaError:
                If the logical type does not exist, or an argument is missing or
                has an invalid value, such as a fixed type without size or a
                precision of 0. The property is left unchanged.
            TypeError:
                If an argument does not apply to the logical type, such as a length for an integer.

        Examples:

            ```python
            property.retype("integer")
            property.retype("int32")
            property.retype("decimal", precision=10, scale=2)
            property.retype("array", of="int32")
            ```
        """
        SchemaError.raise_if_not_in(
            type,
            TYPE_NAMES,
        )

        method = getattr(self, f"to_{type}")
        arguments = {
            "precision": precision,
            "scale": scale,
            "length": length,
            "size": size,
            "time_unit": time_unit,
            "of": of,
            "key": key,
            "value": value,
        }

        return method(**{name: arg for name, arg in arguments.items() if arg is not None})

    def to_string(self) -> Self:
        """Forces the logical type to a string with no length limit."""
        self._clear_type()
        self.logicalType = LogicalType.STRING
        return self

    def to_varchar(self, length: int = None) -> Self:
        """
        Forces the logical type to a string of at most `length` characters, or
        with no limit when `length` is not given.
        """
        SchemaError.raise_if(
            length is not None and length < 1,
            "A varchar requires a length of at least 1",
        )

        if length is None:
            return self.to_string()

        self._clear_type()
        self.logicalType = LogicalType.STRING
        self.logicalTypeOptions = StringOptions(maxLength=length)
        return self

    def to_char(self) -> Self:
        """Forces the logical type to a string of exactly one character."""
        self._clear_type()
        self.logicalType = LogicalType.STRING
        self.logicalTypeOptions = StringOptions(minLength=1, maxLength=1)
        return self

    def to_uuid(self) -> Self:
        """Forces the logical type to a string in the uuid format."""
        self._clear_type()
        self.logicalType = LogicalType.STRING
        self.logicalTypeOptions = StringOptions(format=TiozinLogicalType.UUID)
        return self

    def to_binary(self) -> Self:
        """Forces the logical type to a string of raw bytes."""
        self._clear_type()
        self.logicalType = LogicalType.STRING
        self.binary = True
        return self

    def to_fixed(self, size: int = None) -> Self:
        """Forces the logical type to a string of exactly `size` raw bytes."""
        SchemaError.raise_if(
            size is None,
            "A fixed type requires a size",
        ).raise_if(
            size < 1,
            "A fixed type requires a size of at least 1",
        )

        self._clear_type()
        self.logicalType = LogicalType.STRING
        self.binary = True
        self.typeSize = size
        return self

    def to_integer(self) -> Self:
        """Forces the logical type to a 64-bit integer."""
        return self.to_int64()

    def to_int8(self) -> Self:
        """Forces the logical type to an 8-bit integer."""
        self._clear_type()
        self.logicalType = LogicalType.INTEGER
        self.logicalTypeOptions = IntegerOptions(format=IntegerFormat.INT8)
        return self

    def to_int16(self) -> Self:
        """Forces the logical type to a 16-bit integer."""
        self._clear_type()
        self.logicalType = LogicalType.INTEGER
        self.logicalTypeOptions = IntegerOptions(format=IntegerFormat.INT16)
        return self

    def to_int32(self) -> Self:
        """Forces the logical type to a 32-bit integer."""
        self._clear_type()
        self.logicalType = LogicalType.INTEGER
        self.logicalTypeOptions = IntegerOptions(format=IntegerFormat.INT32)
        return self

    def to_int64(self) -> Self:
        """Forces the logical type to a 64-bit integer."""
        self._clear_type()
        self.logicalType = LogicalType.INTEGER
        self.logicalTypeOptions = IntegerOptions(format=IntegerFormat.INT64)
        return self

    def to_number(self, precision: int = None, scale: int = None) -> Self:
        """
        Forces the logical type to a 64-bit float, or to a decimal when
        `precision` or `scale` is given.
        """
        if precision is not None or scale is not None:
            return self.to_decimal(precision, scale)

        return self.to_float64()

    def to_float32(self) -> Self:
        """Forces the logical type to a 32-bit float."""
        self._clear_type()
        self.logicalType = LogicalType.NUMBER
        self.logicalTypeOptions = NumberOptions(format=NumberFormat.FLOAT32)
        return self

    def to_float64(self) -> Self:
        """Forces the logical type to a 64-bit float."""
        self._clear_type()
        self.logicalType = LogicalType.NUMBER
        self.logicalTypeOptions = NumberOptions(format=NumberFormat.FLOAT64)
        return self

    def to_decimal(self, precision: int = None, scale: int = None) -> Self:
        """
        Forces the logical type to a decimal of `precision` digits, `scale` of
        them after the point, 10 and 0 by default.
        """
        SchemaError.raise_if(
            precision is not None and precision < 1,
            "A decimal requires a precision of at least 1",
        ).raise_if(
            scale is not None and scale < 0,
            "A decimal requires a scale of at least 0",
        )

        self._clear_type()
        self.logicalType = LogicalType.NUMBER
        self.precision = default(precision, 10)
        self.scale = default(scale, 0)
        return self

    def to_boolean(self) -> Self:
        """Forces the logical type to a boolean."""
        self._clear_type()
        self.logicalType = LogicalType.BOOLEAN
        return self

    def to_date(self) -> Self:
        """Forces the logical type to a date."""
        self._clear_type()
        self.logicalType = LogicalType.DATE
        return self

    def to_time(self, time_unit: TiozinTimeUnit | str = None) -> Self:
        """Forces the logical type to a time of day, in micros by default."""
        SchemaError.raise_if_not_in(
            time_unit,
            list(TiozinTimeUnit),
            allow_none=True,
        )

        self._clear_type()
        self.logicalType = LogicalType.TIME
        self.timeUnit = default(time_unit, config.default_schema_time_unit)
        return self

    def to_time_millis(self) -> Self:
        """Forces the logical type to a time of day in millis."""
        return self.to_time(TiozinTimeUnit.MILLIS)

    def to_time_micros(self) -> Self:
        """Forces the logical type to a time of day in micros."""
        return self.to_time(TiozinTimeUnit.MICROS)

    def to_time_nanos(self) -> Self:
        """Forces the logical type to a time of day in nanos."""
        return self.to_time(TiozinTimeUnit.NANOS)

    def to_timestamp(self, time_unit: TiozinTimeUnit | str = None) -> Self:
        """Forces the logical type to a timestamp with timezone, in micros by default."""
        SchemaError.raise_if_not_in(
            time_unit,
            list(TiozinTimeUnit),
            allow_none=True,
        )

        self._clear_type()
        self.logicalType = LogicalType.TIMESTAMP
        self.logicalTypeOptions = TimestampOptions(timezone=True)
        self.timeUnit = default(time_unit, config.default_schema_time_unit)
        return self

    def to_timestamp_millis(self) -> Self:
        """Forces the logical type to a timestamp with timezone in millis."""
        return self.to_timestamp(TiozinTimeUnit.MILLIS)

    def to_timestamp_micros(self) -> Self:
        """Forces the logical type to a timestamp with timezone in micros."""
        return self.to_timestamp(TiozinTimeUnit.MICROS)

    def to_timestamp_nanos(self) -> Self:
        """Forces the logical type to a timestamp with timezone in nanos."""
        return self.to_timestamp(TiozinTimeUnit.NANOS)

    def to_timestamp_ntz(self, time_unit: TiozinTimeUnit | str = None) -> Self:
        """Forces the logical type to a timestamp without timezone, in micros by default."""
        SchemaError.raise_if_not_in(
            time_unit,
            list(TiozinTimeUnit),
            allow_none=True,
        )

        self._clear_type()
        self.logicalType = LogicalType.TIMESTAMP
        self.logicalTypeOptions = TimestampOptions(timezone=False)
        self.timeUnit = default(time_unit, config.default_schema_time_unit)
        return self

    def to_object(self) -> Self:
        """Forces the logical type to an object with no nested properties."""
        self._clear_type()
        self.logicalType = LogicalType.OBJECT
        self.properties = []
        return self

    def to_array(self, of: TypeName = None) -> Self:
        """Forces the logical type to an array of `of` items, strings by default."""
        SchemaError.raise_if_not_in(
            of,
            TYPE_NAMES,
            allow_none=True,
        )

        self._clear_type()
        self.logicalType = LogicalType.ARRAY
        self.items = Property().retype(default(of, LogicalType.STRING))
        return self

    def to_map(
        self,
        value: TypeName = None,
        key: TypeName = None,
    ) -> Self:
        """Forces the logical type to a map from `key` to `value`, strings by default."""
        SchemaError.raise_if_not_in(
            key,
            TYPE_NAMES,
            allow_none=True,
        ).raise_if_not_in(
            value,
            TYPE_NAMES,
            allow_none=True,
        )

        self._clear_type()
        self.logicalType = LogicalType.MAP
        self.map = Map(
            key=Property().retype(default(key, LogicalType.STRING)),
            value=Property().retype(default(value, LogicalType.STRING)),
        )
        return self

    def to_vector(self) -> Self:
        """Forces the logical type to a vector."""
        self._clear_type()
        self.logicalType = LogicalType.VECTOR
        return self

    def _clear_type(self) -> None:
        for field in TypeField:
            setattr(self, field, None)
            self.model_fields_set.discard(field)

        self.customProperties = [
            custom_property
            for custom_property in self.customProperties or []
            if custom_property.vendor is None and custom_property.property != "default"
        ] or None

        if self.customProperties is None:
            self.model_fields_set.discard("customProperties")

    def require(self) -> Self:
        """
        Marks this property as required.

        Examples:

            ```python
            schema["email"].require().required
            # True
            ```
        """
        self.required = True
        return self

    def optional(self) -> Self:
        """
        Marks this property as optional.

        Examples:

            ```python
            schema["email"].optional().required
            # False
            ```
        """
        self.required = False
        return self

    def normalize_field_names(self, case: Case) -> Self:
        """
        Renames every nested property to the given case. This property
        keeps its own name.

        Raises SchemaError when two siblings end up with the same name.

        Examples:

            ```python
            property = Property(
                name="Home Address",
                properties=[Property(name="Zip Code", logicalType="string")],
            )
            property.normalize_field_names(Case.SNAKE)
            [child.name for child in property.children()]
            # ['zip_code']

            Property(
                name="user",
                properties=[Property(name="a b"), Property(name="a_b")],
            ).normalize_field_names(Case.SNAKE)
            # SchemaError: Duplicate property `a_b`
            ```
        """
        for child in self.children():
            child.rename(case.convert(child.name))
            child.normalize_field_names(case)

        self.has_unique_names(self.children())
        return self

    def sort(self) -> Self:
        """
        Sorts the nested properties by name, ignoring case, at every level.

        Examples:

            ```python
            property = Property(
                name="user",
                properties=[Property(name="name"), Property(name="Age"), Property(name="id")],
            )
            [child.name for child in property.sort().children()]
            # ['Age', 'id', 'name']
            ```
        """
        children = self.children()
        children.sort(key=lambda child: child.name.casefold())

        for child in children:
            child.sort()

        return self

    def flatten(self) -> dict[str, Property]:
        """
        Every nested property by its full path, such as "friends.name".
        Parents come before their children.

        Examples:

            ```python
            list(address.flatten())
            # ['city', 'zip_code']

            list(schema["friends"].flatten())
            # ['name']
            ```
        """
        flattened = {}

        for child in self.children():
            flattened[child.name] = child

            for path, descendant in child.flatten().items():
                flattened[f"{child.name}{PATH_SEPARATOR}{path}"] = descendant

        return flattened

    @pyd.field_validator("properties")
    @classmethod
    def has_unique_names(cls, properties: list[Property] | None) -> list[Property] | None:
        """
        Raises SchemaError when a property has no name or shares its name
        with a sibling. Names ignore case.

        Examples:

            ```python
            Property(name="user", properties=[Property(name="id"), Property(name="ID")])
            # SchemaError: Duplicate property `ID`
            ```
        """
        seen_names = set()

        for property in properties or []:
            SchemaError.raise_if(
                not property.name,
                "Every nested property must have a name",
            ).raise_if(
                property.name.casefold() in seen_names,
                f"Duplicate property `{property.name}`",
            )
            seen_names.add(property.name.casefold())

        return properties

    @pyd.field_validator("logicalTypeOptions", mode="before")
    @classmethod
    def has_options_of_its_logical_type(cls, options: Any, info: pyd.ValidationInfo) -> Any:
        """
        Reads the options as the options of the logical type of the property.

        Examples:

            ```python
            property = Property(
                name="age",
                logicalType="integer",
                logicalTypeOptions={"minimum": 0},
            )
            property.logicalTypeOptions
            # IntegerOptions(format='i32', multipleOf=None, minimum=0, ...)
            ```
        """
        if not isinstance(options, dict):
            return options

        options_type = OPTIONS_BY_LOGICAL_TYPE.get(
            info.data.get("logicalType"),
            LogicalTypeOptions,
        )
        return options_type.model_validate(options)

    @pyd.field_validator("relationships")
    @classmethod
    def has_relationships_without_source(
        cls, relationships: list[Relationship] | None
    ) -> list[Relationship] | None:
        """
        Raises SchemaError when a relationship names its source, which is
        always the property itself.

        Examples:

            ```python
            Property(name="customer_id", relationships=[Relationship(to="customers.id")])

            Property(
                name="customer_id",
                relationships=[
                    Relationship(**{"from": "orders.customer_id", "to": "customers.id"}),
                ],
            )
            # SchemaError: A property relationship cannot have `from`: ...
            ```
        """
        for relationship in relationships or []:
            SchemaError.raise_if(
                relationship.from_ is not None,
                "A property relationship cannot have `from`: the source is the property itself",
            )

        return relationships

    def __getitem__(self, path: str | Iterable[str]) -> Property:
        path = PropertyPath(path)
        current = self

        for name in path:
            current = current.child(name)
            PropertyNotFoundError.raise_if(
                current is None,
                str(path),
            )

        return current

    def __contains__(self, path: str | Iterable[str]) -> bool:
        try:
            self[path]
        except PropertyNotFoundError:
            return False
        return True
