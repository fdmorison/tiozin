"""
Integration tests for TiozinApp - Log Security.

These tests ensure that sensitive information (local variables) is NOT exposed
in exception tracebacks by default.

This is a security concern because local variables may contain secrets such as
API keys, passwords, database credentials, or tokens. If show_locals is
misconfigured, these secrets could be leaked in logs, CI outputs, or monitoring
systems.

The TIO_LOG_SHOW_LOCALS environment variable (via ``config.log_show_locals``)
controls this behavior and defaults to False for safety. It is consumed by the
``LogService`` RichTracebackFormatter, which renders the exception traceback
when a failing job is logged.
"""

from unittest.mock import patch

import pytest

from tiozin import TiozinApp
from tiozin.logs.service import LogService

SENSITIVE_JOB = "tests/mocks/jobs/sensitive_job.yaml"

# Must match the api_key value declared in the sensitive_job.yaml mock.
FAKE_SECRET = "secret123"

# The raised error message always appears in the rendered traceback, regardless
# of show_locals, so it guards against asserting over an empty capture.
TRACEBACK_MARKER = "Forced error for testing purposes"


@patch("tiozin.app.signal")
@patch("tiozin.app.atexit")
@patch("tiozin.logs.log_service", new_callable=lambda: LogService(propagate=True))
@patch("tiozin.config.log_show_locals", False)
def test_app_logs_should_not_expose_secrets(
    log_service: LogService,
    _atexit,
    _signal,
    caplog: pytest.LogCaptureFixture,
) -> None:
    # Arrange
    log_service.setup()
    app = TiozinApp()

    # Act
    try:
        app.run(SENSITIVE_JOB)
    except RuntimeError:
        app.exception("Unexpected error while running job")
    finally:
        app.teardown()

    # Assert
    traceback = caplog.text
    actual = (
        TRACEBACK_MARKER in traceback,
        FAKE_SECRET in traceback,
    )
    expected = (True, False)
    assert actual == expected


@patch("tiozin.app.signal")
@patch("tiozin.app.atexit")
@patch("tiozin.logs.log_service", new_callable=lambda: LogService(propagate=True))
@patch("tiozin.config.log_show_locals", True)
def test_app_logs_should_expose_secrets_when_show_locals_enabled(
    log_service: LogService,
    _atexit,
    _signal,
    caplog: pytest.LogCaptureFixture,
) -> None:
    # Arrange
    log_service.setup()
    app = TiozinApp()

    # Act
    try:
        app.run(SENSITIVE_JOB)
    except RuntimeError:
        app.exception("Unexpected error while running job")
    finally:
        app.teardown()

    # Assert
    traceback = caplog.text
    actual = (
        TRACEBACK_MARKER in traceback,
        FAKE_SECRET in traceback,
    )
    expected = (True, True)
    assert actual == expected
