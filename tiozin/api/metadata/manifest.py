from __future__ import annotations

from pydantic import BaseModel, ConfigDict, ValidationError

from tiozin.exceptions import ManifestError
from tiozin.utils.helpers import try_get


class Manifest(BaseModel):
    """
    Base manifest for pipeline resources.

    Provides identity and business context for runners, inputs, transforms, and outputs.
    """

    model_config = ConfigDict(extra="allow")

    @classmethod
    def model_validate(cls, obj, **kwargs) -> None:
        try:
            return super().model_validate(obj, **kwargs)
        except ValidationError as e:
            name = try_get(obj, "name", cls.__name__)
            raise ManifestError.from_pydantic(e, name=name) from e
