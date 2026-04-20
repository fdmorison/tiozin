from freezegun import freeze_time
from pytest import MonkeyPatch

from tiozin.api.metadata.proxy import RegistryProxy
from tiozin.family.tio_kernel import NoOpSettingRegistry


def test_proxy_should_render_env_template_after_setup(monkeypatch: MonkeyPatch):
    # Arrange
    monkeypatch.setenv("MY_VAR", "rendered-value")
    registry = NoOpSettingRegistry(location="{{ ENV.MY_VAR }}")
    proxy = RegistryProxy(registry)

    # Act
    proxy.setup()

    # Assert
    actual = registry.location
    expected = "rendered-value"
    assert actual == expected


@freeze_time("2024-03-15")
def test_proxy_should_render_day_template_after_setup():
    # Arrange
    registry = NoOpSettingRegistry(location="{{ DAY.ds }}")
    proxy = RegistryProxy(registry)

    # Act
    proxy.setup()

    # Assert
    actual = registry.location
    expected = "2024-03-15"
    assert actual == expected


def test_proxy_should_restore_template_after_teardown(monkeypatch: MonkeyPatch):
    # Arrange
    monkeypatch.setenv("MY_VAR", "rendered-value")
    registry = NoOpSettingRegistry(location="{{ ENV.MY_VAR }}")
    proxy = RegistryProxy(registry)
    proxy.setup()

    # Act
    proxy.teardown()

    # Assert
    actual = registry.location
    expected = "{{ ENV.MY_VAR }}"
    assert actual == expected


def test_proxy_should_delegate_repr_to_wrapped():
    # Arrange
    registry = NoOpSettingRegistry()
    proxy = RegistryProxy(registry)

    # Act
    result = repr(proxy)

    # Assert
    actual = result
    expected = repr(registry)
    assert actual == expected
