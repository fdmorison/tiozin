from tiozin.api.metadata.secret.model import Secret
from tiozin.family.tio_kernel import EnvSecretRegistry

# ============================================================================
# __init__
# ============================================================================


def test_env_secret_registry_should_use_tiozin_uri_as_location_when_none_provided():
    # Arrange / Act
    registry = EnvSecretRegistry()

    # Assert
    actual = registry.location
    expected = registry.tiozin_uri
    assert actual == expected


# ============================================================================
# get()
# ============================================================================


def test_env_secret_registry_should_return_secret_when_envvar_exists(monkeypatch):
    # Arrange
    monkeypatch.setenv("DB_PASSWORD", "s3cr3t")
    registry = EnvSecretRegistry()

    # Act
    result = registry.get("DB_PASSWORD")

    # Assert
    actual = (
        result,
        isinstance(result, Secret),
    )
    expected = (
        "s3cr3t",
        True,
    )
    assert actual == expected


def test_env_secret_registry_should_return_none_when_envvar_missing(monkeypatch):
    # Arrange
    monkeypatch.delenv("MISSING_SECRET", raising=False)
    registry: EnvSecretRegistry = EnvSecretRegistry().__wrapped__.__wrapped__

    # Act
    result = registry.get("MISSING_SECRET")

    # Assert
    actual = result
    expected = None
    assert actual == expected


# ============================================================================
# register()
# ============================================================================


def test_env_secret_registry_should_set_envvar_on_register(monkeypatch):
    # Arrange
    monkeypatch.delenv("NEW_SECRET", raising=False)
    registry = EnvSecretRegistry()

    # Act
    registry.register("NEW_SECRET", Secret("newvalue"))

    # Assert
    result = registry.get("NEW_SECRET")
    actual = str(result)
    expected = "newvalue"
    assert actual == expected
