"""
Common filesystem operations for Tiozin.

Wraps fsspec to work uniformly across local paths, cloud storage (S3, GCS,
Azure), and remote protocols (HTTP, HTTPS, FTP, SFTP).
"""

from datetime import date, datetime
from io import StringIO
from pathlib import Path
from typing import Any
from urllib.parse import urlparse, urlunparse

import fsspec
import rapidjson
from ruamel.yaml import YAML
from ruamel.yaml.representer import SafeRepresenter

from tiozin import config

from .helpers import isozformat

StrOrPath = str | Path


def _fs(path: StrOrPath) -> tuple[Any, str]:
    fs, _, paths = fsspec.get_fs_token_paths(str(path))
    return fs, paths[0]


def _yaml(timespec: str = None, indent: int = None) -> YAML:
    """
    Build the canonical YAML implementation used throughout Tiozin.

    This function encapsulates Tiozin's YAML conventions for both loading and
    dumping. Loading always runs in safe mode, duplicate keys are rejected, mapping
    order is preserved, output uses block style without the leading `---` document
    marker, and datetimes are serialized as ISO 8601 strings with a `Z` suffix for
    UTC (e.g. `2026-07-13T12:30:00Z`) instead of YAML's native timestamp format.

    The configurable behaviors are the datetime precision (`timespec`) and the
    block indentation width (`indent`).

    Args:
        timespec: Time precision for rendered datetimes. Values: see `isozformat`.
        indent: Block indentation width for mappings and sequences. Default is 2.
    """

    class TiozinRepresenter(SafeRepresenter):
        def represent_datetime(self, data: datetime) -> Any:
            return self.represent_scalar("tag:yaml.org,2002:timestamp", isozformat(data, timespec))

        def represent_date(self, data: date) -> Any:
            return self.represent_scalar("tag:yaml.org,2002:timestamp", data.isoformat())

    indent = indent or 2

    yaml = YAML(typ="safe")
    yaml.allow_duplicate_keys = False
    yaml.explicit_start = False
    yaml.sort_base_mapping_type_on_output = False
    yaml.default_flow_style = False
    yaml.indent(mapping=indent, sequence=indent, offset=max(indent - 2, 0))

    yaml.Representer = TiozinRepresenter
    yaml.Representer.add_representer(datetime, TiozinRepresenter.represent_datetime)
    yaml.Representer.add_multi_representer(datetime, TiozinRepresenter.represent_datetime)
    yaml.Representer.add_representer(date, TiozinRepresenter.represent_date)
    yaml.Representer.add_multi_representer(date, TiozinRepresenter.represent_date)
    return yaml


def read_text(path: StrOrPath, **options) -> str:
    """
    Read and return the full contents of a text file.

    Supports local filesystems, object storage, and remote protocols via fsspec
    (e.g. ``s3://``, ``gs://``, ``az://``, ``http://``, ``https://``, ``ftp://``, ``sftp://``).
    """
    with fsspec.open(str(path), mode="r", **options) as f:
        return f.read()


def write_text(path: StrOrPath, data: str, **options) -> None:
    """
    Write text data to a file.

    Supports local filesystems, object storage, and remote protocols via fsspec
    (e.g. ``s3://``, ``gs://``, ``az://``, ``sftp://``).
    """
    with fsspec.open(str(path), mode="w", **options) as f:
        f.write(data)


def dumps_json(value: Any, indent: int = None, timespec: str = None) -> str:
    """
    Serialize a Python value to a JSON string.

    Datetimes are rendered in ISO 8601 with a `Z` suffix for UTC
    (e.g. `2026-07-13T12:30:00Z`) and their offset preserved otherwise.
    `timespec` sets the rendered datetime time precision, forwarded to `isozformat`
    which defines the accepted values.
    """

    def _json_default(obj: Any) -> str:
        if isinstance(obj, date):
            return isozformat(obj, timespec)
        raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

    return rapidjson.dumps(value, default=_json_default, indent=indent)


def loads_json(value: str) -> Any:
    """
    Parse a JSON string into a Python value.

    ISO 8601 strings are read back as ``datetime`` or ``date`` objects; a datetime
    without a timezone is read as UTC.
    """
    return rapidjson.loads(
        value,
        datetime_mode=rapidjson.DM_ISO8601 | rapidjson.DM_NAIVE_IS_UTC,
    )


def load_yaml(text: str) -> Any:
    """
    Parse a YAML string and return the result.
    """
    return _yaml().load(text)


