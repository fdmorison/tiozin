import copy
import logging
from datetime import datetime

import pytest

from tiozin import PlugIn
from tiozin.assembly.templating import PluginTemplateOverlay
from tiozin.exceptions import InvalidInputError


# ============================================================================
# Testing PluginTemplateOverlay - Basic Functionality
# ============================================================================
def test_overlay_should_render_and_restore_single_template():
    # Arrange
    plugin = PlugIn()
    plugin.path = "./data/{{domain}}"
    context = {"domain": "sales"}

    # Act
    with PluginTemplateOverlay(plugin, context):
        rendered = plugin.path
    restored = plugin.path

    # Assert
    actual = (
        rendered,
        restored,
    )
    expected = (
        "./data/sales",
        "./data/{{domain}}",
    )
    assert actual == expected


def test_overlay_should_render_and_restore_multiple_templates():
    # Arrange
    plugin = PlugIn()
    plugin.path = "./data/{{domain}}/{{date}}"
    plugin.name = "{{prefix}}_output"
    context = {"domain": "sales", "date": "2024-01-15", "prefix": "test"}

    # Act
    with PluginTemplateOverlay(plugin, context):
        rendered = (plugin.path, plugin.name)
    restored = (plugin.path, plugin.name)

    # Assert
    actual = (
        rendered,
        restored,
    )
    expected = (
        (
            "./data/sales/2024-01-15",
            "test_output",
        ),
        (
            "./data/{{domain}}/{{date}}",
            "{{prefix}}_output",
        ),
    )
    assert actual == expected


def test_overlay_should_not_modify_non_template_strings():
    # Arrange
    plugin = PlugIn()
    plugin.path = "./data/sales"
    plugin.name = "output"
    context = {"domain": "sales"}

    # Act
    with PluginTemplateOverlay(plugin, context):
        rendered = (plugin.path, plugin.name)
    restored = (plugin.path, plugin.name)

    # Assert
    actual = (
        rendered,
        restored,
    )
    expected = (
        (
            "./data/sales",
            "output",
        ),
        (
            "./data/sales",
            "output",
        ),
    )
    assert actual == expected


def test_overlay_should_not_modify_private_attributes():
    # Arrange
    plugin = PlugIn()
    plugin._private = "{{domain}}"
    context = {"domain": "sales"}

    # Act
    with PluginTemplateOverlay(plugin, context):
        rendered = plugin._private
    restored = plugin._private

    # Assert
    actual = (
        rendered,
        restored,
    )
    expected = (
        "{{domain}}",
        "{{domain}}",
    )
    assert actual == expected


def test_overlay_should_render_and_restore_nested_dict_templates():
    # Arrange
    plugin = PlugIn()
    plugin.config = {"path": "./data/{{domain}}", "region": "{{region}}"}
    context = {"domain": "sales", "region": "us-east"}

    # Act
    with PluginTemplateOverlay(plugin, context):
        rendered = dict(plugin.config)
    restored = plugin.config

    # Assert
    actual = (
        rendered,
        restored,
    )
    expected = (
        {
            "path": "./data/sales",
            "region": "us-east",
        },
        {
            "path": "./data/{{domain}}",
            "region": "{{region}}",
        },
    )
    assert actual == expected


def test_overlay_should_render_and_restore_nested_list_templates():
    # Arrange
    plugin = PlugIn()
    plugin.paths = [
        "./{{env}}/data",
        "./output/{{domain}}",
    ]
    context = {"env": "prod", "domain": "sales"}

    # Act
    with PluginTemplateOverlay(plugin, context):
        rendered = list(plugin.paths)
    restored = plugin.paths

    # Assert
    actual = (
        rendered,
        restored,
    )
    expected = (
        [
            "./prod/data",
            "./output/sales",
        ],
        [
            "./{{env}}/data",
            "./output/{{domain}}",
        ],
    )
    assert actual == expected


def test_overlay_should_render_and_restore_nested_plugins():
    # Arrange
    plugin = PlugIn()
    plugin.inner = PlugIn()
    plugin.inner.path = "{{domain}}/inner"
    context = {"domain": "sales"}

    # Act
    with PluginTemplateOverlay(plugin, context):
        rendered = plugin.inner.path
    restored = plugin.inner.path

    # Assert
    actual = (
        rendered,
        restored,
    )
    expected = (
        "sales/inner",
        "{{domain}}/inner",
    )
    assert actual == expected


def test_overlay_should_restore_on_exception():
    # Arrange
    plugin = PlugIn()
    plugin.name = "{{value}}"
    context = {"value": "resolved"}

    # Act
    try:
        with PluginTemplateOverlay(plugin, context):
            rendered = plugin.name
            raise ValueError("Simulated error")
    except ValueError:
        pass
    restored = plugin.name

    # Assert
    actual = (
        rendered,
        restored,
    )
    expected = (
        "resolved",
        "{{value}}",
    )
    assert actual == expected


def test_overlay_should_raise_error_on_missing_variable():
    # Arrange
    plugin = PlugIn()
    plugin.path = "./data/{{missing}}"
    context = {"other": "value"}

    # Act & Assert
    with pytest.raises(InvalidInputError):
        with PluginTemplateOverlay(plugin, context):
            pass


def test_overlay_should_render_and_restore_templates_with_multiple_variables():
    # Arrange
    plugin = PlugIn()
    plugin.path = "./data/{{domain}}/{{year}}-{{month}}-{{day}}/file.txt"
    context = {"domain": "sales", "year": "2024", "month": "01", "day": "15"}

    # Act
    with PluginTemplateOverlay(plugin, context):
        rendered = plugin.path
    restored = plugin.path

    # Assert
    actual = (
        rendered,
        restored,
    )
    expected = (
        "./data/sales/2024-01-15/file.txt",
        "./data/{{domain}}/{{year}}-{{month}}-{{day}}/file.txt",
    )
    assert actual == expected


