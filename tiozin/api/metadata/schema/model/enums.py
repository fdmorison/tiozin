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
