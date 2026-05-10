from unittest.mock import ANY

import pytest

from tiozin.api import Input, Runner
from tiozin.api.metadata.job.model import (
    InputManifest,
    OutputManifest,
    RunnerManifest,
    TransformManifest,
)
from tiozin.api.metadata.model import Manifest
from tiozin.api.metadata.setting.model import SchemaRegistryManifest
from tiozin.compose import TiozinRegistry
from tiozin.exceptions import (
    PluginConflictError,
    PluginNotFoundError,
    TiozinInputError,
)
from tiozin.family.tio_kernel import (
    NoOpInput,
    NoOpOutput,
    NoOpRunner,
    NoOpTransform,
)


@pytest.fixture
def factory() -> TiozinRegistry:
    return TiozinRegistry()


# ============================================================================
# register()
# ============================================================================
def test_register_should_index_plugin_by_multiple_keys(factory: TiozinRegistry):
    # Act
    factory.register(NoOpInput)

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


def test_register_should_group_plugins_with_same_name(factory: TiozinRegistry):
    # Arrange
    class CustomTransform(NoOpTransform): ...

    class1 = CustomTransform

    class CustomTransform(NoOpTransform): ...

    class2 = CustomTransform

    # Act
    factory.register(class1)
    factory.register(class2)

    # Assert
    actual = factory._index.get("CustomTransform")
    expected = {class1, class2}
    assert actual == expected


def test_register_should_fail_when_registering_non_plugin(factory: TiozinRegistry):
    # Arrange
    tiozin = {"kind": "NonPlugin"}  # Not a Tiozin class

    # Act/Assert
    with pytest.raises(TiozinInputError, match="is not a Tiozin"):
        factory.register(tiozin)


# ============================================================================
# resolve()
# ============================================================================
@pytest.mark.parametrize(
    "kind",
    [
        "NoOpInput",
        "tio_kernel:NoOpInput",
        "tiozin.family.tio_kernel.inputs.noop_input.NoOpInput",
    ],
)
def test_resolve_should_find_plugin_by_kind_format(factory: TiozinRegistry, kind: str):
    # Act
    tiozin_class = factory.resolve(kind)

    # Assert
    actual = tiozin_class
    expected = NoOpInput
    assert actual == expected


def test_resolve_should_fail_when_plugin_not_found(factory: TiozinRegistry):
    # Act
    with pytest.raises(PluginNotFoundError):
        factory.resolve("NonExistentPlugin")


def test_resolve_should_fail_when_multiple_plugins_with_same_name(factory: TiozinRegistry):
    # Arrange
    class CustomTransform(NoOpTransform): ...

    class1 = CustomTransform

    class CustomTransform(NoOpTransform): ...

    class2 = CustomTransform

    # Act
    factory.register(class1)
    factory.register(class2)

    # Act
    with pytest.raises(PluginConflictError):
        factory.resolve("CustomTransform")


# ============================================================================
# load()
# ============================================================================
@pytest.mark.parametrize(
    "kind",
    [
        "NoOpInput",
        "NoOpOutput",
        "NoOpTransform",
    ],
)
def test_load_should_load_step_plugin(factory: TiozinRegistry, kind: str):
    # Act
    tiozin = factory.load(
        kind,
        name="test",
    )

    # Assert
    actual = vars(tiozin)
    expected = dict(
        kind=kind,
        name="test",
        slug="test",
        description=None,
        org=None,
        region=None,
        domain=None,
        subdomain=None,
        layer=None,
        product=None,
        model=None,
        schema_subject=None,
        schema_version=None,
        options={},
        verbose=True,
        force_error=False,
    )
    assert actual == expected


def test_load_should_load_runner_plugin(factory: TiozinRegistry):
    # Act
    tiozin = factory.load(
        "NoOpRunner",
        name="test_runner",
        description="test",
    )

    # Assert
    actual = vars(tiozin)
    expected = dict(
        kind="NoOpRunner",
        name="test_runner",
        slug="test_runner",
        description="test",
        streaming=False,
        verbose=True,
        force_error=False,
        options={},
    )
    assert actual == expected


def test_load_should_load_registry_plugin(factory: TiozinRegistry):
    # Act
    tiozin = factory.load("FileJobRegistry")

    # Assert
    actual = vars(tiozin)
    expected = dict(
        kind="FileJobRegistry",
        name="FileJobRegistry",
        slug="filejobregistry",
        description=None,
        options=ANY,
        ready=False,
        location=None,
        cache=False,
        readonly=False,
        timeout=3,
        failfast=False,
    )
    assert actual == expected


def test_load_should_validate_plugin_role(factory: TiozinRegistry):
    # Act
    tiozin = factory.load(
        kind="NoOpInput",
        role=Input,
        name="test",
        org="acme",
        region="us",
        domain="sales",
        layer="raw",
        product="revenue",
        model="daily",
    )

    # Assert
    actual = tiozin.kind
    expected = "NoOpInput"
    assert actual == expected


def test_load_should_fail_when_plugin_does_not_match_role(factory: TiozinRegistry):
    # Act
    with pytest.raises(TiozinInputError):
        factory.load(
            kind="NoOpInput",
            role=Runner,
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
def test_load_manifest_should_return_same_instance_when_given_tiozin(factory: TiozinRegistry):
    # Arrange
    tiozin = NoOpInput(name="test")

    # Act
    result = factory.load_manifest(tiozin)

    # Assert
    assert result is tiozin


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
    factory: TiozinRegistry, plugin_class: type, manifest_class: type
):
    # Arrange
    manifest = manifest_class(
        kind=plugin_class.__name__,
        name="test",
    )

    # Act
    tiozin = factory.load_manifest(manifest)

    # Assert
    assert isinstance(tiozin, plugin_class)


def test_load_manifest_should_preserve_defaults(
    factory: TiozinRegistry,
):
    # Arrange
    manifest = SchemaRegistryManifest(kind="NoOpSchemaRegistry")

    # Act
    registry = factory.load_manifest(manifest)

    # Assert
    actual = (
        registry.kind,
        registry.subject_template,
        registry.default_version,
        registry.show_schema,
    )
    expected = (
        "NoOpSchemaRegistry",
        "{{org}}.{{region}}.{{domain}}.{{subdomain}}.{{layer}}.{{product}}.{{model}}",
        "latest",
        False,
    )
    assert actual == expected


def test_load_manifest_should_fail_when_manifest_has_no_tiozin_role(factory: TiozinRegistry):
    # Arrange
    class UnsupportedManifest(Manifest):
        pass

    manifest = UnsupportedManifest(kind="NoOpInput", name="test")

    # Act/Assert
    with pytest.raises(TiozinInputError):
        factory.load_manifest(manifest)
