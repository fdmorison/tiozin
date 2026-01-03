from unittest.mock import MagicMock, patch

import pytest

import tiozin.app
from tests.mocks.fake_registry_factory import MockedRegistryFactory
from tiozin.app import AppStatus, TiozinApp


@pytest.fixture(scope="function", autouse=True)
def mock_signals():
    with patch("tiozin.app.signal") as mock_signal, patch("tiozin.app.atexit") as mock_atexit:
        yield mock_signal, mock_atexit


@pytest.fixture(scope="function")
def created_app() -> TiozinApp:
    app = TiozinApp(registries=MockedRegistryFactory())
    app.lifecycle = MagicMock()
    app.job_registry = MagicMock()
    return app


@pytest.fixture(scope="function")
def ready_app(created_app: TiozinApp) -> TiozinApp:
    created_app.lifecycle = MagicMock()
    created_app.status = AppStatus.WAITING
    return created_app


@pytest.fixture
def running_app(created_app: TiozinApp) -> TiozinApp:
    created_app.current_job = MagicMock()
    created_app.status = AppStatus.RUNNING
    return created_app


@patch.object(AppStatus, "set_booting")
def test_setup_should_leave_application_ready_when_success(
    set_booting: MagicMock, created_app: TiozinApp
):
    # Act
    created_app.setup()

    # Assert
    set_booting.assert_called_once()
    assert created_app.status.is_waiting()
    assert created_app.status.is_healthy()
    assert created_app.status.is_ready()
    assert created_app.status.is_idle()


def test_setup_should_fail_and_propagate_exception(created_app: TiozinApp):
    # Arrange
    created_app.lifecycle.setup.side_effect = RuntimeError("boom")

    # Act
    with pytest.raises(RuntimeError, match="boom"):
        created_app.setup()

    # Assert
    assert created_app.status.is_failure()
    assert not created_app.status.is_healthy()
    assert created_app.status.is_ready()
    assert created_app.status.is_idle()
    assert created_app.status.is_job_finished()


def test_setup_should_set_booting_before_initialization(created_app: TiozinApp):
    # Arrange
    actual_status: AppStatus = None

    def mocked_setup():
        nonlocal actual_status
        actual_status = created_app.status

    created_app.lifecycle.setup.side_effect = mocked_setup

    # Act
    created_app.setup()

    # Assert
    assert actual_status.is_booting()


def test_setup_should_be_idempotent(created_app: TiozinApp):
    # Act
    created_app.setup()
    created_app.setup()

    # Assert
    created_app.lifecycle.setup.assert_called_once()


def test_setup_should_install_shutdown_hooks(
    created_app: TiozinApp, mock_signals: tuple[MagicMock, ...]
):
    # Arrange
    mock_signal, mock_atexit = mock_signals

    # Act
    created_app.setup()

    # Assert
    actual = set([call[0][0] for call in mock_signal.signal.call_args_list])
    expected = {
        mock_signal.SIGTERM,
        mock_signal.SIGINT,
        mock_signal.SIGHUP,
    }
    assert actual == expected
    mock_atexit.register.assert_called_once_with(created_app.teardown)


def test_teardown_should_terminate(ready_app: TiozinApp):
    # Act
    ready_app.teardown()

    # Assert
    ready_app.lifecycle.teardown.assert_called()
    assert ready_app.status.is_completed()


def test_teardown_should_cancel_running_job(running_app: TiozinApp):
    # Act
    running_app.teardown()

    # Assert
    running_app.current_job.teardown.assert_called_once()
    assert running_app.status.is_canceled()


def test_teardown_should_be_idempotent(running_app: TiozinApp):
    # Act
    running_app.teardown()
    running_app.teardown()

    # Assert
    running_app.lifecycle.teardown.assert_called_once()


@patch.object(tiozin.app.Job, "builder")
def test_run_should_execute_job_and_finish_with_success(
    job_builder: MagicMock, ready_app: TiozinApp
):
    # Arrange
    job = MagicMock()
    job_builder.return_value.from_manifest.return_value.build.return_value = job

    # Act
    ready_app.run("job://test")

    # Assert
    job.execute.assert_called_once()
    assert ready_app.status.is_success()
    assert ready_app.status.is_job_finished()


@patch.object(tiozin.app.Job, "builder")
def test_run_should_fail_and_propagate_exception(job_builder: MagicMock, ready_app: TiozinApp):
    # Arrange
    job = MagicMock()
    job.execute.side_effect = RuntimeError("boom")
    job_builder.return_value.from_manifest.return_value.build.return_value = job

    # Act
    with pytest.raises(RuntimeError, match="boom"):
        ready_app.run("job://fail")

    # Assert
    assert ready_app.status.is_failure()
    assert ready_app.status.is_ready()
    assert ready_app.status.is_job_finished()


@patch.object(tiozin.app.Job, "builder")
def test_run_should_set_running_before_job_execution(job_builder: MagicMock, ready_app: TiozinApp):
    # Arrange
    actual_status: AppStatus = None

    def mocked_job_run(_):
        nonlocal actual_status
        actual_status = ready_app.status

    job = MagicMock()
    job.execute.side_effect = mocked_job_run
    job_builder.return_value.from_manifest.return_value.build.return_value = job

    # Act
    ready_app.run("job://test")

    # Assert
    assert actual_status.is_running()


@patch.object(tiozin.app.Job, "builder")
def test_run_should_setup_app_lazily(job_builder: MagicMock, ready_app: TiozinApp):
    # Arrange
    ready_app.setup = MagicMock()

    # Act
    ready_app.run("job://any")

    # Assert
    ready_app.setup.assert_called_once()
