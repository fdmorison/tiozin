"""
Integration tests for TiozinApp - Custom Settings File.

These tests verify that TiozinApp correctly loads settings from a file
path provided at construction time via the `settings_file` parameter.

This is the primary mechanism for overriding the default settings location
at the CLI level (--settings-file flag) or programmatically.
"""

from unittest.mock import patch

from tiozin import TiozinApp

MOCK_SETTINGS = "tests/mocks/settings/default.yaml"
MOCK_JOB = "tests/mocks/jobs/default.yaml"


# ============================================================================
# settings_file
# ============================================================================
@patch("tiozin.app.signal")
@patch("tiozin.app.atexit")
def test_app_should_load_settings_from_custom_file(_atexit, _signal):
    """
    TiozinApp accepts a custom settings file path at construction time.

    When provided, the settings file is used as the source of registry
    configuration instead of the default discovery mechanism.
    This mirrors the behavior of the --settings-file CLI flag.
    """
    # Arrange
    app = TiozinApp(settings_file=MOCK_SETTINGS)

    # Act
    app.run(MOCK_JOB)
    app.teardown()

    # Assert
    actual = app.lifecycle.settings_registry.location
    expected = MOCK_SETTINGS
    assert actual == expected


# ============================================================================
# ENV template rendering in registry location
# ============================================================================
@patch("tiozin.app.signal")
@patch("tiozin.app.atexit")
def test_app_should_render_env_templates_in_registry_location(_atexit, _signal):
    """
    Registry ``location`` fields support ``{{ ENV.VAR }}`` templates.

    The RegistryProxy applies a TiozinTemplateOverlay during setup() so that
    environment variables are resolved before the registry initializes.
    The template string is restored after setup, so this test verifies
    that setup succeeds (rendering occurred) and the original template is preserved.
    """
    # Arrange
    env_template_settings = "tests/mocks/settings/env_template.yaml"
    app = TiozinApp(settings_file=env_template_settings)

    # Act: no exception means template rendering succeeded with the env var set
    with patch.dict("os.environ", {"TIO_TEST_JOB_LOCATION": "tests/mocks/jobs"}):
        app.run(MOCK_JOB)
        app.teardown()

    # Assert: setup completed and the job ran; original template is preserved post-setup
    assert app.status.is_completed()
    assert app.lifecycle.job_registry.location == "{{ ENV.TIO_TEST_JOB_LOCATION }}"
