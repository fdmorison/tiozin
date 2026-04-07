"""
Integration tests for schema_subject behavior.
"""

from unittest.mock import ANY, patch

import pytest

from tiozin import Schema, TiozinApp
from tiozin.family.tio_kernel import NoOpSchemaRegistry

_SCHEMA = Schema.from_file("tests/mocks/schemas/user/tiozin.odcs.yaml")


@pytest.fixture
def app():
    tiozin_app = TiozinApp()
    tiozin_app.setup()
    yield tiozin_app
    tiozin_app.teardown()


# ============================================================================
# DEFAULT
# ============================================================================


@patch("tiozin.app.signal")
@patch("tiozin.app.atexit")
def test_app_should_not_get_schema_subject_by_default(_atexit, _signal, app: TiozinApp):
    # Arrange
    yaml_job = """
        kind: LinearJob
        name: default_behavior
        org: acme
        region: us
        domain: sales
        subdomain: orders
        layer: raw
        product: crm
        model: daily
        runner:
          kind: NoOpRunner
        inputs:
          - kind: NoOpInput
            name: read_orders
        transforms:
          - kind: NoOpTransform
            name: aggregate
        outputs:
          - kind: NoOpOutput
            name: write_orders
    """

    # Act
    with patch.object(NoOpSchemaRegistry, "get") as schema_registry_get:
        app.run(yaml_job)

    # Assert
    schema_registry_get.assert_not_called()


@patch("tiozin.app.signal")
@patch("tiozin.app.atexit")
def test_app_should_get_schema_subject_when_explicitly_provided(_atexit, _signal, app: TiozinApp):
    # Arrange
    yaml_job = """
        kind: LinearJob
        name: explicit_behavior
        org: acme
        region: us
        domain: sales
        subdomain: orders
        layer: raw
        product: crm
        model: daily
        runner:
          kind: NoOpRunner
        inputs:
          - kind: NoOpInput
            name: read_orders
            schema_subject: my_input_schema_subject
        transforms:
          - kind: NoOpTransform
            name: aggregate
            schema_subject: my_transform_schema_subject
        outputs:
          - kind: NoOpOutput
            name: write_orders
            schema_subject: my_output_schema_subject
    """

    # Act
    with patch.object(NoOpSchemaRegistry, "get", return_value=_SCHEMA) as schema_registry_get:
        app.run(yaml_job)

    # Assert
    actual = schema_registry_get.call_args_list
    expected = [
        (("my_input_schema_subject", ANY),),
        (("my_transform_schema_subject", ANY),),
        (("my_output_schema_subject", ANY),),
    ]
    assert actual == expected


# ============================================================================
# AUTO
# ============================================================================


@patch("tiozin.app.signal")
@patch("tiozin.app.atexit")
def test_app_should_get_auto_schema_subject_when_explicitly_provided(
    _atexit, _signal, app: TiozinApp
):
    # Arrange
    yaml_job = """
        kind: LinearJob
        name: auto_behavior
        org: acme
        region: us
        domain: sales
        subdomain: orders
        layer: raw
        product: crm
        model: daily
        runner:
          kind: NoOpRunner
        inputs:
          - kind: NoOpInput
            name: read_orders
            schema_subject: auto
        transforms:
          - kind: NoOpTransform
            name: aggregate
            schema_subject: auto
        outputs:
          - kind: NoOpOutput
            name: write_orders
            schema_subject: auto
    """

    # Act
    with patch.object(NoOpSchemaRegistry, "get", return_value=_SCHEMA) as schema_registry_get:
        app.run(yaml_job)

    # Assert
    actual = schema_registry_get.call_args_list
    expected = [
        (("acme.us.sales.orders.raw.crm.daily", ANY),),
        (("acme.us.sales.orders.raw.crm.daily", ANY),),
        (("acme.us.sales.orders.raw.crm.daily", ANY),),
    ]
    assert actual == expected
