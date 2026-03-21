from unittest.mock import MagicMock

import pytest

from tiozin.api.metadata.secret.model import Secret
from tiozin.compose.proxies.sensitive import SecretRegistryProxy
from tiozin.exceptions import SecretNotFoundError

# ============================================================================
# SecretRegistryProxy - get()
# ============================================================================


def test_secret_proxy_should_raise_when_get_returns_none():
    # Arrange
    mock = MagicMock()
    mock.get.return_value = None
    proxy = SecretRegistryProxy(mock)

    # Act / Assert
    with pytest.raises(SecretNotFoundError, match="DB_PASSWORD"):
        proxy.get("DB_PASSWORD")


def test_secret_proxy_should_return_secret_when_get_returns_value():
    # Arrange
    mock = MagicMock()
    mock.get.return_value = Secret("s3cr3t")
    proxy = SecretRegistryProxy(mock)

    # Act
    result = proxy.get("DB_PASSWORD")

    # Assert
    actual = (
        str(result),
        isinstance(result, Secret),
    )
    expected = (
        "s3cr3t",
        True,
    )
    assert actual == expected
