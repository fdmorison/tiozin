"""
Filesystem utilities for Tiozin.

This module provides a thin, provider-agnostic abstraction over filesystem
operations using ``fsspec``. It is intended to centralize common I/O behaviors
such as directory creation, deletion, and existence checks, working uniformly
across local filesystems, cloud storage (S3, GCS, Azure), and remote
protocols (HTTP, HTTPS, FTP, SFTP).

By concentrating filesystem semantics here, execution backends and outputs
remain focused on execution logic rather than storage-specific concerns.
"""

from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import fsspec

from tiozin import config

StrOrPath = str | Path


def _fs(path: StrOrPath) -> tuple[Any, str]:
    fs, _, paths = fsspec.get_fs_token_paths(str(path))
    return fs, paths[0]


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


def ensure_dir(path: StrOrPath) -> None:
    """
    Ensure that a directory exists.

    Creates the directory and any missing parent directories if needed.
    No-op if the directory already exists.
    """
    fs, p = _fs(path)

    if fs.exists(p):
        return

    fs.mkdirs(p, exist_ok=True)


def remove_dir(path: StrOrPath, recursive: bool = True) -> None:
    """
    Remove a directory.

    If ``recursive`` is True, removes the directory and all its contents.
    If False, attempts to remove only the empty directory.
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
    Create a temporary working directory under the application temp root.

    Each entry is treated as a path segment and appended in order, producing
    a hierarchical directory structure. The directory is created if it does
    not already exist.
    """
    path = config.app_temp_workdir
    for key in entries:
        if key:
            path /= key
    path.mkdir(parents=True, exist_ok=True)
    return path


def join_path(base: str, path: str) -> str | None:
    """
    Join ``path`` to ``base`` as a base directory.

    If ``path`` is relative (no URL scheme and not starting with ``/``),
    and does not already start with ``base``, it is joined to ``base``.
    Absolute paths and URIs with a scheme are returned unchanged.

    If either argument is ``None``, the other is returned as-is.
    If both are ``None``, returns ``None``.

    Works uniformly for local paths and remote URIs (``s3://``, ``http://``, etc.).
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
