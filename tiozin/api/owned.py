from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, Field

from tiozin.utils import default

from . import docs


class Owned:
    """
    Mixin that adds ownership metadata to a class.

    Defines the standard ownership fields (owner, maintainer, cost_center, and
    labels) used to identify who is responsible for a resource.
    """

    owner: Annotated[str | None, Field(description=docs.OWNER, frozen=True)] = None
    maintainer: Annotated[str | None, Field(description=docs.MAINTAINER, frozen=True)] = None
    cost_center: Annotated[str | None, Field(description=docs.COST_CENTER, frozen=True)] = None
    labels: Annotated[
        dict[str, str], Field(description=docs.LABELS, frozen=True, default_factory=dict)
    ]

    def __init__(self, *args, **options) -> None:
        if isinstance(self, BaseModel):
            return super().__init__(*args, **options)

        self.owner = options.pop("owner", None)
        self.maintainer = options.pop("maintainer", None)
        self.cost_center = options.pop("cost_center", None)
        self.labels = options.pop("labels", None) or {}

        super().__init__(*args, **options)

    def to_owned_dict(self, flat: bool = None) -> dict:
        """
        Return the ownership fields as a dictionary.

        When flat is True, labels are flattened.
        """
        flat = default(flat, False)

        result = {
            "owner": self.owner,
            "maintainer": self.maintainer,
            "cost_center": self.cost_center,
        }

        if flat:
            return result | self.labels

        return result | {"labels": self.labels}
