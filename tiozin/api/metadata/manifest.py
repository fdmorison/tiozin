from __future__ import annotations

from io import StringIO
from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field, ValidationError
from ruamel.yaml import YAML
from ruamel.yaml.constructor import DuplicateKeyError

from tiozin.exceptions import ManifestError

from . import docs

_yaml = YAML(typ="safe")
_yaml.allow_duplicate_keys = False
_yaml.explicit_start = False
_yaml.sort_base_mapping_type_on_output = False
_yaml.default_flow_style = False


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
            manifest = _yaml.load(data)
            return cls.model_validate(manifest)
        except DuplicateKeyError as e:
            raise ManifestError.from_ruamel(cls.__name__, e) from e

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
        except ManifestError:
            return None

    def to_yaml(self) -> str:
        """
        Serialize the manifest to a YAML string.
        Fields not explicitly set are excluded.
        """
        manifest = self.model_dump(mode="json", exclude_unset=True)
        data = StringIO()
        _yaml.dump(manifest, data)
        return data.getvalue()

    def to_json(self) -> str:
        """
        Serialize the manifest to a pretty-printed JSON string.

        Fields not explicitly set are excluded.
        """
        return self.model_dump_json(indent=2, exclude_unset=True, ensure_ascii=False) + "\n"
