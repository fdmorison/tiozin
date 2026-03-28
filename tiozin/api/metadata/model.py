from __future__ import annotations

from enum import StrEnum
from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field, ValidationError
from pydantic.config import ExtraValues
from ruamel.yaml.constructor import DuplicateKeyError

from tiozin.exceptions import ModelError
from tiozin.utils import dump_yaml, load_yaml, read_text, write_text
from tiozin.utils.io import StrOrPath

from . import docs


class Model(BaseModel):
    """
    Base model for Tiozin models.

    Provides validation, YAML/JSON I/O, and user-friendly errors.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_default=True,
        use_enum_values=True,
    )

    def __init__(self, **data: Any):
        try:
            super().__init__(**data)
        except ValidationError as e:
            raise ModelError.from_pydantic(type(self).__name__, e)

    @classmethod
    def model_validate(
        cls,
        obj: Any,
        *,
        strict: bool | None = None,
        extra: ExtraValues | None = None,
        from_attributes: bool | None = None,
        context: Any | None = None,
        by_alias: bool | None = None,
        by_name: bool | None = None,
    ) -> Self:
        try:
            return super().model_validate(
                obj,
                strict=strict,
                extra=extra,
                from_attributes=from_attributes,
                context=context,
                by_alias=by_alias,
                by_name=by_name,
            )
        except ValidationError as e:
            raise ModelError.from_pydantic(cls.__name__, e) from e

    @classmethod
    def from_file(cls, path: StrOrPath, **options) -> Self:
        """
        Load a model from a file or URI.

        Supports local paths and remote files via fsspec, including:
        s3://, gs://, az://, http://, https://, ftp://, and sftp://.

        Supported formats: YAML (.yaml, .yml) and JSON (.json).
        """
        return cls.from_yaml(read_text(path, **options))

    @classmethod
    def from_yaml(cls, data: str) -> Self:
        if not isinstance(data, str):
            raise ModelError(cls.__name__, f"Expected a model string, got: {data}")

        try:
            return cls.model_validate(load_yaml(data))
        except DuplicateKeyError as e:
            raise ModelError.from_ruamel(cls.__name__, e) from e
        except ModelError:
            raise
        except Exception as e:
            raise ModelError(cls.__name__, str(e)) from e

    @classmethod
    def try_from_yaml(cls, data: str | Model | Any) -> Self | None:
        if isinstance(data, cls):
            return data
        if not isinstance(data, str):
            return None
        try:
            return cls.from_yaml(data)
        except Exception:
            return None

    def to_yaml(self) -> str:
        return dump_yaml(self.model_dump(mode="json", exclude_unset=True))

    def to_json(self) -> str:
        return (
            self.model_dump_json(
                indent=2,
                exclude_unset=True,
                ensure_ascii=False,
            )
            + "\n"
        )

    def to_file(self, path: StrOrPath, **options) -> None:
        """
        Write the model to a file or URI.

        Supports local paths and remote files via fsspec, including:
        s3://, gs://, az://, http://, https://, ftp://, and sftp://.

        Supported formats: YAML (.yaml, .yml) and JSON (.json).
        """
        if path.endswith((".yaml", ".yml")):
            data = self.to_yaml()
        elif path.endswith(".json"):
            data = self.to_json()
        else:
            raise ValueError(f"Unsupported file format: {path}")

        write_text(path, data, **options)


class ImmutableModel(Model):
    """
    Base model for Tiozin immutable models.

    Represents a value object with enforced immutability.
    """

    model_config = ConfigDict(
        frozen=True,
        str_strip_whitespace=True,
        validate_default=True,
        use_enum_values=True,
    )


class Manifest(Model):
    """
    Base model for Tiozin manifests.

    Represents a typed recipe for constructing runtime objects.
    """

    model_config = ConfigDict(
        extra="allow",
        str_strip_whitespace=True,
        validate_default=True,
    )

    kind: str = Field(description=docs.KIND)


class UpperEnum(StrEnum):
    @staticmethod
    def _generate_next_value_(name: str, *_) -> str:
        return name.upper()

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return self.value


class LowerEnum(StrEnum):
    @staticmethod
    def _generate_next_value_(name: str, *_) -> str:
        return name.lower()

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return self.value
