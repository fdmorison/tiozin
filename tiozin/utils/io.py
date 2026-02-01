"""
Filesystem utilities for Tiozin.

This module provides a thin, provider-agnostic abstraction over filesystem
operations using ``fsspec``. It is intended to centralize common I/O behaviors
such as directory creation, deletion, and existence checks, working uniformly
across local filesystems and cloud storage (e.g. S3, GCS, Azure).

By concentrating filesystem semantics here, execution backends and outputs
remain focused on execution logic rather than storage-specific concerns.
"""

from pathlib import Path
from typing import Any

import fsspec

from tiozin import config


def _fs(path: str) -> tuple[Any, str]:
    fs, _, paths = fsspec.get_fs_token_paths(path)
    return fs, paths[0]


def read_text(path: str, **options) -> str:
    """
    Read and return the full contents of a text file.

    Supports local filesystems and object storage via fsspec.
    """
    with fsspec.open(path, mode="r", **options) as f:
        return f.read()


def write_text(path: str, data: str, **options) -> None:
    """
    Write text data to a file.

    Supports local filesystems and object storage via fsspec.
    """
    with fsspec.open(path, mode="w", **options) as f:
        f.write(data)


def ensure_dir(path: str) -> None:
    """
    Ensure that a directory exists.

    Creates the directory and any missing parent directories if needed.
    No-op if the directory already exists.
    """
    fs, p = _fs(path)

    if fs.exists(p):
        return

    fs.mkdirs(p, exist_ok=True)


def remove_dir(path: str, recursive: bool = True) -> None:
    """
    Remove a directory.

    If ``recursive`` is True, removes the directory and all its contents.
    If False, attempts to remove only the empty directory.
    """
    fs, p = _fs(path)

    if not fs.exists(p):
        return

    fs.rm(p, recursive=recursive)


def clear_dir(path: str) -> None:
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


def exists(path: str) -> bool:
    """
    Return True if the path exists.
    """
    fs, p = _fs(path)
    return fs.exists(p)


def create_local_temp_dir(*entries: str) -> Path:
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
