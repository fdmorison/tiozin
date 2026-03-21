"""
Integration tests for TiozinApp - Secret Template Variables.

These tests verify that TiozinApp correctly resolves secrets from the
SecretRegistry during YAML template rendering, using both the attribute
syntax (``SECRET.NAME``) and the item syntax (``SECRET["path/name"]``).

The active registry is EnvSecretRegistry (set in ``tests/env.py``), so
secrets are backed by environment variables in these tests.
"""

from unittest.mock import patch

import pytest

from tiozin import TiozinApp
from tiozin.exceptions import TiozinInputError

MOCK_SETTINGS = "tests/mocks/settings/default.yaml"


@pytest.fixture
def app():
    app = TiozinApp(MOCK_SETTINGS)
    yield app
    app.teardown()


# ============================================================================
# Attribute syntax – SECRET.NAME
# ============================================================================
@patch("tiozin.app.signal")
@patch("tiozin.app.atexit")
def test_app_should_render_secret_attribute_syntax(
    _atexit, _signal, app: TiozinApp, monkeypatch: pytest.MonkeyPatch
):
    """
    Secrets are accessible in templates via attribute syntax: ``SECRET.NAME``.

    The secret value is read from the environment variable matching the
    identifier exactly (case-sensitive).
    """
    # Arrange
    monkeypatch.setenv("DB_PASSWORD", "s3cr3t")

    yaml_job = """
        kind: LinearJob
        name: secret_attr_job
        org: tiozin
        region: latam
        domain: data
        subdomain: platform
        product: noop
        model: noop
        layer: refined
        runner:
          kind: NoOpRunner
          password: "{{ SECRET.DB_PASSWORD }}"
        inputs:
          - kind: NoOpInput
            name: noop_input
        outputs:
          - kind: NoOpOutput
            name: noop_output
    """

    # Act / Assert: no exception means the secret resolved successfully
    app.run(yaml_job)


# ============================================================================
# Item syntax – SECRET["path/name"]
# ============================================================================
@patch("tiozin.app.signal")
@patch("tiozin.app.atexit")
def test_app_should_render_secret_item_syntax(_atexit, _signal, app: TiozinApp, monkeypatch):
    """
    Secrets with path-based identifiers are accessible via item syntax:
    ``SECRET["env/app/name"]``.

    Use this syntax when the identifier contains characters that are not
    valid Python attribute names, such as slashes.
    """
    # Arrange
    monkeypatch.setenv("env/app/db_password", "s3cr3t")

    yaml_job = """
        kind: LinearJob
        name: secret_item_job
        org: tiozin
        region: latam
        domain: data
        subdomain: platform
        product: noop
        model: noop
        layer: refined
        runner:
          kind: NoOpRunner
          password: '{{ SECRET["env/app/db_password"] }}'
        inputs:
          - kind: NoOpInput
            name: noop_input
        outputs:
          - kind: NoOpOutput
            name: noop_output
    """

    # Act / Assert: no exception means the secret resolved successfully
    app.run(yaml_job)


# ============================================================================
# Missing secret raises
# ============================================================================
@patch("tiozin.app.signal")
@patch("tiozin.app.atexit")
def test_app_should_raise_when_secret_is_missing(_atexit, _signal, app: TiozinApp, monkeypatch):
    """
    Referencing a secret that does not exist in the registry raises an error
    during template rendering.

    Missing secrets fail loudly so misconfigured jobs are caught early.
    """
    # Arrange
    monkeypatch.delenv("DB_PASSWORD", raising=False)

    yaml_job = """
        kind: LinearJob
        name: missing_secret_job
        org: tiozin
        region: latam
        domain: data
        subdomain: platform
        product: noop
        model: noop
        layer: refined
        runner:
          kind: NoOpRunner
          password: "{{ SECRET.DB_PASSWORD }}"
        inputs:
          - kind: NoOpInput
            name: noop_input
        outputs:
          - kind: NoOpOutput
            name: noop_output
    """

    # Act / Assert
    with pytest.raises(TiozinInputError):
        app.run(yaml_job)
