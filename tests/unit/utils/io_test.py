from pathlib import Path

import pytest

from tests.config import app_temp_workdir
from tiozin.utils.io import (
    clear_dir,
    create_local_temp_dir,
    ensure_dir,
    exists,
    join_path,
    read_text,
    remove_dir,
    write_text,
)


# ============================================================================
# Testing create_local_temp_dir()
# ============================================================================
def test_create_local_temp_dir_should_create_directory():
    # Act
    dir = create_local_temp_dir("my_job")

    # Assert
    actual = (
        dir,
        dir.is_dir(),
    )
    expected = (
        app_temp_workdir / "my_job",
        True,
    )
    assert actual == expected


def test_create_local_temp_dir_should_create_subdirectories():
    # Act
    dir = create_local_temp_dir("job_name", "run_id", "step_name")

    # Assert
    actual = (
        dir,
        dir.is_dir(),
    )
    expected = (
        app_temp_workdir / "job_name" / "run_id" / "step_name",
        True,
    )
    assert actual == expected


@pytest.mark.parametrize(
    "entry",
    ["", None],
)
def test_create_local_temp_dir_should_skip_unset_entries(entry: str):
    # Act
    create_local_temp_dir("job_name", entry, "step_name")

    # Assert
    expected = app_temp_workdir / "job_name" / "step_name"
    assert expected.exists()


def test_create_local_temp_dir_should_return_app_temp_dir_when_no_entries():
    # Act
    dir = create_local_temp_dir()

    # Assert
    actual = dir
    expected = app_temp_workdir
    assert actual == expected


def test_create_local_temp_dir_should_be_idempotent():
    # Act
    create_local_temp_dir("my_job", "run_123")
    create_local_temp_dir("my_job", "run_123")

    # Assert
    expected = app_temp_workdir / "my_job" / "run_123"
    assert expected.exists()


def test_create_local_temp_dir_should_accept_path_as_first_entry():
    # Arrange
    base_path = app_temp_workdir / "existing_job"

    # Act
    create_local_temp_dir(base_path, "step_name")

    # Assert
    expected = base_path / "step_name"
    assert expected.exists()


# ============================================================================
# Testing write_text() / read_text()
# ============================================================================
@pytest.mark.parametrize("path_type", [str, Path])
def test_write_text_should_write_content_to_file(tmp_path: Path, path_type: type[str] | Path):
    # Arrange
    file = tmp_path / "out.txt"
    path = path_type(file)

    # Act
    write_text(path, "hello")

    # Assert
    actual = file.read_text()
    expected = "hello"
    assert actual == expected


@pytest.mark.parametrize("path_type", [str, Path])
def test_read_text_should_return_file_contents(tmp_path: Path, path_type: type[str] | Path):
    # Arrange
    file = tmp_path / "in.txt"
    file.write_text("world")
    path = path_type(file)

    # Act
    result = read_text(path)

    # Assert
    actual = result
    expected = "world"
    assert actual == expected


# ============================================================================
# Testing ensure_dir()
# ============================================================================
@pytest.mark.parametrize("path_type", [str, Path])
def test_ensure_dir_should_create_directory(tmp_path: Path, path_type: type[str] | Path):
    # Arrange
    target = tmp_path / "new_dir"
    path = path_type(target)

    # Act
    ensure_dir(path)

    # Assert
    actual = target.is_dir()
    expected = True
    assert actual == expected


@pytest.mark.parametrize("path_type", [str, Path])
def test_ensure_dir_should_not_fail_when_directory_already_exists(
    tmp_path: Path, path_type: type[str] | Path
):
    # Arrange
    target = tmp_path / "existing_dir"
    target.mkdir()
    path = path_type(target)

    # Act
    ensure_dir(path)

    # Assert
    actual = target.is_dir()
    expected = True
    assert actual == expected


# ============================================================================
# Testing remove_dir()
# ============================================================================
@pytest.mark.parametrize("path_type", [str, Path])
def test_remove_dir_should_delete_directory(tmp_path: Path, path_type: type[str] | Path):
    # Arrange
    target = tmp_path / "to_remove"
    target.mkdir()
    path = path_type(target)

    # Act
    remove_dir(path)

    # Assert
    actual = target.exists()
    expected = False
    assert actual == expected


