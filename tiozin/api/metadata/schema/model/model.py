from __future__ import annotations

import pydantic as pyd

from tiozin.api.metadata.model import Metadata


class Model(Metadata):
    """
    Base of every schema model.

    Attributes are named as in the Open Data Contract Standard v3.2.0, and
    unknown attributes are rejected. Attributes that were never set keep the
    default of the standard, and stay out of the files the model writes.

    Examples:

        ```python
        Synonym(synonym="client", locale="en-US").to_yaml()
        # 'synonym: client\nlocale: en-US\n'

        Synonym(synonym="client", color="blue")
        # ModelError: Field `color` is not allowed.
        ```
    """

    model_config = pyd.ConfigDict(
        extra="forbid",
        serialize_by_alias=True,
        validate_by_name=True,
        validate_by_alias=True,
    )
