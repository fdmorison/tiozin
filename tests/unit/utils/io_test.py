from pathlib import Path

import pytest

from tests.config import app_temp_workdir
from tiozin.utils import io


# ============================================================================
# Testing io.create_local_temp_dir()
# ============================================================================
def test_create_local_temp_dir_should_create_directory():
    # Act
    dir = io.create_local_temp_dir("my_job")

    # Assert
    actual = dir
    expected = app_temp_workdir / "my_job"
    assert actual == expected
    assert dir.is_dir()


def test_create_local_temp_dir_should_create_subdirectories():
    # Act
    dir = io.create_local_temp_dir("job_name", "run_id", "step_name")

    # Assert
    actual = dir
    expected = app_temp_workdir / "job_name" / "run_id" / "step_name"
    assert actual == expected
    assert dir.is_dir()


@pytest.mark.parametrize(
    "entry",
    ["", None],
)
def test_create_local_temp_dir_should_skip_unset_entries(entry: str):
    # Arrange
    expected = app_temp_workdir / "job_name" / "step_name"

    # Act
    io.create_local_temp_dir("job_name", entry, "step_name")

    # Assert
    assert expected.exists()


def test_create_local_temp_dir_should_return_app_temp_dir_when_no_entries():
    # Act
    dir = io.create_local_temp_dir()

    # Assert
    actual = dir
    expected = app_temp_workdir
    assert actual == expected


def test_create_local_temp_dir_should_be_idempotent():
    # Arrange
    expected = app_temp_workdir / "my_job" / "run_123"

    # Act
    io.create_local_temp_dir("my_job", "run_123")
    io.create_local_temp_dir("my_job", "run_123")

    # Assert
    assert expected.exists()


def test_create_local_temp_dir_should_accept_path_as_first_entry():
    # Arrange
    base_path = app_temp_workdir / "existing_job"
    expected = base_path / "step_name"

    # Act
    io.create_local_temp_dir(base_path, "step_name")

    # Assert
    assert expected.exists()


# ============================================================================
# Testing io.write_text() / io.read_text()
# ============================================================================
@pytest.mark.parametrize("path_type", [str, Path])
def test_write_text_should_write_content_to_file(tmp_path: Path, path_type: type[str] | Path):
    # Arrange
    file = tmp_path / "out.txt"
    path = path_type(file)

    # Act
    io.write_text(path, "hello")

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
    result = io.read_text(path)

    # Assert
    actual = result
    expected = "world"
    assert actual == expected


# ============================================================================
# Testing io.mkdirs()
# ============================================================================
@pytest.mark.parametrize("path_type", [str, Path])
def test_mkdirs_should_create_directory(tmp_path: Path, path_type: type[str] | Path):
    # Arrange
    target = tmp_path / "new_dir"
    path = path_type(target)

    # Act
    io.mkdirs(path)

    # Assert
    assert target.is_dir()


@pytest.mark.parametrize("path_type", [str, Path])
def test_mkdirs_should_not_fail_when_directory_already_exists(
    tmp_path: Path, path_type: type[str] | Path
):
    # Arrange
    target = tmp_path / "existing_dir"
    target.mkdir()
    path = path_type(target)

    # Act
    io.mkdirs(path)

    # Assert
    assert target.is_dir()


# ============================================================================
# Testing io.remove()
# ============================================================================
@pytest.mark.parametrize("path_type", [str, Path])
def test_remove_should_delete_directory(tmp_path: Path, path_type: type[str] | Path):
    # Arrange
    target = tmp_path / "to_remove"
    target.mkdir()
    (target / "file.txt").write_text("data")
    path = path_type(target)

    # Act
    io.remove(path, recursive=True)

    # Assert
    assert not target.exists()


@pytest.mark.parametrize("path_type", [str, Path])
def test_remove_should_delete_file(tmp_path: Path, path_type: type[str] | Path):
    # Arrange
    target = tmp_path / "file.txt"
    target.write_text("data")
    path = path_type(target)

    # Act
    io.remove(path)

    # Assert
    assert not target.exists()


@pytest.mark.parametrize("path_type", [str, Path])
def test_remove_should_be_noop_when_path_does_not_exist(
    tmp_path: Path, path_type: type[str] | Path
):
    # Arrange
    ghost = tmp_path / "ghost"
    path = path_type(ghost)

    # Act
    io.remove(path)

    # Assert
    assert not ghost.exists()


# ============================================================================
# Testing io.clear_dir()
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
    io.clear_dir(path)

    # Assert
    actual = list(target.iterdir())
    expected = []
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
    io.clear_dir(path)

    # Assert
    actual = list(target.iterdir())
    expected = []
    assert actual == expected


@pytest.mark.parametrize("path_type", [str, Path])
def test_clear_dir_should_raise_when_path_is_a_file(tmp_path: Path, path_type: type[str] | Path):
    # Arrange
    target = tmp_path / "file.txt"
    target.write_text("data")
    path = path_type(target)

    # Act / Assert
    with pytest.raises(ValueError, match="Not a directory"):
        io.clear_dir(path)


# ============================================================================
# Testing io.exists()
# ============================================================================
@pytest.mark.parametrize("path_type", [str, Path])
def test_exists_should_return_true_when_path_exists(tmp_path: Path, path_type: type[str] | Path):
    # Arrange
    path = path_type(tmp_path)

    # Act
    result = io.exists(path)

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
    result = io.exists(path)

    # Assert
    actual = result
    expected = False
    assert actual == expected


