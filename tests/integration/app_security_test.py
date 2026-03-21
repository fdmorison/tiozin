"""
Integration tests for TiozinApp - Log Security.

These tests ensure that sensitive information (local variables) is NOT exposed
in exception tracebacks by default.

This is a security concern because local variables may contain secrets such as
API keys, passwords, database credentials, or tokens. If show_locals is
misconfigured, these secrets could be leaked in logs, CI outputs, or monitoring
systems.

The TIO_LOG_SHOW_LOCALS environment variable controls this behavior and defaults
to False for safety.
"""

from unittest.mock import patch

import pytest

from tiozin import TiozinApp
from tiozin.exceptions import TiozinInternalError
from tiozin.family.tio_kernel import LinearJob, NoOpInput, NoOpRunner, NoOpTransform
from tiozin.logs.service import LogService


@pytest.fixture
def app_secure():
    with (
        patch("tiozin.config.log_show_locals", False),
        patch("tiozin.logs.log_service", LogService(propagate=True)) as mock_log_service,
    ):
        mock_log_service.setup()
        app = TiozinApp()
        yield app
        app.teardown()


@pytest.fixture
def app_insecure():
    with (
        patch("tiozin.config.log_show_locals", True),
        patch("tiozin.logs.log_service", LogService(propagate=True)) as mock_log_service,
    ):
        mock_log_service.setup()
        app = TiozinApp()
        yield app
        app.teardown()


@patch("tiozin.app.signal")
@patch("tiozin.app.atexit")
def test_exception_traceback_should_not_expose_local_variables(
    _atexit, _signal, app_secure: TiozinApp, capsys: pytest.CaptureFixture[str]
) -> None:
    # Arrange
    fake_secret = "secret123"

    job = LinearJob(
        kind="LinearJob",
        name="failing_job",
        org="tiozin",
        region="latam",
        domain="test",
        subdomain="verification",
        product="security",
        model="log_check",
        layer="raw",
        runner=NoOpRunner(),
        inputs=[
            NoOpInput(name="source"),
        ],
        transforms=[
            NoOpTransform(name="will_fail", force_error=True, api_key=fake_secret),
        ],
    )

    # Act
    with pytest.raises(TiozinInternalError):
        app_secure.run(job)

    # Assert
    actual = fake_secret in capsys.readouterr().out
    expected = False
    assert actual == expected


@patch("tiozin.app.signal")
@patch("tiozin.app.atexit")
def test_exception_traceback_should_expose_local_variables(
    _atexit,
    _signal,
    app_insecure: TiozinApp,
    caplog: pytest.LogCaptureFixture,
) -> None:
    # Arrange
    fake_secret = "secret123"

    job = LinearJob(
        kind="LinearJob",
        name="failing_job",
        org="tiozin",
        region="latam",
        domain="test",
        subdomain="verification",
        product="security",
        model="log_check",
        layer="raw",
        runner=NoOpRunner(),
        inputs=[
            NoOpInput(name="source"),
        ],
        transforms=[
            NoOpTransform(name="will_fail", force_error=True, api_key=fake_secret),
        ],
    )

    # Act
    with pytest.raises(TiozinInternalError):
        app_insecure.run(job)

    # Assert
    assert fake_secret in caplog.text