def dump_yaml(data: Any, indent: int = None, timespec: str = None) -> str:
    """
    Serialize data to a YAML string.

    Datetimes are rendered in ISO 8601 with a `Z` suffix for UTC
    (e.g. `2026-07-13T12:30:00Z`). `timespec` sets the rendered datetime time
    precision, forwarded to `isozformat` which defines the accepted values.
    `indent` sets the block indentation width; None uses the default.
    """
    buffer = StringIO()
    _yaml(timespec, indent).dump(data, buffer)
    return buffer.getvalue()


def read_yaml(path: StrOrPath, **options) -> Any:
    """
    Read and parse a YAML file.

    Supports local filesystems, object storage, and remote protocols via fsspec
    (e.g. `s3://`, `gs://`, `az://`, `http://`, `https://`, `ftp://`, `sftp://`).
    """
    return load_yaml(read_text(path, **options))


def write_yaml(path: StrOrPath, data: Any, **options) -> None:
    """
    Serialize and write data to a YAML file.

    Supports local filesystems, object storage, and remote protocols via fsspec
    (e.g. `s3://`, `gs://`, `az://`, `sftp://`).
    """
    write_text(path, dump_yaml(data), **options)


def mkdirs(path: StrOrPath) -> None:
    """
    Ensure that a directory exists.

    Creates the directory and any missing parent directories if needed.
    No-op if the directory already exists.
    """
    fs, p = _fs(path)
    fs.mkdirs(p, exist_ok=True)


def remove(path: StrOrPath, recursive: bool = False) -> None:
    """
    Remove a file or directory. No-op if the path does not exist.

    Directories with content require `recursive=True`. Without it, the
    operation will fail if the directory is not empty.
    """
    fs, p = _fs(path)

    if not fs.exists(p):
        return

    fs.rm(p, recursive=recursive)


def clear_dir(path: StrOrPath) -> None:
    """
    Remove all contents of a directory, preserving the directory itself.
    """
    fs, p = _fs(path)

    if not fs.exists(p):
        return

    if not fs.isdir(p):
        raise ValueError(f"Not a directory: {path}")

    for entry in fs.ls(p, detail=True):
        name = entry["name"]
        if entry["type"] == "directory":
            fs.rm(name, recursive=True)
        else:
            fs.rm(name)


def exists(path: StrOrPath) -> bool:
    """
    Return True if the path exists.
    """
    fs, p = _fs(path)
    return fs.exists(p)


def create_local_temp_dir(*entries: StrOrPath) -> Path:
    """
    Create and return a directory under the application temp root.

    Each entry becomes a path segment, appended in order. Empty and None
    entries are skipped. The directory is created if it does not exist.
    """
    path = config.app_temp_workdir
    for key in entries:
        if key:
            path /= key
    path.mkdir(parents=True, exist_ok=True)
    return path


def join_path(base: str, path: str) -> str | None:
    """
    Prepend `base` to `path` if `path` is relative.

    Relative means: no URL scheme and does not start with `/`. Absolute paths
    and URIs are returned unchanged. If `path` already starts with `base`,
    it is also returned unchanged.

    If either argument is None, the other is returned as-is. Both None returns None.
    """
    if base is None:
        return path
    if path is None:
        return base
    parsed = urlparse(path)
    if not parsed.scheme and not path.startswith("/"):
        prefix = base.rstrip("/") + "/"
        if not path.startswith(prefix):
            return prefix + path
    return path


def normalize_uri(
    uri: StrOrPath,
    *,
    as_absolute: bool = False,
    strip_glob: bool = False,
    strip_partitions: bool = False,
) -> str:
    """
    Normalize a URI or path.

    Removes trailing slashes and, optionally:

    - `strip_glob`: removes a glob pattern from the last path segment (``*``, ``?``, ``[``).
    - `strip_partitions`: removes Hive-style partition segments (``key=value``) from the
      right until a non-partition segment is reached.

    Preserves scheme/authority for URIs. For local paths, returns a `file://`
    URI when `as_absolute=True`, otherwise a normalized relative path.
    """
    uri = str(uri)

    def _strip_glob(path: str) -> str:
        p = Path(path)
        return str(p.parent) if any(c in p.name for c in "*?[") else path

    def _strip_partitions(path: str) -> str:
        p = Path(path)
        while "=" in p.name:
            p = p.parent
        return str(p)

    parsed = urlparse(uri)
    path = _strip_glob(parsed.path) if strip_glob else parsed.path
    path = _strip_partitions(path) if strip_partitions else path
    path = path.rstrip("/") or "/"

    if parsed.scheme:
        return urlunparse(parsed._replace(path=path))

    if not as_absolute:
        return path

    return Path(path).expanduser().resolve().as_uri()