# ============================================================================
# Testing io.join_path()
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
    # Act
    result = io.join_path(base, path)

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
    # Act
    result = io.join_path("jobs", path)

    # Assert
    actual = result
    expected = path
    assert actual == expected


def test_join_path_should_return_path_unchanged_when_already_starts_with_base():
    # Act
    result = io.join_path("jobs", "jobs/mini.yaml")

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
    # Act
    result = io.join_path(base, path)

    # Assert
    actual = result
    assert actual == expected


# ============================================================================
# Testing io.normalize_uri()
# ============================================================================
@pytest.mark.parametrize("path_type", [str, Path])
def test_normalize_uri_should_accept_str_and_path(path_type: type[str] | Path):
    # Act
    result = io.normalize_uri(path_type("/absolute/local/file.csv"), as_absolute=True)

    # Assert
    actual = result
    expected = "file:///absolute/local/file.csv"
    assert actual == expected


@pytest.mark.parametrize(
    "uri",
    [
        "http://example.com/data/file.csv",
        "https://example.com/data/file.csv",
        "s3://my-bucket/data/file.parquet",
        "gs://my-bucket/data/file.parquet",
        "az://my-container/data/file.parquet",
        "ftp://host.example.com/data/file.csv",
        "sftp://host.example.com/data/file.csv",
        "file:///absolute/local/file.csv",
    ],
)
def test_normalize_uri_should_return_uri_unchanged_when_scheme_is_present(uri: str):
    # Act
    result = io.normalize_uri(uri)

    # Assert
    actual = result
    expected = uri
    assert actual == expected


def test_normalize_uri_should_return_file_uri_when_absolute_path(tmp_path: Path):
    # Act
    result = io.normalize_uri(tmp_path / "file.csv", as_absolute=True)

    # Assert
    actual = result
    expected = f"file://{tmp_path}/file.csv"
    assert actual == expected


def test_normalize_uri_should_resolve_relative_path_to_absolute_file_uri(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    # Arrange
    monkeypatch.chdir(tmp_path)

    # Act
    result = io.normalize_uri("data/file.csv", as_absolute=True)

    # Assert
    actual = result
    expected = f"file://{tmp_path}/data/file.csv"
    assert actual == expected


def test_normalize_uri_should_expand_tilde_when_path_starts_with_home(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    # Arrange
    monkeypatch.setenv("HOME", str(tmp_path))

    # Act
    result = io.normalize_uri("~/data/file.csv", as_absolute=True)

    # Assert
    actual = result
    expected = f"file://{tmp_path}/data/file.csv"
    assert actual == expected


@pytest.mark.parametrize(
    "uri, expected",
    [
        ("s3://my-bucket/data/shakespeare/*.txt", "s3://my-bucket/data/shakespeare"),
        ("gs://my-bucket/logs/**/*.parquet", "gs://my-bucket/logs/**"),
        ("s3://my-bucket/data/orders/", "s3://my-bucket/data/orders"),
    ],
    ids=["s3-glob", "gs-double-star-glob", "s3-trailing-slash"],
)
def test_normalize_uri_should_strip_glob_and_trailing_slash_when_scheme_is_present(
    uri: str, expected: str
):
    # Act
    result = io.normalize_uri(uri, strip_glob=True)

    # Assert
    actual = result
    assert actual == expected


@pytest.mark.parametrize(
    "uri, expected",
    [
        ("examples/data/shakespeare/*.txt", "examples/data/shakespeare"),
        ("logs/**/*.parquet", "logs/**"),
        ("data/orders/", "data/orders"),
    ],
    ids=["local-glob", "local-double-star-glob", "local-trailing-slash"],
)
def test_normalize_uri_should_strip_glob_and_trailing_slash_when_absolute_is_false(
    uri: str, expected: str
):
    # Act
    result = io.normalize_uri(uri, strip_glob=True)

    # Assert
    actual = result
    assert actual == expected


def test_normalize_uri_should_strip_glob_before_resolving_absolute_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    # Arrange
    monkeypatch.chdir(tmp_path)

    # Act
    result = io.normalize_uri("data/shakespeare/*.txt", as_absolute=True, strip_glob=True)

    # Assert
    actual = result
    expected = f"file://{tmp_path}/data/shakespeare"
    assert actual == expected


@pytest.mark.parametrize(
    "uri, expected",
    [
        (
            "s3://my-bucket/data/orders/year=2024/month=01",
            "s3://my-bucket/data/orders",
        ),
        (
            "data/orders/year=2024/month=01",
            "data/orders",
        ),
        (
            "s3://my-bucket/data/orders/year=2024/month=01/*.parquet",
            "s3://my-bucket/data/orders",
        ),
    ],
    ids=["s3-partitions", "local-partitions", "s3-partitions-and-glob"],
)
def test_normalize_uri_should_strip_hive_partition_segments(uri: str, expected: str):
    # Act
    result = io.normalize_uri(uri, strip_glob=True, strip_partitions=True)

    # Assert
    actual = result
    assert actual == expected


def test_normalize_uri_should_strip_trailing_slash_before_resolving_absolute_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    # Arrange
    monkeypatch.chdir(tmp_path)

    # Act
    result = io.normalize_uri("data/orders/", as_absolute=True)

    # Assert
    actual = result
    expected = f"file://{tmp_path}/data/orders"
    assert actual == expected
