from __future__ import annotations

from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field, ValidationError
from ruamel.yaml.constructor import DuplicateKeyError

from tiozin.exceptions import ManifestError
from tiozin.utils import dump_yaml, load_yaml

from . import docs


class Manifest(BaseModel):
    """
    Base class for serializable Tiozin manifests.

    Provides common validation, parsing, and serialization utilities for manifest definitions
    loaded from YAML or JSON.
    """

    model_config = ConfigDict(
        extra="allow",
        str_strip_whitespace=True,
        validate_default=True,
    )

    kind: str = Field(description=docs.KIND)

    @classmethod
    def model_validate(cls, obj, **kwargs) -> Self:
        try:
            return super().model_validate(obj, **kwargs)
        except ValidationError as e:
            raise ManifestError.from_pydantic(cls.__name__, e) from e

    @classmethod
    def from_arguments(cls, **kwargs) -> Self:
        try:
            return cls(**kwargs)
        except ValidationError as e:
            raise ManifestError.from_pydantic(cls.__name__, e) from e

    @classmethod
    def from_yaml_or_json(cls, data: str) -> Self:
        """
        Load a manifest instance from a YAML or JSON string.
        JSON is parsed as YAML since JSON is a valid YAML subset.

        Raises:
            ManifestError: If parsing or validation fails.
        """
        if not isinstance(data, str):
            raise ManifestError(
                manifest=cls.__name__,
                message=f"Manifest data should be a string, but got: {data}",
            )

        try:
            manifest = load_yaml(data)
            return cls.model_validate(manifest)
        except DuplicateKeyError as e:
            raise ManifestError.from_ruamel(cls.__name__, e) from e
        except ManifestError:
            raise
        except Exception as e:
            raise ManifestError(manifest=cls.__name__, message=str(e)) from e

    @classmethod
    def try_from_yaml_or_json(cls, data: str | Manifest | Any) -> Self | None:
        """
        Attempt to load a manifest from YAML or JSON.
        Returns None if parsing or validation fails.
        """
        if isinstance(data, cls):
            return data

        if not isinstance(data, str):
            return None

        try:
            return cls.from_yaml_or_json(data)
        except Exception:
            return None

    def to_yaml(self) -> str:
        """
        Serialize the manifest to a YAML string.
        Fields not explicitly set are excluded.
        """
        dyct = self.model_dump(mode="json", exclude_unset=True)
        return dump_yaml(dyct)

    def to_json(self) -> str:
        """
        Serialize the manifest to a pretty-printed JSON string.

        Fields not explicitly set are excluded.
        """
        return self.model_dump_json(indent=2, exclude_unset=True, ensure_ascii=False) + "\n"
