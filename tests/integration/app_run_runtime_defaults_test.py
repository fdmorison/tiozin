"""
Integration tests for TiozinApp - Runtime Defaults.

These tests verify that plugins loaded during job construction receive
default argument values declared in the settings file under runtime_defaults,
even when those arguments are not explicitly provided at the call site.
"""

from unittest.mock import patch

import pytest

from tiozin import Job, TiozinApp
from tiozin.compose.assembly.tiozin_registry import tiozin_registry

MOCK_SETTINGS = "tests/mocks/settings/runtime_defaults.yaml"


@pytest.fixture(autouse=True)
def reset_registry_defaults():
    yield
    tiozin_registry._defaults.clear()


# ============================================================================
# runtime_defaults
# ============================================================================
@patch("tiozin.app.signal")
@patch("tiozin.app.atexit")
def test_app_should_apply_runtime_defaults_to_job_plugins(_atexit, _signal):
    # Arrange
    app = TiozinApp(settings_path=MOCK_SETTINGS)
    app.setup()

    # Act
    job = (
        Job.builder()
        .with_kind("LinearJob")
        .with_name("test_job")
        .with_org("acme")
        .with_region("latam")
        .with_domain("sales")
        .with_subdomain("retail")
        .with_layer("raw")
        .with_product("orders")
        .with_model("daily")
        .with_runner({"kind": "NoOpRunner"})
        .with_inputs({"kind": "NoOpInput", "name": "test_input"})
        .build()
    )
    app.teardown()

    # Assert
    actual = (
        job.inputs[0].verbose,
        job.inputs[0].schema_subject,
        job.inputs[0].options.get("other_field"),
    )
    expected = (
        False,
        "{{ domain }}.{{ subdomain }}.{{ product }}",
        12345,
    )
    assert actual == expected
