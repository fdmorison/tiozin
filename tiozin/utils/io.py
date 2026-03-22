"""
Common filesystem operations for Tiozin.

Wraps fsspec to work uniformly across local paths, cloud storage (S3, GCS,
Azure), and remote protocols (HTTP, HTTPS, FTP, SFTP).
"""

from io import StringIO
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import fsspec
from ruamel.yaml import YAML

from tiozin import config

StrOrPath = str | Path


def _fs(path: StrOrPath) -> tuple[Any, str]:
    fs, _, paths = fsspec.get_fs_token_paths(str(path))
    return fs, paths[0]


def _yaml() -> YAML:
    loader = YAML(typ="safe")
    loader.allow_duplicate_keys = False
    loader.explicit_start = False
    loader.sort_base_mapping_type_on_output = False
    loader.default_flow_style = False
    return loader


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


def load_yaml(text: str) -> Any:
    """
    Parse a YAML string and return the result.
    """
    return _yaml().load(text)


def dump_yaml(data: Any) -> str:
    """
    Serialize data to a YAML string.
    """
    buffer = StringIO()
    _yaml().dump(data, buffer)
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


def normalize_uri(uri: StrOrPath) -> str:
    """
    Return a fully qualified URI for the given path or URI.

    If `uri` already has a scheme (e.g. `s3://`, `gs://`, `file://`), it is
    returned unchanged. Otherwise it is treated as a local filesystem path:
    `~` is expanded and the path is resolved to an absolute `file://` URI.
    """
    parsed = urlparse(str(uri))

    # already a URI
    if parsed.scheme:
        return str(uri)

    # local path → file:// URI
    path = Path(uri).expanduser().resolve()
    return path.as_uri()
