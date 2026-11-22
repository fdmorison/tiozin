from __future__ import annotations

from collections.abc import Iterable
from typing import Any, Literal

import pydantic as pyd
from pygments.styles import get_all_styles
from rich.console import Console
from rich.syntax import RICH_SYNTAX_THEMES, Syntax

from tiozin.utils import default

from ..converters import SchemaConverter
from ..converters import conventions as conv
from ..exceptions import SchemaError
from ..merges import BackwardCompatibleEvolution, DocumentationMerge
from ..utils import SchemaYamlLexer
from .context import Context
from .element import Element
from .enums import Case, LogicalType
from .map import Map
from .path import PropertyPath
from .property import Property
from .relationship import Relationship

TERMINAL_BACKGROUND = "default"
DEFAULT_THEME = "solarized-dark"
DEFAULT_PHYSICAL_TYPE = "table"
INT8_FORMAT = "i8"
INT16_FORMAT = "i16"
INT32_FORMAT = "i32"
INT64_FORMAT = "i64"
FLOAT32_FORMAT = "f32"
FLOAT64_FORMAT = "f64"


class Schema(Element):
    """
    An Open Data Contract Standard schema that is easy to navigate and edit.

    Operations change the schema in place and return it, so calls can be
    chained. Use `clone` to keep the original.

    Find properties with a dotted path, such as "friends.name". Paths go
    through arrays and maps, and names ignore case.

    Examples:

        ```python
        schema = (
            Schema(name="users")
            .string("name", required=True)
            .object("profile")
            .integer("profile.age")
            .array("friends", of="object")
            .string("friends.name", classification="pii")
        )

        schema["friends.name"].classification
        # 'pii'

        "profile.age" in schema
        # True
        ```

        Load a schema from another format and convert it back:

        ```python
        schema = Schema.from_avro(avro_schema)
        schema.normalize_field_names("snake").to_spark()
        ```
    """

    physicalType: str | None = pyd.Field(
        DEFAULT_PHYSICAL_TYPE,
        description="Kind of object in storage, such as table, view, topic or file.",
    )
    logicalType: Literal["object"] | None = pyd.Field(
        None,
        description="Type of the schema, which is always object.",
    )
    dataGranularityDescription: str | None = pyd.Field(
        None,
        description="What one row of the data represents.",
    )
    properties: list[Property] | None = pyd.Field(
        None,
        description="Properties of the schema.",
    )
    context: Context | str | None = pyd.Field(
        None,
        description="Guidance for AI agents and tools on how to use the schema.",
    )

    @property
    def root(self) -> Property:
        """
        The properties of this schema as one object property. Editing it
        edits the schema.

        Examples:

            ```python
            schema.root.logicalType
            # 'object'

            schema.root.add(Property(name="email", logicalType="string"))
            "email" in schema
            # True
            ```
        """
        if self.properties is None:
            self.properties = []

        return Property.model_construct(logicalType=LogicalType.OBJECT, properties=self.properties)

    def show(self, theme: str = None) -> None:
        """
        Prints this schema as colored YAML.

        The theme is the name of any Pygments style, such as "dracula" or
        "nord". It is "solarized-dark" by default.

        Raises SchemaError if the theme does not exist.

        Examples:

            ```python
            schema.show()
            schema.show("dracula")
            ```
        """
        theme = default(theme, DEFAULT_THEME)

        SchemaError.raise_if_not_in(
            theme,
            [*RICH_SYNTAX_THEMES, *get_all_styles()],
        )

        yaml = Syntax(
            self.to_yaml(),
            SchemaYamlLexer(),
            theme=theme,
            background_color=TERMINAL_BACKGROUND,
        )
        Console().print(yaml)

    def to_format(self, format: str, **options) -> Any:
        """
        Converts this schema to another format.

        Supported formats include:
        - "spark": returns a Spark struct type in JSON, as a dict
        - "avro": returns an Avro record schema in JSON, as a dict

        Each format also has a shortcut, such as `to_avro()`. Options are
        settings specific to the format, such as `time_type` for "spark", and
        formats ignore the options they do not know.

        Raises SchemaError if the format is not supported.

        Examples:

            ```python
            schema = Schema(name="users").string("id")

            schema.to_format("avro")["type"]
            # 'record'

            schema.to_format("spark", time_type="time")

            StructType.fromJson(schema.to_spark())
            # StructType([StructField('id', StringType(), True)])
            ```
        """
        return SchemaConverter.for_format(format).dump(self, **options)

    @classmethod
    def from_format(cls, format: str, schema: Any, **options) -> Schema:
        """
        Creates a schema from another format.

        Supported formats include:
        - "spark": expects a Spark struct type in JSON, as a dict or a string
        - "avro": expects an Avro record schema in JSON, as a dict or a string

        Each format also has a shortcut, such as `from_avro()`. A string must
        hold the JSON document, not a path to a file. Options are settings
        specific to the format, and formats ignore the options they do not
        know.

        Raises SchemaError if the format is not supported.

        Examples:

            ```python
            Schema.from_format(
                "avro",
                {"type": "record", "name": "users", "fields": [{"name": "id", "type": "long"}]},
            )

            Schema.from_avro('{"type": "record", "name": "users", "fields": []}')

            Schema.from_spark(spark_df.schema.jsonValue())
            ```
        """
        return SchemaConverter.for_format(format).load(schema, **options)

    @classmethod
    def from_spark(cls, schema: dict[str, Any] | str, **options) -> Schema:
        return cls.from_format("spark", schema, **options)

    @classmethod
    def from_avro(cls, schema: dict[str, Any] | str, **options) -> Schema:
        return cls.from_format("avro", schema, **options)

    def to_spark(self, time_type: str = None, **options) -> dict[str, Any]:
        """
        Converts this schema to a Spark struct type in JSON, as a dict.

        The time type is the Spark type of a time property: "timestamp_ntz"
        by default, or "time", "long" or "string". No single Spark type reads
        a time from every source, so pick the one the source supports.
        """
        return self.to_format("spark", time_type=time_type, **options)

    def to_avro(self, **options) -> dict[str, Any]:
        return self.to_format("avro", **options)

    def flatten(self) -> dict[str, Property]:
        """
        Every property by its full path, such as "friends.name". Parents come
        before their children.

        Examples:

            ```python
            schema = Schema(name="users").string("name").array("friends", of="object")
            schema.string("friends.name")

            list(schema.flatten())
            # ['name', 'friends', 'friends.name']
            ```
        """
        return self.root.flatten()

    def normalize_field_names(self, case: str = None) -> Schema:
        """
        Renames every property to the given case, snake by default. See `Case`
        for the cases available.

        Raises SchemaError when two siblings end up with the same name.

        Examples:

            ```python
            schema = Schema(name="users").string("First Name").object("Home Address")
            schema.string("Home Address.Zip Code")

            list(schema.normalize_field_names().flatten())
            # ['first_name', 'home_address', 'home_address.zip_code']

            list(schema.normalize_field_names("camel").flatten())
            # ['firstName', 'homeAddress', 'homeAddress.zipCode']
            ```
        """
        case = default(case, Case.SNAKE)

        SchemaError.raise_if_not_in(
            case,
            list(Case),
        )

        self.root.normalize_field_names(Case(case))
        return self

    def sort(self) -> Schema:
        """
        Sorts the properties by name, ignoring case, at every level.

        Examples:

            ```python
            list(Schema(name="users").string("name").string("Age").sort().flatten())
            # ['Age', 'name']
            ```
        """
        self.root.sort()
        return self

    def evolve(self, observed: Schema) -> Schema:
        """
        Evolves this contract schema with an observed schema, keeping
        backward compatibility. See `BackwardCompatibleEvolution`.

        Examples:

            ```python
            contract = Schema(name="users").integer("id", required=True)
            observed = Schema(name="users").integer("id").string("email")

            contract.evolve(observed)
            list(contract.flatten())
            # ['id', 'email']

            contract["email"].required
            # False
            ```
        """
        return BackwardCompatibleEvolution().merge(self, observed)

    def document_from(self, contract: Schema) -> Schema:
        """
        Copies documentation from a contract schema into this observed schema,
        without touching structure or types. See `DocumentationMerge`.

        Examples:

            ```python
            contract = Schema(name="users").integer("id", description="Unique user id.")
            observed = Schema.from_spark(spark_df.schema.jsonValue())

            observed.document_from(contract)
            observed["id"].description
            # 'Unique user id.'
            ```
        """
        return DocumentationMerge().merge(self, contract)

    def add(
        self, path: str | Iterable[str], logical_type: LogicalType | str, **attributes
    ) -> Schema:
        """
        Adds a property at the given path. Extra arguments set attributes of
        the property, such as its description.

        The parent must already exist and be composite. Shortcuts such as
        `string` or `integer` pass the logical type for you.

        Examples:

            ```python
            schema.add("id", "integer", primaryKey=True)
            schema.add("profile", LogicalType.OBJECT)
            schema.add("profile.bio", "string", description="Free text.")

            schema.string("email", required=True, classification="pii")
            ```
        """
        path = PropertyPath(path)
        new_property = Property(name=path.name, logicalType=str(logical_type), **attributes)

        parent = self[path.parents] if path.parents else self.root
        parent.add(new_property)
        return self

    def remove(self, path: str | Iterable[str]) -> Schema:
        """
        Removes the property at the given path.

        Raises PropertyNotFoundError when there is no such property.

        Examples:

            ```python
            schema.remove("profile.bio").remove("email")
            ```
        """
        path = PropertyPath(path)

        parent = self[path.parents] if path.parents else self.root
        parent.remove(path.name)
        return self

    def string(self, path: str | Iterable[str], **attributes) -> Schema:
        return self.add(path, LogicalType.STRING, **attributes)

    def integer(self, path: str | Iterable[str], **attributes) -> Schema:
        return self.add(path, LogicalType.INTEGER, **attributes)

    def number(self, path: str | Iterable[str], **attributes) -> Schema:
        return self.add(path, LogicalType.NUMBER, **attributes)

    def boolean(self, path: str | Iterable[str], **attributes) -> Schema:
        return self.add(path, LogicalType.BOOLEAN, **attributes)

    def date(self, path: str | Iterable[str], **attributes) -> Schema:
        return self.add(path, LogicalType.DATE, **attributes)

    def timestamp(self, path: str | Iterable[str], **attributes) -> Schema:
        return self.add(path, LogicalType.TIMESTAMP, **attributes)

    def time(self, path: str | Iterable[str], **attributes) -> Schema:
        return self.add(path, LogicalType.TIME, **attributes)

    def time_millis(self, path: str | Iterable[str], **attributes) -> Schema:
        return self.time(path, timeUnit=conv.MILLIS, **attributes)

    def time_micros(self, path: str | Iterable[str], **attributes) -> Schema:
        return self.time(path, timeUnit=conv.MICROS, **attributes)

    def time_nanos(self, path: str | Iterable[str], **attributes) -> Schema:
        return self.time(path, timeUnit=conv.NANOS, **attributes)

    def timestamp_millis(self, path: str | Iterable[str], **attributes) -> Schema:
        return self.timestamp(path, timeUnit=conv.MILLIS, **attributes)

    def timestamp_micros(self, path: str | Iterable[str], **attributes) -> Schema:
        return self.timestamp(path, timeUnit=conv.MICROS, **attributes)

    def timestamp_nanos(self, path: str | Iterable[str], **attributes) -> Schema:
        return self.timestamp(path, timeUnit=conv.NANOS, **attributes)

    def timestamp_ntz(self, path: str | Iterable[str], **attributes) -> Schema:
        options = with_options(attributes, timezone=False)
        return self.timestamp(path, logicalTypeOptions=options, **attributes)

    def int8(self, path: str | Iterable[str], **attributes) -> Schema:
        options = with_options(attributes, format=INT8_FORMAT)
        return self.integer(path, logicalTypeOptions=options, **attributes)

    def int16(self, path: str | Iterable[str], **attributes) -> Schema:
        options = with_options(attributes, format=INT16_FORMAT)
        return self.integer(path, logicalTypeOptions=options, **attributes)

    def int32(self, path: str | Iterable[str], **attributes) -> Schema:
        options = with_options(attributes, format=INT32_FORMAT)
        return self.integer(path, logicalTypeOptions=options, **attributes)

    def int64(self, path: str | Iterable[str], **attributes) -> Schema:
        options = with_options(attributes, format=INT64_FORMAT)
        return self.integer(path, logicalTypeOptions=options, **attributes)

    def float32(self, path: str | Iterable[str], **attributes) -> Schema:
        options = with_options(attributes, format=FLOAT32_FORMAT)
        return self.number(path, logicalTypeOptions=options, **attributes)

    def float64(self, path: str | Iterable[str], **attributes) -> Schema:
        options = with_options(attributes, format=FLOAT64_FORMAT)
        return self.number(path, logicalTypeOptions=options, **attributes)

    def decimal(
        self, path: str | Iterable[str], precision: int, scale: int = None, **attributes
    ) -> Schema:
        return self.number(path, precision=precision, scale=scale, **attributes)

    def uuid(self, path: str | Iterable[str], **attributes) -> Schema:
        options = with_options(attributes, format=conv.UUID_FORMAT)
        return self.string(path, logicalTypeOptions=options, **attributes)

    def varchar(self, path: str | Iterable[str], length: int, **attributes) -> Schema:
        options = with_options(attributes, maxLength=length)
        return self.string(path, logicalTypeOptions=options, **attributes)

    def char(self, path: str | Iterable[str], length: int, **attributes) -> Schema:
        options = with_options(attributes, minLength=length, maxLength=length)
        return self.string(path, logicalTypeOptions=options, **attributes)

    def binary(self, path: str | Iterable[str], **attributes) -> Schema:
        return self.string(path, binary=True, **attributes)

    def fixed(self, path: str | Iterable[str], size: int, **attributes) -> Schema:
        return self.binary(path, typeSize=size, **attributes)

    def object(self, path: str | Iterable[str], **attributes) -> Schema:
        return self.add(path, LogicalType.OBJECT, **attributes)

    def array(self, path: str | Iterable[str], of: LogicalType | str, **attributes) -> Schema:
        """
        Adds an array whose elements have the given logical type. Add
        properties to an array of objects through the array path.

        Examples:

            ```python
            schema.array("tags", of="string")

            schema.array("friends", of="object")
            schema.string("friends.name")
            ```
        """
        element = Property(logicalType=str(of))
        return self.add(path, LogicalType.ARRAY, items=element, **attributes)

    def map(
        self,
        path: str | Iterable[str],
        value: LogicalType | str,
        key: LogicalType | str = None,
        **attributes,
    ) -> Schema:
        """
        Adds a map with the given value type. Keys are strings by default.

        Examples:

            ```python
            schema.map("scores", value="integer")
            schema.map("counts_by_day", value="integer", key="date")

            schema.map("addresses", value="object")
            schema.string("addresses.city")
            ```
        """
        map_definition = Map(
            key=Property(logicalType=str(default(key, LogicalType.STRING))),
            value=Property(logicalType=str(value)),
        )
        return self.add(path, LogicalType.MAP, map=map_definition, **attributes)

    @pyd.field_validator("properties")
    @classmethod
    def has_unique_names(cls, properties: list[Property] | None) -> list[Property] | None:
        """
        Raises SchemaError when a property has no name or shares its name
        with a sibling. Names ignore case.

        Examples:

            ```python
            Schema(name="users").string("id").string("ID")
            # SchemaError: Duplicate property `ID`
            ```
        """
        return Property.has_unique_names(properties)

    @pyd.field_validator("relationships")
    @classmethod
    def has_relationships_with_source(
        cls, relationships: list[Relationship] | None
    ) -> list[Relationship] | None:
        """
        Raises SchemaError when a relationship does not name its source.

        Examples:

            ```python
            Schema(
                name="orders",
                relationships=[
                    Relationship(**{"from": "orders.customer_id", "to": "customers.id"}),
                ],
            )

            Schema(name="orders", relationships=[Relationship(to="customers.id")])
            # SchemaError: A schema relationship needs both `from` and `to`
            ```
        """
        for relationship in relationships or []:
            SchemaError.raise_if(
                relationship.from_ is None,
                "A schema relationship needs both `from` and `to`",
            )

        return relationships

    def __getitem__(self, path: str | Iterable[str]) -> Property:
        return self.root[path]

    def __contains__(self, path: str | Iterable[str]) -> bool:
        return path in self.root


def with_options(attributes: dict[str, Any], **options) -> dict[str, Any]:
    """
    Removes the logical type options from the attributes and returns them
    with the given options added, so a shortcut keeps the options a caller
    passes.
    """
    given = attributes.pop("logicalTypeOptions", None)
    if isinstance(given, pyd.BaseModel):
        given = given.model_dump(exclude_unset=True)
    return {**(given or {}), **options}
