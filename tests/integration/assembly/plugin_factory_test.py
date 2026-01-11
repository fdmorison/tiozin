from datetime import datetime
from unittest.mock import ANY

import pytest
from freezegun import freeze_time

from tiozin.api import Output
from tiozin.api.metadata.job_manifest import (
    InputManifest,
    Manifest,
    OutputManifest,
    RunnerManifest,
    TransformManifest,
)
from tiozin.assembly.plugin_factory import PluginFactory
from tiozin.exceptions import AmbiguousPluginError, PluginNotFoundError, TiozinUnexpectedError
from tiozin.family.tio_kernel import (
    NoOpInput,
    NoOpOutput,
    NoOpRunner,
    NoOpTransform,
)

ISO_2025_01_02T12_00_00Z = "2025-01-02T12:00:00Z"
OBJ_2025_01_02T12_00_00Z = datetime.fromisoformat(ISO_2025_01_02T12_00_00Z)


@pytest.fixture
def factory() -> PluginFactory:
    f = PluginFactory()
    f.setup()
    return f


def test_register_should_fail_when_registering_non_plugin(factory: PluginFactory):
    # Act/Assert
    with pytest.raises(TypeError, match="is not a Plugin"):
        factory.register(plugin=12345)


def test_register_should_index_plugin_by_multiple_keys(factory: PluginFactory):
    # Assert
    actual = (
        factory._index.get("NoOpInput"),
        factory._index.get("tio_kernel:NoOpInput"),
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
    class CustomTransform(NoOpTransform):
        pass

    class1 = CustomTransform

    class CustomTransform(NoOpTransform):
        pass

    class2 = CustomTransform

    # Act
    factory.register(class1)
    factory.register(class2)

    # Assert
    actual = factory._index.get("CustomTransform")
    expected = {class1, class2}
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
@freeze_time(ISO_2025_01_02T12_00_00Z)
def test_load_should_load_input_plugin(factory: PluginFactory, kind: str):
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
        kind="NoOpInput",
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
        run_id=None,
        created_at=OBJ_2025_01_02T12_00_00Z,
        executed_at=None,
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
@freeze_time(ISO_2025_01_02T12_00_00Z)
def test_load_should_load_output_plugin(factory: PluginFactory, kind: str):
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
        kind="NoOpOutput",
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
        run_id=None,
        created_at=OBJ_2025_01_02T12_00_00Z,
        executed_at=None,
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
@freeze_time(ISO_2025_01_02T12_00_00Z)
def test_load_should_load_transform_plugin(factory: PluginFactory, kind: str):
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
        kind="NoOpTransform",
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
        run_id=None,
        created_at=OBJ_2025_01_02T12_00_00Z,
        executed_at=None,
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
@freeze_time(ISO_2025_01_02T12_00_00Z)
def test_load_should_load_runner_plugin(factory: PluginFactory, kind: str):
    # Act
    plugin = factory.load_plugin(
        kind,
        name="test_runner",
        description="test",
    )

    # Assert
    actual = vars(plugin)
    expected = dict(
        id=ANY,
        kind="NoOpRunner",
        name="test_runner",
        description="test",
        streaming=False,
        options={},
        logger=ANY,
        run_id=None,
        created_at=OBJ_2025_01_02T12_00_00Z,
        executed_at=None,
        finished_at=None,
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
    # Act
    plugin = factory.load_plugin(kind)

    # Assert
    actual = vars(plugin)
    expected = dict(
        id=ANY,
        kind="FileJobRegistry",
        name="FileJobRegistry",
        description=None,
        options=ANY,
        ready=False,
        logger=ANY,
    )
    assert actual == expected


def test_load_should_fail_when_plugin_not_found(factory: PluginFactory):
    # Act/Assert
    with pytest.raises(PluginNotFoundError):
        factory.load_plugin("NonExistentPlugin")


def test_load_should_fail_when_plugin_kind_mismatch(factory: PluginFactory):
    # Act/Assert
    with pytest.raises(PluginNotFoundError):
        factory.load_plugin("NoOpInput", plugin_kind=Output)


def test_load_should_fail_when_multiple_plugins_with_same_name(factory: PluginFactory):
    # Arrange
    class AmbiguousInput(NoOpInput):
        pass

    factory.register(AmbiguousInput)

    class AmbiguousInput(NoOpInput):
        pass

    factory.register(AmbiguousInput)

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
