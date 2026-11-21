from __future__ import annotations

import pydantic as pyd

from ..model import Model


class LogicalTypeOptions(Model):
    """
    Extra details about the logical type of a property.

    Each logical type has its own options, such as the length of a string or
    the range of an integer. Types without options of their own accept any.

    Pass a dict and the property picks the options class of its logical type,
    so unknown options of a typed class are rejected.

    Examples:

        ```python
        Property(name="active", logicalType="boolean", logicalTypeOptions={"anything": 1})

        Property(name="name", logicalType="string", logicalTypeOptions={"maxLength": 80})
        # logicalTypeOptions is a StringOptions

        Property(name="name", logicalType="string", logicalTypeOptions={"anything": 1})
        # ModelError: StringOptions: `Field `anything` is not allowed.`
        ```
    """

    model_config = pyd.ConfigDict(extra="allow")
