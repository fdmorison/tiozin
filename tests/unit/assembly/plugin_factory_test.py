import pytest

from tiozin.api import Output
from tiozin.api.metadata.job_manifest import (
    InputManifest,
    Manifest,
    OutputManifest,
    RunnerManifest,
    TransformManifest,
)
from tiozin.assembly.plugin_factory import PluginFactory, PluginMetadata
from tiozin.exceptions import AmbiguousPluginError, PluginNotFoundError, TiozinUnexpectedError
from tiozin.family.tio_kernel import NoOpInput, NoOpOutput, NoOpRunner, NoOpTransform


@pytest.fixture
def factory():
    return PluginFactory()


def test_register_should_store_plugin_class(factory: PluginFactory):
    # Arrange
    provider = "tio_john"
    plugin = NoOpTransform

    # Act
    factory.register(provider, plugin)

    # Assert
    actual = factory._index.get("NoOpTransform")
    expected = {NoOpTransform}
    assert actual == expected


def test_register_should_set_plugin_metadata(factory: PluginFactory):
    # Arrange
    provider = "tio_john"
    plugin = NoOpTransform

    # Act
    factory.register(provider, plugin)

    # Assert
    actual = plugin.__tiometa__
    expected = PluginMetadata(
        kind="NoOpTransform",
        tio_kind="tio_john:NoOpTransform",
        python_kind="tiozin.family.tio_kernel.transforms.noop_transform.NoOpTransform",
        provider="tio_john",
    )
    assert actual == expected


def test_register_should_preserve_existing_plugin_metadata(factory: PluginFactory):
    # Arrange
    plugin = NoOpTransform

    # Act
    factory.register("tio_john", plugin)
    factory.register("tio_xxxx", plugin)

    # Assert
    actual = NoOpTransform.__tiometa__
    expected = PluginMetadata(
        kind="NoOpTransform",
        tio_kind="tio_john:NoOpTransform",
        python_kind="tiozin.family.tio_kernel.transforms.noop_transform.NoOpTransform",
        provider="tio_john",
    )
    assert actual == expected


def test_register_should_fail_when_registering_non_plugin(factory: PluginFactory):
    # Arrange
    provider = "tio_john"
    plugin = 12345

    # Act/Assert
    with pytest.raises(TypeError, match="is not a Plugin"):
        factory.register(provider, plugin)


def test_register_should_index_plugin_by_multiple_keys(factory: PluginFactory):
    # Arrange
    provider = "tio_john"
    plugin = NoOpInput

    # Act
    factory.register(provider, plugin)

    # Assert
    actual = (
        factory._index.get("NoOpInput"),
        factory._index.get("tio_john:NoOpInput"),
        factory._index.get("tiozin.family.tio_kernel.inputs.noop_input.NoOpInput"),
    )
    expected = (
        {NoOpInput},
        NoOpInput,
        NoOpInput,
    )
    assert actual == expected


def test_register_should_group_plugins_with_same_name(factory: PluginFactory):
    # Arrange
    class CustomTransform1(NoOpTransform):
        pass

    class CustomTransform2(NoOpTransform):
        pass

    CustomTransform1.__name__ = "MyTransform"
    CustomTransform2.__name__ = "MyTransform"

    # Act
    factory.register("tio_john", CustomTransform1)
    factory.register("tio_mary", CustomTransform2)

    # Assert
    actual = factory._index.get("MyTransform")
    expected = {CustomTransform1, CustomTransform2}
    assert actual == expected


