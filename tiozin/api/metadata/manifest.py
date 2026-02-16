from __future__ import annotations

import json
from io import StringIO
from typing import Any, Self

from pydantic import BaseModel, ConfigDict, ValidationError
from ruamel.yaml import YAML
from ruamel.yaml.constructor import DuplicateKeyError

from tiozin.compose.reflection import try_get
from tiozin.exceptions import ManifestError

_yaml = YAML(typ="safe")
_yaml.allow_duplicate_keys = False
_yaml.explicit_start = False
_yaml.sort_base_mapping_type_on_output = False
_yaml.default_flow_style = False


class Manifest(BaseModel):
    """
    Base manifest for pipeline resources.

    Provides identity and business context for runners, inputs, transforms, and outputs.
    """

    model_config = ConfigDict(extra="allow")

    @classmethod
    def for_kind(cls) -> type:
        """
        Returns the resource type expected to be built from this manifest.
        """
        return None

    @classmethod
    def model_validate(cls, obj, **kwargs) -> None:
        try:
            return super().model_validate(obj, **kwargs)
        except ValidationError as e:
            name = try_get(obj, "name", cls.__name__)
            raise ManifestError.from_pydantic(e, name=name) from e

    @classmethod
    def from_yaml_or_json(cls, data: str) -> Self:
        """
        Load manifest from YAML or JSON string.
        JSON is parsed as YAML since JSON is a valid YAML subset.

        Args:
            data: YAML or JSON formatted string to parse.
            failfast: returns None instead of raising an exception.

        Returns:
            Validated manifest instance.

        Raises:
            ManifestError: If the data contains duplicate keys or validation fails.
        """
        try:
            manifest = _yaml.load(data)
            return cls.model_validate(manifest)
        except DuplicateKeyError as e:
            raise ManifestError.from_ruamel(e, cls.__name__) from e

    @classmethod
    def try_from_yaml_or_json(cls, data: str | Manifest | Any) -> Self | None:
        """
        Alias of from_yaml_or_json() that suppresses all exceptions.
        Try to load manifest from YAML or JSON string, returning None on failure.

        Args:
            data: YAML/JSON string, manifest instance, or any other object type.

        Returns:
            Manifest instance if data is already a manifest or valid YAML/JSON string.
            Returns None if parsing/validation fails or data is an unsupported type.
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
        Serialize manifest to YAML string.

        Returns:
            YAML formatted string with None values excluded.
        """
        manifest = self.model_dump(mode="json", exclude_unset=True)
        data = StringIO()
        _yaml.dump(manifest, data)
        return data.getvalue()

    def to_json(self) -> str:
        """
        Serialize manifest to JSON string.

        Returns:
            Pretty-printed JSON string with 2-space indentation and None values excluded.
        """
        manifest = self.model_dump(mode="json", exclude_unset=True)
        return json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
