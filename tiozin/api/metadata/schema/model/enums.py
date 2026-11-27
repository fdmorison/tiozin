from enum import StrEnum

import inflection

from tiozin.utils import slugify

NAME_WITHOUT_WORDS = "_"


class LogicalType(StrEnum):
    """
    Logical data types defined by the Open Data Contract Standard v3.2.0.

    A logical type does not depend on any engine. Engine details, such as the
    width of an integer, go in the physical type of the property.

    Wherever a logical type is expected, its name as a string works too.

    Examples:

        ```python
        Property(name="age", logicalType=LogicalType.INTEGER)
        Property(name="age", logicalType="integer")

        schema.add("age", LogicalType.INTEGER)
        schema["age"].cast("string")
        ```
    """

    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    DATE = "date"
    TIMESTAMP = "timestamp"
    TIME = "time"
    OBJECT = "object"
    ARRAY = "array"
    MAP = "map"
    VECTOR = "vector"


class TiozinCustomProperty(StrEnum):
    """
    Attributes of a type that the Open Data Contract Standard has no place
    for. Tiozin writes them as custom properties of the same name, without
    vendor, and every converter reads and writes them with the same meaning.

    - typeName and namespace: the name and namespace of a named type, such as
      an Avro record, enum or fixed type.
    - binary: true for a string of raw bytes.
    - precision and scale: the digits of a decimal number.
    - typeSize: the size in bytes of a fixed-size binary type.
    - timeUnit: the unit of a timestamp or a time.
    """

    TYPE_NAME = "typeName"
    NAMESPACE = "namespace"
    BINARY = "binary"
    PRECISION = "precision"
    SCALE = "scale"
    TYPE_SIZE = "typeSize"
    TIME_UNIT = "timeUnit"


class IntegerFormat(StrEnum):
    """
    Size and sign of an integer, named as the Rust integer types, as the Open
    Data Contract Standard v3.2.0 defines them.
    """

    INT8 = "i8"
    INT16 = "i16"
    INT32 = "i32"
    INT64 = "i64"
    INT128 = "i128"
    UINT8 = "u8"
    UINT16 = "u16"
    UINT32 = "u32"
    UINT64 = "u64"
    UINT128 = "u128"


class NumberFormat(StrEnum):
    """
    Size of a floating point number, named as the Rust float types, as the
    Open Data Contract Standard v3.2.0 defines them.
    """

    FLOAT32 = "f32"
    FLOAT64 = "f64"


class StringFormat(StrEnum):
    """
    Formats of a string that Tiozin knows.
    """

    UUID = "uuid"


class TimeUnit(StrEnum):
    """
    Unit of a timestamp or a time.
    """

    MILLIS = "millis"
    MICROS = "micros"
    NANOS = "nanos"


class Case(StrEnum):
    """
    Naming conventions that property names can be normalized to.

    - snake: lowercase words delimited by underscores, as `first_name`.
    - camel: words without delimiters, all capitalized but the first, as `firstName`.
    - pascal: capitalized words without delimiters, as `FirstName`.
    - macro: uppercase words delimited by underscores, as `FIRST_NAME`.
    - kebab: lowercase words delimited by hyphens, as `first-name`.
    - cobol: uppercase words delimited by hyphens, as `FIRST-NAME`.
    - flat: lowercase words without delimiters, as `firstname`.
    - upperflat: uppercase words without delimiters, as `FIRSTNAME`.

    Examples:

        ```python
        Case.CAMEL.convert("first_name")
        # 'firstName'

        schema.normalize_field_names("kebab")
        ```
    """

    SNAKE = "snake"
    CAMEL = "camel"
    PASCAL = "pascal"
    MACRO = "macro"
    KEBAB = "kebab"
    COBOL = "cobol"
    FLAT = "flat"
    UPPERFLAT = "upperflat"

    def convert(self, name: str) -> str:
        """
        Writes the name in this case.

        Accents are replaced by plain letters, separators and special
        characters split the words, and a name that starts with a digit gets
        an underscore in front. A name made only of special characters
        becomes an underscore.

        Examples:

            ```python
            Case.CAMEL.convert("First Name")
            # 'firstName'

            Case.MACRO.convert("firstName")
            # 'FIRST_NAME'

            Case.SNAKE.convert("Ação Nº1")
            # 'acao_no1'

            Case.SNAKE.convert("1st place")
            # '_1st_place'

            Case.SNAKE.convert("!!!")
            # '_'
            ```
        """
        snake_name = slugify(name).removeprefix("_")

        if not snake_name:
            return NAME_WITHOUT_WORDS

        match self:
            case Case.CAMEL:
                converted_name = inflection.camelize(snake_name, uppercase_first_letter=False)
            case Case.PASCAL:
                converted_name = inflection.camelize(snake_name)
            case Case.MACRO:
                converted_name = snake_name.upper()
            case Case.KEBAB:
                converted_name = snake_name.replace("_", "-")
            case Case.COBOL:
                converted_name = snake_name.replace("_", "-").upper()
            case Case.FLAT:
                converted_name = snake_name.replace("_", "")
            case Case.UPPERFLAT:
                converted_name = snake_name.replace("_", "").upper()
            case _:
                converted_name = snake_name

        return f"_{converted_name}" if converted_name[:1].isdigit() else converted_name
