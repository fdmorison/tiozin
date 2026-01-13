import copy

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

    # Assert
    actual = (
        rendered,
        plugin.path,
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
        rendered_path = plugin.path
        rendered_name = plugin.name

    # Assert
    actual = (
        rendered_path,
        plugin.path,
        rendered_name,
        plugin.name,
    )
    expected = (
        "./data/sales/2024-01-15",
        "./data/{{domain}}/{{date}}",
        "test_output",
        "{{prefix}}_output",
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
        rendered_path = plugin.path
        rendered_name = plugin.name

    # Assert
    actual = (
        rendered_path,
        plugin.path,
        rendered_name,
        plugin.name,
    )
    expected = (
        "./data/sales",
        "./data/sales",
        "output",
        "output",
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

    # Assert
    actual = (
        rendered,
        plugin._private,
    )
    expected = (
        "{{domain}}",
        "{{domain}}",
    )
    assert actual == expected


def test_overlay_should_handle_nested_dict_templates():
    # Arrange
    plugin = PlugIn()
    plugin.config = {"path": "./data/{{domain}}", "region": "{{region}}"}
    context = {"domain": "sales", "region": "us-east"}

    # Act
    with PluginTemplateOverlay(plugin, context):
        rendered = dict(plugin.config)

    # Assert
    actual = (
        rendered,
        plugin.config,
    )
    expected = (
        {"path": "./data/sales", "region": "us-east"},
        {"path": "./data/{{domain}}", "region": "{{region}}"},
    )
    assert actual == expected


def test_overlay_should_handle_nested_list_templates():
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

    # Assert
    actual = (
        rendered,
        plugin.paths,
    )
    expected = (
        ["./prod/data", "./output/sales"],
        ["./{{env}}/data", "./output/{{domain}}"],
    )
    assert actual == expected


def test_overlay_should_handle_nested_plugins():
    # Arrange
    plugin = PlugIn()
    plugin.inner = PlugIn()
    plugin.inner.path = "{{domain}}/inner"
    context = {"domain": "sales"}

    # Act
    with PluginTemplateOverlay(plugin, context):
        rendered = plugin.inner.path

    # Assert
    actual = (
        rendered,
        plugin.inner.path,
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

    # Assert
    actual = (
        rendered,
        plugin.name,
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


def test_overlay_should_handle_complex_templates():
    # Arrange
    plugin = PlugIn()
    plugin.path = "./data/{{domain}}/{{year}}-{{month}}-{{day}}/file.txt"
    context = {"domain": "sales", "year": "2024", "month": "01", "day": "15"}

    # Act
    with PluginTemplateOverlay(plugin, context):
        rendered = plugin.path

    # Assert
    actual = (
        rendered,
        plugin.path,
    )
    expected = (
        "./data/sales/2024-01-15/file.txt",
        "./data/{{domain}}/{{year}}-{{month}}-{{day}}/file.txt",
    )
    assert actual == expected


def test_overlay_should_handle_empty_context():
    # Arrange
    plugin = PlugIn()
    plugin.path = "./data/static"
    context = {}

    # Act
    with PluginTemplateOverlay(plugin, context):
        rendered = plugin.path

    # Assert
    actual = (
        rendered,
        plugin.path,
    )
    expected = (
        "./data/static",
        "./data/static",
    )
    assert actual == expected


def test_overlay_should_handle_deeply_nested_structures():
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

    # Assert
    actual = (
        rendered,
        plugin.config,
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
    [42, True, False, 3.14, None],
)
def test_overlay_should_not_modify_non_string_values(value):
    # Arrange
    plugin = PlugIn()
    plugin.value = value
    context = {}

    # Act
    with PluginTemplateOverlay(plugin, context):
        rendered = plugin.value

    # Assert
    actual = (
        rendered,
        plugin.value,
    )
    expected = (
        value,
        value,
    )
    assert actual == expected


def test_overlay_should_handle_multiple_overlays_sequentially():
    # Arrange
    plugin = PlugIn()
    plugin.path = "./data/{{domain}}"

    # Act
    with PluginTemplateOverlay(plugin, {"domain": "sales"}):
        rendered_1 = plugin.path

    with PluginTemplateOverlay(plugin, {"domain": "finance"}):
        rendered_2 = plugin.path

    # Assert
    actual = (
        rendered_1,
        rendered_2,
        plugin.path,
    )
    expected = (
        "./data/sales",
        "./data/finance",
        "./data/{{domain}}",
    )
    assert actual == expected


def test_overlay_should_handle_jinja2_filters():
    # Arrange
    plugin = PlugIn()
    plugin.path = "./data/{{domain|upper}}"
    context = {"domain": "sales"}

    # Act
    with PluginTemplateOverlay(plugin, context):
        rendered = plugin.path

    # Assert
    actual = (
        rendered,
        plugin.path,
    )
    expected = (
        "./data/SALES",
        "./data/{{domain|upper}}",
    )
    assert actual == expected


def test_overlay_should_handle_jinja2_expressions():
    # Arrange
    plugin = PlugIn()
    plugin.path = "./data/{{ domain ~ '/' ~ date }}"
    context = {"domain": "sales", "date": "2024-01-15"}

    # Act
    with PluginTemplateOverlay(plugin, context):
        rendered = plugin.path

    # Assert
    actual = (
        rendered,
        plugin.path,
    )
    expected = (
        "./data/sales/2024-01-15",
        "./data/{{ domain ~ '/' ~ date }}",
    )
    assert actual == expected
