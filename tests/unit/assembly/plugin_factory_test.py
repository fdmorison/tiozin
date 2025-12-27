import pytest

from tiozin.assembly.plugin_factory import PluginMetadata, plugin_factory
from tiozin.exceptions import AmbiguousPluginError, PluginNotFoundError
from tiozin.family.tio_kernel import NoOpInput, NoOpTransform
from tiozin.model import Output


def test_register_should_store_plugin_class():
    # Arrange
    provider = "tio_john"
    plugin = NoOpTransform

    # Act
    plugin_factory.register(provider, plugin)

    # Assert
    actual = plugin_factory._registry.get("NoOpTransform")
    expected = {NoOpTransform}
    assert actual == expected


def test_register_should_set_plugin_metadata():
    # Arrange
    provider = "tio_john"
    plugin = NoOpTransform

    # Act
    plugin_factory.register(provider, plugin)

    # Assert
    actual = plugin.__tiometa__
    expected = PluginMetadata(
        kind="NoOpTransform",
        tio_kind="tio_john:NoOpTransform",
        python_kind="tiozin.family.tio_kernel.transforms.noop_transform.NoOpTransform",
        provider="tio_john",
    )
    assert actual == expected


def test_register_should_preserve_existing_plugin_metadata():
    # Arrange
    plugin = NoOpTransform

    # Act
    plugin_factory.register("tio_john", plugin)
    plugin_factory.register("tio_xxxx", plugin)

    # Assert
    actual = NoOpTransform.__tiometa__
    expected = PluginMetadata(
        kind="NoOpTransform",
        tio_kind="tio_john:NoOpTransform",
        python_kind="tiozin.family.tio_kernel.transforms.noop_transform.NoOpTransform",
        provider="tio_john",
    )
    assert actual == expected


def test_register_should_fail_when_registering_non_plugin():
    # Arrange
    provider = "tio_john"
    plugin = 12345

    # Act/Assert
    with pytest.raises(TypeError, match="is not a Plugin"):
        plugin_factory.register(provider, plugin)


def test_register_should_index_plugin_by_multiple_keys():
    # Arrange
    provider = "tio_john"
    plugin = NoOpInput

    # Act
    plugin_factory.register(provider, plugin)

    # Assert
    actual = (
        plugin_factory._registry.get("NoOpInput"),
        plugin_factory._registry.get("tio_john:NoOpInput"),
        plugin_factory._registry.get("tiozin.family.tio_kernel.inputs.noop_input.NoOpInput"),
    )
    expected = (
        {NoOpInput},
        NoOpInput,
        NoOpInput,
    )
    assert actual == expected


def test_register_should_group_plugins_with_same_name():
    # Arrange
    class CustomTransform1(NoOpTransform):
        pass

    class CustomTransform2(NoOpTransform):
        pass

    CustomTransform1.__name__ = "MyTransform"
    CustomTransform2.__name__ = "MyTransform"

    # Act
    plugin_factory.register("tio_john", CustomTransform1)
    plugin_factory.register("tio_mary", CustomTransform2)

    # Assert
    actual = plugin_factory._registry.get("MyTransform")
    expected = {CustomTransform1, CustomTransform2}
    assert actual == expected


# ============================================================================
# get()
# ============================================================================
@pytest.mark.parametrize(
    "plugin,kind",
    [
        (NoOpInput, "NoOpInput"),
        (NoOpInput, "tio_john:NoOpInput"),
        (NoOpInput, "tiozin.family.tio_kernel.inputs.noop_input.NoOpInput"),
    ],
)
def test_get_should_return_plugin_instance(plugin: type, kind: str):
    # Arrange
    plugin_factory.register("tio_john", plugin)

    # Act
    result = plugin_factory.get(
        kind,
        name="test",
        description="test",
        org="acme",
        region="us",
        domain="sales",
        layer="raw",
        product="revenue",
        model="daily",
    )

    # Assert
    assert isinstance(result, plugin)


def test_get_should_fail_when_plugin_not_found():
    # Act/Assert
    with pytest.raises(PluginNotFoundError):
        plugin_factory.get("NonExistentPlugin")


def test_get_should_fail_when_plugin_kind_mismatch():
    # Arrange
    plugin_factory.register("tio_john", NoOpInput)

    # Act/Assert
    with pytest.raises(PluginNotFoundError):
        plugin_factory.get("NoOpInput", plugin_kind=Output)


def test_get_should_fail_when_multiple_plugins_with_same_name():
    # Arrange
    class CustomInput1(NoOpInput):
        pass

    class CustomInput2(NoOpInput):
        pass

    CustomInput1.__name__ = "AmbiguousInput"
    CustomInput2.__name__ = "AmbiguousInput"

    plugin_factory.register("tio_john", CustomInput1)
    plugin_factory.register("tio_mary", CustomInput2)

    # Act/Assert
    with pytest.raises(AmbiguousPluginError):
        plugin_factory.get("AmbiguousInput")


def test_get_should_pass_arguments_to_plugin_constructor():
    # Arrange
    plugin_factory.register("tio_john", NoOpTransform)

    # Act
    plugin = plugin_factory.get(
        "NoOpTransform",
        name="my_transform",
        description="my description",
        org="acme",
        region="us",
        domain="sales",
        layer="raw",
        product="revenue",
        model="daily",
    )

    # Assert
    actual = (plugin.name, plugin.description, plugin.org)
    expected = ("my_transform", "my description", "acme")
    assert actual == expected
