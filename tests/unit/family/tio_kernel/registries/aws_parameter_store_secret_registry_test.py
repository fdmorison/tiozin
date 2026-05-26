from unittest.mock import MagicMock, patch

import pytest

from tiozin.api.metadata.secret.model import Secret
from tiozin.exceptions import SecretNotFoundError
from tiozin.family.tio_kernel import AwsParameterStoreSecretRegistry

# ============================================================================
# setup()
# ============================================================================


@pytest.mark.parametrize(
    "location, region_name, expected_endpoint_url, expected_region_name",
    [
        ("http://localhost:4566", "us-east-1", "http://localhost:4566", "us-east-1"),
        (None, None, None, None),
    ],
)
@patch("boto3.client", return_value=MagicMock())
def test_setup_should_create_ssm_client_with_provided_args(
    client: MagicMock,
    location,
    region_name,
    expected_endpoint_url,
    expected_region_name,
):
    # Arrange
    registry = AwsParameterStoreSecretRegistry(location=location, region_name=region_name)

    # Act
    registry.setup()

    # Assert
    client.assert_called_once_with(
        "ssm",
        region_name=expected_region_name,
        endpoint_url=expected_endpoint_url,
    )


# ============================================================================
# get()
# ============================================================================


@patch("boto3.client", return_value=MagicMock())
def test_get_should_return_secret(client: MagicMock):
    # Arrange
    client.return_value.get_parameter.return_value = {
        "Parameter": {"Value": "s3cr3t"},
    }
    registry = AwsParameterStoreSecretRegistry(location="http://localhost:4566")
    registry.setup()

    # Act
    result = registry.get("DB_PASSWORD")

    # Assert
    actual = result
    expected = Secret("s3cr3t")
    assert actual == expected


@patch("boto3.client", return_value=MagicMock())
def test_get_should_always_decrypt_secret(client: MagicMock):
    # Arrange
    client.return_value.get_parameter.return_value = {
        "Parameter": {"Value": "s3cr3t"},
    }
    registry = AwsParameterStoreSecretRegistry(location="http://localhost:4566")
    registry.setup()

    # Act
    registry.get("DB_PASSWORD")

    # Assert
    client.return_value.get_parameter.assert_called_once_with(
        Name="DB_PASSWORD",
        WithDecryption=True,
    )


@patch("boto3.client", return_value=MagicMock())
def test_get_should_fail_when_secret_not_found(client: MagicMock):
    # Arrange
    client.return_value.exceptions.ParameterNotFound = type("ParameterNotFound", (Exception,), {})
    client.return_value.get_parameter.side_effect = (
        client.return_value.exceptions.ParameterNotFound()
    )
    registry = AwsParameterStoreSecretRegistry(location="http://localhost:4566", failfast=True)
    registry.setup()

    # Act / Assert
    with pytest.raises(SecretNotFoundError, match="MISSING_PARAM"):
        registry.get("MISSING_PARAM")


@patch("boto3.client", return_value=MagicMock())
def test_get_should_propagate_unexpected_error(client: MagicMock):
    # Arrange
    client.return_value.exceptions.ParameterNotFound = type("ParameterNotFound", (Exception,), {})
    client.return_value.get_parameter.side_effect = Exception("boom")
    registry = AwsParameterStoreSecretRegistry()
    registry.setup()

    # Act / Assert
    with pytest.raises(Exception, match="boom"):
        registry.get("DB_PASSWORD")


# ============================================================================
# register()
# ============================================================================


@patch("boto3.client", return_value=MagicMock())
def test_register_should_put_parameter_as_secure_string(client: MagicMock):
    # Arrange
    registry = AwsParameterStoreSecretRegistry(location="http://localhost:4566")
    registry.setup()

    # Act
    registry.register("DB_PASSWORD", Secret("newvalue"))

    # Assert
    client.return_value.put_parameter.assert_called_once_with(
        Name="DB_PASSWORD",
        Value="newvalue",
        Type="SecureString",
        Overwrite=True,
    )
