from datetime import datetime
from unittest.mock import ANY

import pytest
from freezegun import freeze_time

from tiozin.api import Input, Runner
from tiozin.api.metadata.job_manifest import (
    InputManifest,
    OutputManifest,
    RunnerManifest,
    TransformManifest,
)
from tiozin.api.metadata.manifest import Manifest
from tiozin.assembly.plugin_factory import PluginRegistry
from tiozin.exceptions import (
    AmbiguousPluginError,
    InvalidInputError,
    PluginKindError,
    PluginNotFoundError,
)
from tiozin.family.tio_kernel import (
    NoOpInput,
    NoOpOutput,
    NoOpRunner,
    NoOpTransform,
)

ISO_2025_01_02T12_00_00Z = "2025-01-02T12:00:00Z"
OBJ_2025_01_02T12_00_00Z = datetime.fromisoformat(ISO_2025_01_02T12_00_00Z)


@pytest.fixture
def factory() -> PluginRegistry:
    return PluginRegistry()


def test_register_should_fail_when_registering_non_plugin(factory: PluginRegistry):
    # Act/Assert
    with pytest.raises(InvalidInputError, match="is not a Plugin"):
        factory.register(plugin=12345)


def test_register_should_index_plugin_by_multiple_keys(factory: PluginRegistry):
    # Assert
    actual = (
        factory._index.get("NoOpInput"),
        factory._index.get("tio_kernel:NoOpInput"),
        factory._index.get("tiozin://tio_kernel/input/NoOpInput"),
        factory._index.get("tiozin.family.tio_kernel.inputs.noop_input.NoOpInput"),
    )
    expected = (
        {NoOpInput},
        {NoOpInput},
        {NoOpInput},
        {NoOpInput},
    )
    assert actual == expected


def test_register_should_group_plugins_with_same_name(factory: PluginRegistry):
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
def test_load_should_load_input_plugin(factory: PluginRegistry, kind: str):
    # Act
    plugin = factory.load(
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
        verbose=False,
        force_error=False,
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
def test_load_should_load_output_plugin(factory: PluginRegistry, kind: str):
    # Act
    plugin = factory.load(
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
        verbose=False,
        force_error=False,
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
def test_load_should_load_transform_plugin(factory: PluginRegistry, kind: str):
    # Act
    plugin = factory.load(
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
        verbose=False,
        force_error=False,
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
def test_load_should_load_runner_plugin(factory: PluginRegistry, kind: str):
    # Act
    plugin = factory.load(
        kind,
        name="test_runner",
        description="test",
    )

    # Assert
    actual = vars(plugin)
    expected = dict(
        kind="NoOpRunner",
        name="test_runner",
        description="test",
        streaming=False,
        verbose=False,
        force_error=False,
        options={},
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
def test_load_should_load_registry_plugin(factory: PluginRegistry, kind: str):
    # Act
    plugin = factory.load(kind)

    # Assert
    actual = vars(plugin)
    expected = dict(
        kind="FileJobRegistry",
        name="FileJobRegistry",
        description=None,
        options=ANY,
        ready=False,
    )
    assert actual == expected


def test_load_should_fail_when_plugin_not_found(factory: PluginRegistry):
    # Act/Assert
    with pytest.raises(PluginNotFoundError):
        factory.load("NonExistentPlugin")


def test_load_should_fail_when_multiple_plugins_with_same_name(factory: PluginRegistry):
    # Arrange
    class AmbiguousInput(NoOpInput):
        pass

    factory.register(AmbiguousInput)

    class AmbiguousInput(NoOpInput):
        pass

    factory.register(AmbiguousInput)

    # Act/Assert
    with pytest.raises(AmbiguousPluginError):
        factory.load("AmbiguousInput")


# ============================================================================
# safe_load()
# ============================================================================
def test_safe_load_should_return_typed_plugin(factory: PluginRegistry):
    # Act
    plugin = factory.safe_load(
        kind="NoOpInput",
        plugin_kind=Input,
        name="test",
        org="acme",
        region="us",
        domain="sales",
        layer="raw",
        product="revenue",
        model="daily",
    )

    # Assert
    actual = (isinstance(plugin, Input), isinstance(plugin, NoOpInput))
    expected = (True, True)
    assert actual == expected


def test_safe_load_should_fail_when_plugin_kind_does_not_match(factory: PluginRegistry):
    # Act/Assert
    with pytest.raises(PluginKindError):
        factory.safe_load(
            kind="NoOpInput",
            plugin_kind=Runner,
            name="test",
            org="acme",
            region="us",
            domain="sales",
            layer="raw",
            product="revenue",
            model="daily",
        )


# ============================================================================
# load_manifest()
# ============================================================================
def test_load_manifest_should_return_plugin_as_is(factory: PluginRegistry):
    # Arrange
    plugin = NoOpInput(
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
    result = factory.load_manifest(plugin)

    # Assert
    assert result is plugin


@pytest.mark.parametrize(
    "plugin_class,manifest_class",
    [
        (NoOpRunner, RunnerManifest),
        (NoOpInput, InputManifest),
        (NoOpTransform, TransformManifest),
        (NoOpOutput, OutputManifest),
    ],
)
def test_load_manifest_should_load_plugin_from_manifest(
    factory: PluginRegistry, plugin_class: type, manifest_class: type
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


def test_load_manifest_should_fail_when_manifest_has_no_plugin_kind(factory: PluginRegistry):
    # Arrange
    class UnsupportedManifest(Manifest):
        pass

    manifest = UnsupportedManifest(kind="NoOpInput", name="test")

    # Act/Assert
    with pytest.raises(PluginKindError):
        factory.load_manifest(manifest)
