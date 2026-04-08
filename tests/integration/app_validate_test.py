"""
Integration tests for TiozinApp - Job Validation.

These tests demonstrate how to validate job definitions using TiozinApp.validate
without submitting them for execution.

Validation is useful for:
- CI/CD pipelines that need to catch manifest errors before deploying
- Linting job files during code review
- Pre-flight checks before running expensive compute workloads

This file focuses exclusively on validate behavior and does not cover:
- Job execution (app.run)
- Job construction APIs (builder, programmatic)
"""

from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from tiozin import TiozinApp
from tiozin.exceptions import TiozinUsageError

JOBS_DIR = Path("tests/mocks/jobs")


@pytest.fixture
def app() -> Generator[TiozinApp, Any, None]:
    app = TiozinApp()
    yield app
    app.teardown()


# ============================================================================
# Validate – File-Based Job
# ============================================================================
@patch("tiozin.app.signal")
@patch("tiozin.app.atexit")
def test_validate_should_succeed_when_job_file_is_valid(_atexit, _signal, app: TiozinApp):
    """
    A job manifest loaded from a well-formed YAML file must pass validation.
    """
    # Arrange
    path = str(JOBS_DIR / "default_job.yaml")

    # Act
    result = app.validate(path)

    # Assert
    actual = result
    expected = None
    assert actual == expected


# ============================================================================
# Validate – Multiple Jobs
# ============================================================================
@patch("tiozin.app.signal")
@patch("tiozin.app.atexit")
def test_validate_should_succeed_for_multiple_job_files(_atexit, _signal, app: TiozinApp):
    """
    Multiple job manifests can be validated in a single call.
    All must be valid for the call to succeed.
    """
    # Arrange
    path = str(JOBS_DIR / "default_job.yaml")

    # Act
    result = app.validate(path, path)

    # Assert
    actual = result
    expected = None
    assert actual == expected


# ============================================================================
# Validate – Invalid Manifest
# ============================================================================
@patch("tiozin.app.signal")
@patch("tiozin.app.atexit")
def test_validate_should_fail_when_manifest_is_missing_required_fields(
    _atexit, _signal, app: TiozinApp
):
    """
    A job manifest with missing required fields must raise a usage error.
    """
    # Arrange
    path = str(JOBS_DIR / "invalid.yaml")

    # Act / Assert
    with pytest.raises(TiozinUsageError):
        app.validate(path)


# ============================================================================
# Validate – Non-existent File
# ============================================================================
@patch("tiozin.app.signal")
@patch("tiozin.app.atexit")
def test_validate_should_fail_when_identifier_does_not_exist(_atexit, _signal, app: TiozinApp):
    """
    A job identifier that cannot be resolved must raise a usage error.
    This is the expected behavior for CI/CD pipelines that reference
    non-existent or mistyped job identifiers.
    """
    # Arrange
    path = str(JOBS_DIR / "does_not_exist.yaml")

    # Act / Assert
    with pytest.raises(TiozinUsageError):
        app.validate(path)
