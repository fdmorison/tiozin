from pathlib import Path

from pytest import MonkeyPatch

from tiozin.utils.io import create_local_temp_dir


# ============================================================================
# Testing create_local_temp_dir()
# ============================================================================
def test_create_local_temp_dir_should_create_directory_with_single_entry(
    tmp_path: Path, monkeypatch: MonkeyPatch
):
    # Arrange
    monkeypatch.setattr("tiozin.utils.helpers.config.app_temp_workdir", tmp_path)

    # Act
    result = create_local_temp_dir("my_job")

    # Assert
    actual = result
    expected = tmp_path / "my_job"
    assert actual == expected
    assert actual.exists()
    assert actual.is_dir()


def test_create_local_temp_dir_should_create_nested_directory_with_multiple_entries(
    tmp_path, monkeypatch
):
    # Arrange
    monkeypatch.setattr("tiozin.utils.helpers.config.app_temp_workdir", tmp_path)

    # Act
    result = create_local_temp_dir("job_name", "run_id", "step_name")

    # Assert
    actual = result
    expected = tmp_path / "job_name" / "run_id" / "step_name"
    assert actual == expected
    assert actual.exists()
    assert actual.is_dir()


def test_create_local_temp_dir_should_skip_empty_entries(tmp_path: Path, monkeypatch: MonkeyPatch):
    # Arrange
    monkeypatch.setattr("tiozin.utils.helpers.config.app_temp_workdir", tmp_path)

    # Act
    result = create_local_temp_dir("job_name", "", "step_name")

    # Assert
    actual = result
    expected = tmp_path / "job_name" / "step_name"
    assert actual == expected


def test_create_local_temp_dir_should_skip_none_entries(tmp_path: Path, monkeypatch: MonkeyPatch):
    # Arrange
    monkeypatch.setattr("tiozin.utils.helpers.config.app_temp_workdir", tmp_path)

    # Act
    result = create_local_temp_dir("job_name", None, "step_name")

    # Assert
    actual = result
    expected = tmp_path / "job_name" / "step_name"
    assert actual == expected


def test_create_local_temp_dir_should_return_base_path_when_no_entries(
    tmp_path: Path, monkeypatch: MonkeyPatch
):
    # Arrange
    monkeypatch.setattr("tiozin.utils.helpers.config.app_temp_workdir", tmp_path)

    # Act
    result = create_local_temp_dir()

    # Assert
    actual = result
    expected = tmp_path
    assert actual == expected


def test_create_local_temp_dir_should_be_idempotent(tmp_path: Path, monkeypatch: MonkeyPatch):
    # Arrange
    monkeypatch.setattr("tiozin.utils.helpers.config.app_temp_workdir", tmp_path)

    # Act
    first_call = create_local_temp_dir("my_job", "run_123")
    second_call = create_local_temp_dir("my_job", "run_123")

    # Assert
    actual = first_call
    expected = second_call
    assert actual == expected
    assert actual.exists()


def test_create_local_temp_dir_should_accept_path_as_first_entry(
    tmp_path: Path, monkeypatch: MonkeyPatch
):
    # Arrange
    monkeypatch.setattr("tiozin.utils.helpers.config.app_temp_workdir", tmp_path)
    base_path = tmp_path / "existing_job"
    base_path.mkdir()

    # Act
    result = create_local_temp_dir(base_path, "step_name")

    # Assert
    actual = result
    expected = base_path / "step_name"
    assert actual == expected
    assert actual.exists()