# ============================================================================
# Testing remove_dir()
# ============================================================================
@pytest.mark.parametrize("path_type", [str, Path])
def test_remove_dir_should_be_noop_when_path_does_not_exist(
    tmp_path: Path, path_type: type[str] | Path
):
    # Arrange
    path = path_type(tmp_path / "ghost")

    # Act
    remove_dir(path)

    # Assert
    actual = (tmp_path / "ghost").exists()
    expected = False
    assert actual == expected


# ============================================================================
# Testing clear_dir()
# ============================================================================
@pytest.mark.parametrize("path_type", [str, Path])
def test_clear_dir_should_remove_contents_and_preserve_directory(
    tmp_path: Path, path_type: type[str] | Path
):
    # Arrange
    target = tmp_path / "to_clear"
    target.mkdir()
    (target / "file.txt").write_text("data")
    path = path_type(target)

    # Act
    clear_dir(path)

    # Assert
    actual = (target.is_dir(), list(target.iterdir()))
    expected = (True, [])
    assert actual == expected


@pytest.mark.parametrize("path_type", [str, Path])
def test_clear_dir_should_be_noop_when_directory_is_empty(
    tmp_path: Path, path_type: type[str] | Path
):
    # Arrange
    target = tmp_path / "empty_dir"
    target.mkdir()
    path = path_type(target)

    # Act
    clear_dir(path)

    # Assert
    actual = (target.is_dir(), list(target.iterdir()))
    expected = (True, [])
    assert actual == expected


# ============================================================================
# Testing exists()
# ============================================================================
@pytest.mark.parametrize("path_type", [str, Path])
def test_exists_should_return_true_when_path_exists(tmp_path: Path, path_type: type[str] | Path):
    # Arrange
    path = path_type(tmp_path)

    # Act
    result = exists(path)

    # Assert
    actual = result
    expected = True
    assert actual == expected


@pytest.mark.parametrize("path_type", [str, Path])
def test_exists_should_return_false_when_path_does_not_exist(
    tmp_path: Path, path_type: type[str] | Path
):
    # Arrange
    path = path_type(tmp_path / "ghost")

    # Act
    result = exists(path)

    # Assert
    actual = result
    expected = False
    assert actual == expected


# ============================================================================
# Testing join_path()
# ============================================================================


@pytest.mark.parametrize(
    "base, path, expected",
    [
        ("jobs", "mini.yaml", "jobs/mini.yaml"),
        ("jobs/", "mini.yaml", "jobs/mini.yaml"),
        ("s3://bucket/jobs", "mini.yaml", "s3://bucket/jobs/mini.yaml"),
        ("https://example.com/jobs", "mini.yaml", "https://example.com/jobs/mini.yaml"),
    ],
)
def test_join_path_should_prepend_base_to_relative_path(base: str, path: str, expected: str):
    # Arrange / Act
    result = join_path(base, path)

    # Assert
    actual = result
    assert actual == expected


@pytest.mark.parametrize(
    "path",
    [
        "/absolute/path/job.yaml",
        "s3://bucket/job.yaml",
        "http://example.com/job.yaml",
        "ftp://host/job.yaml",
        "sftp://host/job.yaml",
    ],
)
def test_join_path_should_return_path_unchanged_when_non_relative(path: str):
    # Arrange / Act
    result = join_path("jobs", path)

    # Assert
    actual = result
    expected = path
    assert actual == expected


def test_join_path_should_return_path_unchanged_when_already_starts_with_base():
    # Arrange / Act
    result = join_path("jobs", "jobs/mini.yaml")

    # Assert
    actual = result
    expected = "jobs/mini.yaml"
    assert actual == expected


@pytest.mark.parametrize(
    "base, path, expected",
    [
        (None, "mini.yaml", "mini.yaml"),
        ("jobs", None, "jobs"),
        (None, None, None),
    ],
)
def test_join_path_should_not_fail_when_either_argument_is_none(
    base: str | None, path: str | None, expected: str | None
):
    # Arrange / Act
    result = join_path(base, path)

    # Assert
    actual = result
    assert actual == expected
