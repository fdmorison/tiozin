"""
Integration tests for TiozinApp - Custom Settings Path.

These tests verify that TiozinApp correctly loads settings from a file
path provided at construction time via the `settings_path` parameter.

This is the primary mechanism for overriding the default settings location
at the CLI level (--settings-path flag) or programmatically.
"""

from unittest.mock import patch

from pytest import MonkeyPatch

from tiozin import TiozinApp

MOCK_SETTINGS = "tests/mocks/settings/default.yaml"
MOCK_JOB = "tests/mocks/jobs/default_job.yaml"


# ============================================================================
# settings_path
# ============================================================================
@patch("tiozin.app.signal")
@patch("tiozin.app.atexit")
def test_app_should_load_settings_from_custom_file(_atexit, _signal):
    """
    TiozinApp accepts a custom settings path at construction time.

    When provided, the settings path is used as the source of registry
    configuration instead of the default discovery mechanism.
    This mirrors the behavior of the --settings-path CLI flag.
    """
    # Arrange
    app = TiozinApp(settings_path=MOCK_SETTINGS)

    # Act
    app.run(MOCK_JOB)
    app.teardown()

    # Assert
    actual = app._containers.registries.setting.location
    expected = MOCK_SETTINGS
    assert actual == expected


# ============================================================================
# ENV template rendering in registry location
# ============================================================================
@patch("tiozin.app.signal")
@patch("tiozin.app.atexit")
def test_app_should_render_env_templates_in_registry_location(
    _atexit, _signal, monkeypatch: MonkeyPatch
):
    """
    Registry `location` fields support `{{ ENV.VAR }}` templates.

    The RegistryProxy renders env templates during setup() and restores the
    original string on teardown(). This test verifies both: that `location`
    holds the rendered value while the registry is active, and that the
    original template is restored after teardown.
    """
    # Arrange
    monkeypatch.setenv("TEST_VALUE", "tests/mocks/jobs")
    env_template_settings = "tests/mocks/settings/env_template.yaml"
    app = TiozinApp(settings_path=env_template_settings)

    # Act
    app.setup()
    app.run(MOCK_JOB)
    rendered = app._containers.registries.job.location
    app.teardown()
    restored = app._containers.registries.job.location

    # Assert
    actual = (
        rendered,
        restored,
    )
    expected = (
        "tests/mocks/jobs",
        "{{ ENV.TEST_VALUE }}",
    )
    assert actual == expected
