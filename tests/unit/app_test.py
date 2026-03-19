from unittest.mock import MagicMock, patch

import pytest

import tiozin.app
from tiozin import Job, JobManifest
from tiozin.app import AppStatus, TiozinApp
from tiozin.exceptions import TiozinInternalError


def test_app_should_forward_settings_path_to_container():
    # Arrange / Act
    app = TiozinApp(settings_path="custom/tiozin.yaml")

    # Assert
    actual = app._containers.settings_path
    expected = "custom/tiozin.yaml"
    assert actual == expected


@pytest.fixture(scope="function", autouse=True)
def mock_signals():
    with patch("tiozin.app.signal") as mock_signal, patch("tiozin.app.atexit") as mock_atexit:
        yield mock_signal, mock_atexit


@pytest.fixture(scope="function", autouse=True)
def mock_context_for_job():
    with patch("tiozin.app.Context.for_job", return_value=MagicMock()) as mock:
        yield mock


@pytest.fixture(scope="function")
def created_app() -> TiozinApp:
    app = TiozinApp()
    app._containers = MagicMock()
    return app


@pytest.fixture(scope="function")
def ready_app(created_app: TiozinApp) -> TiozinApp:
    created_app._containers = MagicMock()
    created_app._status = AppStatus.READY
    return created_app


@patch.object(AppStatus, "set_booting")
def test_setup_should_leave_application_ready_when_success(
    set_booting: MagicMock, created_app: TiozinApp
):
    # Act
    created_app.setup()

    # Assert
    set_booting.assert_called_once()
    assert created_app._status.is_ready()


def test_setup_should_set_booting_before_initialization(created_app: TiozinApp):
    # Arrange
    actual_status: AppStatus = None

    def mocked_setup():
        nonlocal actual_status
        actual_status = created_app._status

    created_app._containers.setup.side_effect = mocked_setup

    # Act
    created_app.setup()

    # Assert
    assert actual_status.is_booting()


def test_setup_should_be_idempotent(created_app: TiozinApp):
    # Act
    created_app.setup()
    created_app.setup()

    # Assert
    created_app._containers.setup.assert_called_once()


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


def test_teardown_should_shutdown(ready_app: TiozinApp):
    # Act
    ready_app.teardown()

    # Assert
    ready_app._containers.teardown.assert_called()
    assert ready_app._status.is_shutdown()


def test_teardown_should_be_idempotent(ready_app: TiozinApp):
    # Act
    ready_app.teardown()
    ready_app.teardown()

    # Assert
    ready_app._containers.teardown.assert_called_once()


@patch.object(tiozin.app.Job, "builder")
def test_run_should_execute_job_and_return_result(job_builder: MagicMock, ready_app: TiozinApp):
    # Arrange
    job = MagicMock(spec=Job)
    job_builder.return_value.from_manifest.return_value.build.return_value = job

    # Act
    result = ready_app.run("job://test")

    # Assert
    job.submit.assert_called_once()
    assert result == [job.submit.return_value]


@patch.object(tiozin.app.Job, "builder")
def test_run_should_fail_and_propagate_exception(job_builder: MagicMock, ready_app: TiozinApp):
    # Arrange
    job = MagicMock(spec=Job)
    job.submit.side_effect = RuntimeError("boom")
    job_builder.return_value.from_manifest.return_value.build.return_value = job

    # Act - TiozinApp wraps unexpected exceptions in TiozinInternalError
    with pytest.raises(TiozinInternalError):
        ready_app.run("job://fail")


@patch.object(tiozin.app.Job, "builder")
def test_run_should_setup_app_lazily(job_builder: MagicMock, ready_app: TiozinApp):
    # Arrange
    ready_app.setup = MagicMock()
    job_builder.return_value.from_manifest.return_value.build.return_value = MagicMock(spec=Job)

    # Act
    ready_app.run("job://any")

    # Assert
    ready_app.setup.assert_called_once()