def test_overlay_should_not_modify_strings_when_context_is_empty():
    # Arrange
    plugin = PlugIn()
    plugin.path = "./data/static"
    context = {}

    # Act
    with PluginTemplateOverlay(plugin, context):
        rendered = plugin.path
    restored = plugin.path

    # Assert
    actual = (
        rendered,
        restored,
    )
    expected = (
        "./data/static",
        "./data/static",
    )
    assert actual == expected


def test_overlay_should_render_and_restore_deeply_nested_structures():
    # Arrange
    plugin = PlugIn()
    plugin.config = {
        "level1": {
            "level2": ["./{{a}}", "./{{b}}"],
        }
    }
    context = {"a": "foo", "b": "bar"}

    # Act
    with PluginTemplateOverlay(plugin, context):
        rendered = copy.deepcopy(plugin.config)
    restored = plugin.config

    # Assert
    actual = (
        rendered,
        restored,
    )
    expected = (
        {
            "level1": {
                "level2": ["./foo", "./bar"],
            }
        },
        {
            "level1": {
                "level2": ["./{{a}}", "./{{b}}"],
            }
        },
    )
    assert actual == expected


@pytest.mark.parametrize(
    "value",
    [42, True, False, 3.14, None, datetime.now(), logging.getLogger("test")],
)
def test_overlay_should_not_modify_non_string_values(value):
    # Arrange
    plugin = PlugIn()
    plugin.value = value
    context = {}

    # Act
    with PluginTemplateOverlay(plugin, context):
        rendered = plugin.value
    restored = plugin.value

    # Assert
    actual = (
        rendered,
        restored,
    )
    expected = (
        value,
        value,
    )
    assert actual == expected


def test_overlay_should_not_modify_immutable_tuple_with_templates():
    # Arrange
    plugin = PlugIn()
    plugin.paths = (
        "./{{env}}/data",
        "./output/{{domain}}",
    )
    context = {"env": "prod", "domain": "sales"}

    # Act
    with PluginTemplateOverlay(plugin, context):
        rendered = plugin.paths
    restored = plugin.paths

    # Assert
    actual = (
        rendered,
        restored,
    )
    expected = (
        (
            "./{{env}}/data",
            "./output/{{domain}}",
        ),
        (
            "./{{env}}/data",
            "./output/{{domain}}",
        ),
    )
    assert actual == expected


def test_overlay_should_not_modify_immutable_frozenset_with_templates():
    # Arrange
    plugin = PlugIn()
    plugin.tags = frozenset(["{{env}}", "{{domain}}"])
    context = {"env": "prod", "domain": "sales"}

    # Act
    with PluginTemplateOverlay(plugin, context):
        rendered = plugin.tags
    restored = plugin.tags

    # Assert
    actual = (
        rendered,
        restored,
    )
    expected = (
        frozenset(["{{env}}", "{{domain}}"]),
        frozenset(["{{env}}", "{{domain}}"]),
    )
    assert actual == expected


def test_overlay_should_render_and_restore_mutable_objects_inside_immutable_tuple():
    # Arrange
    plugin = PlugIn()
    plugin.data = (
        {"path": "./data/{{domain}}"},
        ["./{{env}}/data", "./output/{{region}}"],
        "static_value",
    )
    context = {"domain": "sales", "env": "prod", "region": "us-east"}

    # Act
    with PluginTemplateOverlay(plugin, context):
        rendered = copy.deepcopy(plugin.data)
    restored = plugin.data

    # Assert
    actual = (
        rendered,
        restored,
    )
    expected = (
        (
            {"path": "./data/sales"},
            ["./prod/data", "./output/us-east"],
            "static_value",
        ),
        (
            {"path": "./data/{{domain}}"},
            ["./{{env}}/data", "./output/{{region}}"],
            "static_value",
        ),
    )
    assert actual == expected


def test_overlay_should_restore_templates_after_each_sequential_overlay():
    # Arrange
    plugin = PlugIn()
    plugin.path = "./data/{{domain}}"

    # Act
    with PluginTemplateOverlay(plugin, {"domain": "sales"}):
        rendered = plugin.path

    with PluginTemplateOverlay(plugin, {"domain": "finance"}):
        rendered_2 = plugin.path
    restored = plugin.path

    # Assert
    actual = (
        rendered,
        rendered_2,
        restored,
    )
    expected = (
        "./data/sales",
        "./data/finance",
        "./data/{{domain}}",
    )
    assert actual == expected


def test_overlay_should_render_and_restore_templates_with_jinja2_filters():
    # Arrange
    plugin = PlugIn()
    plugin.path = "./data/{{domain|upper}}"
    context = {"domain": "sales"}

    # Act
    with PluginTemplateOverlay(plugin, context):
        rendered = plugin.path
    restored = plugin.path

    # Assert
    actual = (
        rendered,
        restored,
    )
    expected = (
        "./data/SALES",
        "./data/{{domain|upper}}",
    )
    assert actual == expected


def test_overlay_should_render_and_restore_templates_with_jinja2_expressions():
    # Arrange
    plugin = PlugIn()
    plugin.path = "./data/{{ domain ~ '/' ~ date }}"
    context = {"domain": "sales", "date": "2024-01-15"}

    # Act
    with PluginTemplateOverlay(plugin, context):
        rendered = plugin.path
    restored = plugin.path

    # Assert
    actual = (
        rendered,
        restored,
    )
    expected = (
        "./data/sales/2024-01-15",
        "./data/{{ domain ~ '/' ~ date }}",
    )
    assert actual == expected
