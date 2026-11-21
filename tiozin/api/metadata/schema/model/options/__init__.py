"""
The options of each logical type.

A property reads plain dict options as the options of its logical type.

Examples:

    ```python
    Property(name="age", logicalType="integer", logicalTypeOptions={"minimum": 0})
    Property(name="age", logicalType="integer", logicalTypeOptions=IntegerOptions(minimum=0))
    ```
"""

from .array_options import ArrayOptions
from .date_options import DateOptions
from .integer_options import IntegerOptions
from .logical_type_options import LogicalTypeOptions
from .number_options import NumberOptions
from .object_options import ObjectOptions
from .string_options import StringOptions
from .timestamp_options import TimestampOptions
from .vector_options import VectorOptions

__all__ = [
    "ArrayOptions",
    "DateOptions",
    "IntegerOptions",
    "LogicalTypeOptions",
    "NumberOptions",
    "ObjectOptions",
    "StringOptions",
    "TimestampOptions",
    "VectorOptions",
]