def test_run_should_accept_job_instance_directly(ready_app: TiozinApp):
    # Arrange
    job = MagicMock(spec=Job)
    job.name = "test_job"

    # Act
    result = ready_app.run(job)

    # Assert
    assert result == [job.submit.return_value]


@patch.object(tiozin.app.Job, "builder")
def test_run_should_accept_job_manifest_instance(job_builder: MagicMock, ready_app: TiozinApp):
    # Arrange
    manifest = JobManifest(
        kind="Job",
        name="test_job",
        org="tiozin",
        region="latam",
        domain="quality",
        subdomain="pipeline",
        product="test_cases",
        model="some_case",
        layer="test",
        runner={"kind": "TestRunner"},
        inputs=[{"kind": "TestInput", "name": "reader"}],
    )
    job = MagicMock(spec=Job)
    job_builder.return_value.from_manifest.return_value.build.return_value = job

    # Act
    result = ready_app.run(manifest)

    # Assert
    assert result == [job.submit.return_value]


@patch.object(tiozin.app.Job, "builder")
def test_run_should_accept_yaml_string(job_builder: MagicMock, ready_app: TiozinApp):
    # Arrange
    yaml_string = """
        kind: Job
        name: test_job
        description: Test job from YAML
    """
    job = MagicMock(spec=Job)
    job_builder.return_value.from_manifest.return_value.build.return_value = job

    # Act
    result = ready_app.run(yaml_string)

    # Assert
    assert result == [job.submit.return_value]


@patch.object(tiozin.app.Job, "builder")
def test_run_should_accept_json_string(job_builder: MagicMock, ready_app: TiozinApp):
    # Arrange
    json_string = """
        {
            "kind": "Job",
            "name": "test_job",
            "description": "Test job from JSON"
        }
    """
    job = MagicMock(spec=Job)
    job_builder.return_value.from_manifest.return_value.build.return_value = job

    # Act
    result = ready_app.run(json_string)

    # Assert
    assert result == [job.submit.return_value]


@patch.object(tiozin.app.Job, "builder")
def test_run_should_accept_identifier_string_from_registry(
    job_builder: MagicMock, ready_app: TiozinApp
):
    # Arrange
    ready_app._containers.job_registry.get.return_value = JobManifest(
        kind="Job",
        name="test_job",
        org="tiozin",
        region="latam",
        domain="quality",
        subdomain="pipeline",
        product="test_cases",
        model="some_case",
        layer="test",
        runner={"kind": "TestRunner"},
        inputs=[{"kind": "TestInput", "name": "reader"}],
    )
    job = MagicMock(spec=Job)
    job_builder.return_value.from_manifest.return_value.build.return_value = job

    # Act
    result = ready_app.run("job://registered_job")

    # Assert
    assert result == [job.submit.return_value]


@patch.object(tiozin.app.Job, "builder")
def test_run_should_accept_list_of_jobs(job_builder: MagicMock, ready_app: TiozinApp):
    # Arrange
    job_a = MagicMock(spec=Job)
    job_b = MagicMock(spec=Job)
    job_builder.return_value.from_manifest.return_value.build.side_effect = [job_a, job_b]

    # Act
    results = ready_app.run(["job://first", "job://second"])

    # Assert
    assert results == [job_a.submit.return_value, job_b.submit.return_value]


@patch.object(tiozin.app.Job, "builder")
def test_run_should_execute_list_sequentially(job_builder: MagicMock, ready_app: TiozinApp):
    # Arrange
    call_order = []

    job_a = MagicMock(spec=Job)
    job_a.submit.side_effect = lambda: call_order.append("a")

    job_b = MagicMock(spec=Job)
    job_b.submit.side_effect = lambda: call_order.append("b")

    job_builder.return_value.from_manifest.return_value.build.side_effect = [job_a, job_b]

    # Act
    ready_app.run(["job://first", "job://second"])

    # Assert
    assert call_order == ["a", "b"]
