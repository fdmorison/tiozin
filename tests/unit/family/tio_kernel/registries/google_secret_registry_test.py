from unittest.mock import MagicMock, call, patch

import pytest
from google.api_core.exceptions import AlreadyExists, NotFound

from tiozin.api.metadata.secret.model import Secret
from tiozin.exceptions import SecretNotFoundError
from tiozin.family.tio_kernel import GoogleSecretRegistry

# ============================================================================
# setup()
# ============================================================================


@patch("google.cloud.secretmanager.SecretManagerServiceClient")
def test_setup_should_create_client_without_options_when_location_is_not_set(client: MagicMock):
    # Arrange
    registry = GoogleSecretRegistry(project_id="my-project")

    # Act
    registry.setup()

    # Assert
    client.assert_called_once_with()


@patch("google.cloud.secretmanager.SecretManagerServiceClient")
def test_setup_should_create_client_with_api_endpoint_when_location_is_set(client: MagicMock):
    # Arrange
    registry = GoogleSecretRegistry(
        project_id="my-project",
        location="http://localhost:6174",
    )

    # Act
    registry.setup()

    # Assert
    client.assert_called_once_with(client_options={"api_endpoint": "http://localhost:6174"})


# ============================================================================
# get()
# ============================================================================


@patch("google.cloud.secretmanager.SecretManagerServiceClient")
def test_get_should_return_secret(client: MagicMock):
    # Arrange
    client.return_value.access_secret_version.return_value.payload.data = b"s3cr3t"
    registry = GoogleSecretRegistry(project_id="my-project")
    registry.setup()

    # Act
    result = registry.get("DB_PASSWORD")

    # Assert
    actual = result
    expected = Secret("s3cr3t")
    assert actual == expected


@patch("google.cloud.secretmanager.SecretManagerServiceClient")
def test_get_should_access_latest_version_of_secret(client: MagicMock):
    # Arrange
    client.return_value.access_secret_version.return_value.payload.data = b"s3cr3t"
    registry = GoogleSecretRegistry(project_id="my-project")
    registry.setup()

    # Act
    registry.get("DB_PASSWORD")

    # Assert
    client.return_value.access_secret_version.assert_called_once_with(
        request={"name": "projects/my-project/secrets/DB_PASSWORD/versions/latest"}
    )


@patch("google.cloud.secretmanager.SecretManagerServiceClient")
def test_get_should_raise_secret_not_found_error_when_secret_does_not_exist(client: MagicMock):
    # Arrange
    client.return_value.access_secret_version.side_effect = NotFound("secret not found")
    registry = GoogleSecretRegistry(project_id="my-project", failfast=True)
    registry.setup()

    # Act / Assert
    with pytest.raises(SecretNotFoundError, match="MISSING_SECRET"):
        registry.get("MISSING_SECRET")


# ============================================================================
# register()
# ============================================================================


@patch("google.cloud.secretmanager.SecretManagerServiceClient")
def test_register_should_create_secret_and_add_version(client: MagicMock):
    # Arrange
    registry = GoogleSecretRegistry(project_id="my-project")
    registry.setup()

    # Act
    registry.register("DB_PASSWORD", Secret("newvalue"))

    # Assert
    actual = client.return_value.create_secret.call_args
    expected = call(
        request={
            "parent": "projects/my-project",
            "secret_id": "DB_PASSWORD",
            "secret": {"replication": {"automatic": {}}},
        }
    )
    assert actual == expected


@patch("google.cloud.secretmanager.SecretManagerServiceClient")
def test_register_should_add_encoded_secret_version(client: MagicMock):
    # Arrange
    registry = GoogleSecretRegistry(project_id="my-project")
    registry.setup()

    # Act
    registry.register("DB_PASSWORD", Secret("newvalue"))

    # Assert
    actual = client.return_value.add_secret_version.call_args
    expected = call(
        request={
            "parent": "projects/my-project/secrets/DB_PASSWORD",
            "payload": {"data": b"newvalue"},
        }
    )
    assert actual == expected


@patch("google.cloud.secretmanager.SecretManagerServiceClient")
def test_register_should_still_add_version_when_secret_already_exists(client: MagicMock):
    # Arrange
    client.return_value.create_secret.side_effect = AlreadyExists("already exists")
    registry = GoogleSecretRegistry(project_id="my-project")
    registry.setup()

    # Act
    registry.register("DB_PASSWORD", Secret("newvalue"))

    # Assert
    client.return_value.add_secret_version.assert_called_once_with(
        request={
            "parent": "projects/my-project/secrets/DB_PASSWORD",
            "payload": {"data": b"newvalue"},
        }
    )