# ============================================================================
# load()
# ============================================================================
@pytest.mark.parametrize(
    "plugin,kind",
    [
        (NoOpInput, "NoOpInput"),
        (NoOpInput, "tio_john:NoOpInput"),
        (NoOpInput, "tiozin.family.tio_kernel.inputs.noop_input.NoOpInput"),
    ],
)
def test_load_should_return_plugin_instance(factory: PluginFactory, plugin: type, kind: str):
    # Arrange
    factory.register("tio_john", plugin)

    # Act
    result = factory.load_plugin(
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


def test_load_should_fail_when_plugin_not_found(factory: PluginFactory):
    # Act/Assert
    with pytest.raises(PluginNotFoundError):
        factory.load_plugin("NonExistentPlugin")


def test_load_should_fail_when_plugin_kind_mismatch(factory: PluginFactory):
    # Arrange
    factory.register("tio_john", NoOpInput)

    # Act/Assert
    with pytest.raises(PluginNotFoundError):
        factory.load_plugin("NoOpInput", plugin_kind=Output)


def test_load_should_fail_when_multiple_plugins_with_same_name(factory: PluginFactory):
    # Arrange
    class CustomInput1(NoOpInput):
        pass

    class CustomInput2(NoOpInput):
        pass

    CustomInput1.__name__ = "AmbiguousInput"
    CustomInput2.__name__ = "AmbiguousInput"

    factory.register("tio_john", CustomInput1)
    factory.register("tio_mary", CustomInput2)

    # Act/Assert
    with pytest.raises(AmbiguousPluginError):
        factory.load_plugin("AmbiguousInput")


def test_load_should_pass_arguments_to_plugin_constructor(factory: PluginFactory):
    # Arrange
    factory.register("tio_john", NoOpTransform)

    # Act
    plugin = factory.load_plugin(
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


# ============================================================================
# load_step()
# ============================================================================
def test_load_step_should_return_operator_instance_unchanged(factory: PluginFactory):
    # Arrange
    operator = NoOpInput(
        name="test",
        description="test",
        org="acme",
        region="us",
        domain="sales",
        layer="raw",
        product="revenue",
        model="daily",
    )

    # Act
    result = factory.load_step(operator)

    # Assert
    assert result is operator


def test_load_step_should_load_runner_from_manifest(factory: PluginFactory):
    # Arrange
    factory.register("tio_kernel", NoOpRunner)
    manifest = RunnerManifest(
        kind="NoOpRunner",
        name="test_runner",
        description="test",
        org="acme",
        region="us",
        domain="sales",
        layer="raw",
        product="revenue",
        model="daily",
    )

    # Act
    result = factory.load_step(manifest)

    # Assert
    assert isinstance(result, NoOpRunner)
    assert result.name == "test_runner"


def test_load_step_should_load_input_from_manifest(factory: PluginFactory):
    # Arrange
    factory.register("tio_kernel", NoOpInput)
    manifest = InputManifest(
        kind="NoOpInput",
        name="test_input",
        description="test",
        org="acme",
        region="us",
        domain="sales",
        layer="raw",
        product="revenue",
        model="daily",
    )

    # Act
    result = factory.load_step(manifest)

    # Assert
    assert isinstance(result, NoOpInput)
    assert result.name == "test_input"


def test_load_step_should_load_transform_from_manifest(factory: PluginFactory):
    # Arrange
    factory.register("tio_kernel", NoOpTransform)
    manifest = TransformManifest(
        kind="NoOpTransform",
        name="test_transform",
        description="test",
        org="acme",
        region="us",
        domain="sales",
        layer="raw",
        product="revenue",
        model="daily",
    )

    # Act
    result = factory.load_step(manifest)

    # Assert
    assert isinstance(result, NoOpTransform)
    assert result.name == "test_transform"


def test_load_step_should_load_output_from_manifest(factory: PluginFactory):
    # Arrange
    factory.register("tio_kernel", NoOpOutput)
    manifest = OutputManifest(
        kind="NoOpOutput",
        name="test_output",
        description="test",
        org="acme",
        region="us",
        domain="sales",
        layer="raw",
        product="revenue",
        model="daily",
    )

    # Act
    result = factory.load_step(manifest)

    # Assert
    assert isinstance(result, NoOpOutput)
    assert result.name == "test_output"


def test_load_step_should_fail_for_unsupported_manifest(factory: PluginFactory):
    # Arrange
    class UnsupportedManifest(Manifest):
        pass

    manifest = UnsupportedManifest(
        kind="Something",
        name="test",
        description="test",
        org="acme",
        region="us",
        domain="sales",
        layer="raw",
        product="revenue",
        model="daily",
    )

    # Act/Assert
    with pytest.raises(TiozinUnexpectedError, match="Unsupported manifest"):
        factory.load_step(manifest)
