import pytest

from tests.config import app_temp_workdir
from tiozin.utils.io import create_local_temp_dir


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
