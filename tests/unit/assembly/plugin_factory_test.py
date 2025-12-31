from unittest.mock import ANY

import pytest

from tiozin.api import Input, JobRegistry, Output, Registry, Runner, Transform
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
from tiozin.family.tio_kernel.registries import FileJobRegistry


@pytest.fixture
def factory():
    return PluginFactory()


def test_register_should_store_plugin_class(factory: PluginFactory):
    # Act
    factory.register(provider="tio_john", plugin=NoOpTransform)

    # Assert
    actual = factory._index.get("NoOpTransform")
    expected = {NoOpTransform}
    assert actual == expected


def test_register_should_set_plugin_metadata(factory: PluginFactory):
    # Act
    factory.register(provider="tio_john", plugin=NoOpTransform)

    # Assert
    actual = NoOpTransform.__tiometa__
    expected = PluginMetadata(
        kind="NoOpTransform",
        tio_kind="tio_john:NoOpTransform",
        python_kind="tiozin.family.tio_kernel.transforms.noop_transform.NoOpTransform",
        provider="tio_john",
    )
    assert actual == expected


def test_register_should_preserve_existing_plugin_metadata(factory: PluginFactory):
    # Act
    factory.register(provider="tio_john", plugin=NoOpTransform)
    factory.register(provider="tio_xxxx", plugin=NoOpTransform)

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
    # Act/Assert
    with pytest.raises(TypeError, match="is not a Plugin"):
        factory.register(provider="tio_john", plugin=12345)


def test_register_should_index_plugin_by_multiple_keys(factory: PluginFactory):
    # Act
    factory.register(provider="tio_john", plugin=NoOpInput)

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
    "kind",
    [
        "NoOpInput",
        "tio_kernel:NoOpInput",
        "tiozin.family.tio_kernel.inputs.noop_input.NoOpInput",
    ],
)
def test_load_should_load_input_plugin(factory: PluginFactory, kind: str):
    # Arrange
    factory.register("tio_kernel", NoOpInput)

    # Act
    plugin = factory.load_plugin(
        kind,
        name="test_input",
        description="test",
        org="acme",
        region="us",
        domain="sales",
        layer="raw",
        product="revenue",
        model="daily",
    )

    # Assert
    actual = vars(plugin)
    expected = dict(
        kind=NoOpInput,
        plugin_kind=Input,
        name="test_input",
        description="test",
        org="acme",
        region="us",
        domain="sales",
        layer="raw",
        product="revenue",
        model="daily",
        schema=None,
        schema_subject=None,
        schema_version=None,
        options={},
        id=ANY,
        run_id=ANY,
        created_at=ANY,
        started_at=None,
        finished_at=None,
        logger=ANY,
    )
    assert actual == expected


@pytest.mark.parametrize(
    "kind",
    [
        "NoOpOutput",
        "tio_kernel:NoOpOutput",
        "tiozin.family.tio_kernel.outputs.noop_output.NoOpOutput",
    ],
)
def test_load_should_load_output_plugin(factory: PluginFactory, kind: str):
    # Arrange
    factory.register("tio_kernel", NoOpOutput)

    # Act
    plugin = factory.load_plugin(
        kind,
        name="test_output",
        description="test",
        org="acme",
        region="us",
        domain="sales",
        layer="raw",
        product="revenue",
        model="daily",
    )

    # Assert
    actual = vars(plugin)
    expected = dict(
        kind=NoOpOutput,
        plugin_kind=Output,
        name="test_output",
        description="test",
        org="acme",
        region="us",
        domain="sales",
        layer="raw",
        product="revenue",
        model="daily",
        options={},
        id=ANY,
        run_id=ANY,
        created_at=ANY,
        started_at=None,
        finished_at=None,
        logger=ANY,
    )
    assert actual == expected


@pytest.mark.parametrize(
    "kind",
    [
        "NoOpTransform",
        "tio_kernel:NoOpTransform",
        "tiozin.family.tio_kernel.transforms.noop_transform.NoOpTransform",
    ],
)
def test_load_should_load_transform_plugin(factory: PluginFactory, kind: str):
    # Arrange
    factory.register("tio_kernel", NoOpTransform)

    # Act
    plugin = factory.load_plugin(
        kind,
        name="test_transform",
        description="test",
        org="acme",
        region="us",
        domain="sales",
        layer="raw",
        product="revenue",
        model="daily",
    )

    # Assert
    actual = vars(plugin)
    expected = dict(
        kind=NoOpTransform,
        plugin_kind=Transform,
        name="test_transform",
        description="test",
        org="acme",
        region="us",
        domain="sales",
        layer="raw",
        product="revenue",
        model="daily",
        options={},
        id=ANY,
        run_id=ANY,
        created_at=ANY,
        started_at=None,
        finished_at=None,
        logger=ANY,
    )
    assert actual == expected


@pytest.mark.parametrize(
    "kind",
    [
        "NoOpRunner",
        "tio_kernel:NoOpRunner",
        "tiozin.family.tio_kernel.runners.noop_runner.NoOpRunner",
    ],
)
def test_load_should_load_runner_plugin(factory: PluginFactory, kind: str):
    # Arrange
    factory.register("tio_kernel", NoOpRunner)

    # Act
    plugin = factory.load_plugin(
        kind,
        name="test_runner",
        description="test",
        org="acme",
        region="us",
        domain="sales",
        layer="raw",
        product="revenue",
        model="daily",
    )

    # Assert
    actual = vars(plugin)
    expected = dict(
        kind=NoOpRunner,
        plugin_kind=Runner,
        name="test_runner",
        description="test",
        org="acme",
        region="us",
        domain="sales",
        layer="raw",
        product="revenue",
        model="daily",
        streaming=False,
        options={},
        id=ANY,
        run_id=ANY,
        created_at=ANY,
        started_at=None,
        finished_at=None,
        logger=ANY,
    )
    assert actual == expected


@pytest.mark.parametrize(
    "kind",
    [
        "FileJobRegistry",
        "tio_kernel:FileJobRegistry",
        "tiozin.family.tio_kernel.registries.file_job_registry.FileJobRegistry",
    ],
)
def test_load_should_load_registry_plugin(factory: PluginFactory, kind: str):
    # Arrange
    factory.register("tio_kernel", FileJobRegistry)

    # Act
    plugin = factory.load_plugin(kind)

    # Assert
    actual = vars(plugin)
    expected = dict(
        id=ANY,
        kind=FileJobRegistry,
        plugin_kind=Registry,
        registry_kind=JobRegistry,
        name="FileJobRegistry",
        description=None,
        options={},
        ready=False,
        logger=ANY,
        yaml=ANY,
    )
    assert actual == expected


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


# ============================================================================
# load_step()
# ============================================================================
def test_load_step_should_return_operator_as_is(factory: PluginFactory):
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
    result = factory.load_manifest(operator)

    # Assert
    assert result is operator


@pytest.mark.parametrize(
    "plugin_class,manifest_class",
    [
        (NoOpRunner, RunnerManifest),
        (NoOpInput, InputManifest),
        (NoOpTransform, TransformManifest),
        (NoOpOutput, OutputManifest),
    ],
)
def test_load_step_should_load_plugin_from_manifest(
    factory: PluginFactory, plugin_class: type, manifest_class: type
):
    # Arrange
    factory.register("tio_kernel", plugin_class)
    manifest = manifest_class(
        kind=plugin_class.__name__,
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
    plugin = factory.load_manifest(manifest)

    # Assert
    assert isinstance(plugin, plugin_class)


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
        factory.load_manifest(manifest)
