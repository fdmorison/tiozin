import pytest

from tiozin.api.runtime.input.proxy import InputProxy
from tiozin.api.runtime.output.proxy import OutputProxy
from tiozin.api.runtime.transform.proxy import TransformProxy
from tiozin.family.tio_kernel import (
    LinearJob,
    NoOpBatchRegistry,
    NoOpInput,
    NoOpOutput,
    NoOpRunner,
    NoOpTransform,
)

# ============================================================================
# Testing Tiozin.name
# ============================================================================


@pytest.mark.parametrize(
    "name,expected_name",
    [
        ("my input", "my_input"),
        ("  my input  ", "my_input"),
        ("Customer Orders", "customer_orders"),
        ("orders-2024", "orders_2024"),
        ("already_valid", "already_valid"),
    ],
)
def test_tiozin_should_normalize_name(name: str, expected_name: str):
    # Arrange / Act
    tiozin = NoOpInput(
        name=name, org="x", region="x", domain="x", subdomain="x", layer="x", product="x", model="x"
    )

    # Assert
    actual = tiozin.name
    expected = expected_name
    assert actual == expected


def test_tiozin_should_use_kind_as_name_when_name_is_not_provided():
    # Arrange / Act
    tiozin = NoOpRunner()

    # Assert
    actual = tiozin.name
    expected = "nooprunner"
    assert actual == expected


# ============================================================================
# Testing Tiozin.display_name
# ============================================================================


def test_tiozin_should_preserve_display_name():
    # Arrange / Act
    tiozin = NoOpInput(name="My Step Name")

    # Assert
    actual = (
        tiozin.display_name,
        tiozin.name,
    )
    expected = (
        "My Step Name",
        "my_step_name",
    )
    assert actual == expected


def test_tiozin_should_use_kind_as_display_name_when_name_is_not_provided():
    # Arrange / Act
    tiozin = NoOpRunner()

    # Assert
    actual = tiozin.display_name
    expected = "NoOpRunner"
    assert actual == expected


# ============================================================================
# Testing Tiozin.tioproxy
# ============================================================================
def test_tioproxy_should_return_registered_proxies():
    """tioproxy returns the proxy list registered via @tioproxy."""

    # Act
    actual = (
        NoOpInput.tioproxy,
        NoOpTransform.tioproxy,
        NoOpOutput.tioproxy,
    )

    # Assert
    expected = (
        [InputProxy],
        [TransformProxy],
        [OutputProxy],
    )
    assert actual == expected


# ============================================================================
# Testing Tiozin.to_dict
# ============================================================================
def test_to_dict_should_return_all_attributes():
    # Arrange
    tiozin = NoOpInput(
        name="test_input",
        description="A test input",
        org="acme",
        region="latam",
        domain="sales",
        subdomain="checkout",
        layer="raw",
        product="orders",
        model="transactions",
    )

    # Act
    result = tiozin.to_dict()

    # Assert
    actual = result.keys()
    expected = tiozin.__dict__.keys()
    assert actual == expected


def test_to_dict_should_exclude_fields_when_requested():
    # Arrange
    tiozin = NoOpInput(
        name="test_input",
        org="acme",
        region="latam",
        domain="sales",
        subdomain="checkout",
        layer="raw",
        product="orders",
        model="transactions",
    )

    # Act
    result = tiozin.to_dict(exclude={"name", "org"})

    # Assert
    actual = (
        "name" not in result,
        "org" not in result,
    )
    expected = (True, True)
    assert actual == expected


def test_to_dict_should_include_none_by_default():
    # Arrange
    tiozin = NoOpInput(
        name="test_input",
        description=None,
        org="acme",
        region="latam",
        domain="sales",
        subdomain="checkout",
        layer="raw",
        product="orders",
        model="transactions",
    )

    # Act
    result = tiozin.to_dict()

    # Assert
    actual = "description" in result
    expected = True
    assert actual == expected


def test_to_dict_should_exclude_none_when_requested():
    # Arrange
    tiozin = NoOpInput(
        name="test_input",
        description=None,
        org="acme",
        region="latam",
        domain="sales",
        subdomain="checkout",
        layer="raw",
        product="orders",
        model="transactions",
    )

    # Act
    result = tiozin.to_dict(exclude_none=True)

    # Assert
    actual = None in result.values()
    expected = False
    assert actual == expected


def test_to_dict_should_apply_both_filters_when_requested():
    # Arrange
    tiozin = NoOpInput(
        name="test_input",
        description=None,
        org="acme",
        region="latam",
        domain="sales",
        subdomain="checkout",
        layer="raw",
        product="orders",
        model="transactions",
    )

    # Act
    result = tiozin.to_dict(
        exclude={"org", "region"},
        exclude_none=True,
    )

    # Assert
    actual = (
        "org" not in result,
        "region" not in result,
        "description" not in result,
    )
    expected = (True, True, True)
    assert actual == expected


def test_to_dict_should_return_new_dict_each_call():
    # Arrange
    tiozin = NoOpInput(
        name="test_input",
        org="acme",
        region="latam",
        domain="sales",
        subdomain="checkout",
        layer="raw",
        product="orders",
        model="transactions",
    )

    # Act
    result1 = tiozin.to_dict()
    result2 = tiozin.to_dict()

    # Assert
    assert result1 is not result2


# ============================================================================
# Testing Tiozin.is_*
# ============================================================================
def test_is_registry_should_pass_when_role_is_registry():
    # Act
    result = NoOpBatchRegistry.is_registry()

    # Assert
    assert result


@pytest.mark.parametrize(
    "tiozin",
    [LinearJob, NoOpRunner, NoOpInput, NoOpTransform, NoOpOutput],
)
def test_is_registry_should_not_pass_when_role_is_not_registry(tiozin: type):
    # Act
    result = tiozin.is_registry()

    # Assert
    assert not result


def test_is_job_should_pass_when_role_is_job():
    # Act
    result = LinearJob.is_job()

    # Assert
    assert result


@pytest.mark.parametrize(
    "tiozin",
    [NoOpBatchRegistry, NoOpRunner, NoOpInput, NoOpTransform, NoOpOutput],
)
def test_is_job_should_not_pass_when_role_is_not_job(tiozin: type):
    # Act
    result = tiozin.is_job()

    # Assert
    assert not result


def test_is_runner_should_pass_when_role_is_runner():
    # Act
    result = NoOpRunner.is_runner()

    # Assert
    assert result


@pytest.mark.parametrize(
    "tiozin",
    [NoOpBatchRegistry, LinearJob, NoOpInput, NoOpTransform, NoOpOutput],
)
def test_is_runner_should_not_pass_when_role_is_not_runner(tiozin: type):
    # Act
    result = tiozin.is_runner()

    # Assert
    assert not result


def test_is_input_should_pass_when_role_is_input():
    # Act
    result = NoOpInput.is_input()

    # Assert
    assert result


@pytest.mark.parametrize(
    "tiozin",
    [NoOpBatchRegistry, LinearJob, NoOpRunner, NoOpTransform, NoOpOutput],
)
def test_is_input_should_not_pass_when_role_is_not_input(tiozin: type):
    # Act
    result = tiozin.is_input()

    # Assert
    assert not result


def test_is_transform_should_pass_when_role_is_transform():
    # Act
    result = NoOpTransform.is_transform()

    # Assert
    assert result


@pytest.mark.parametrize(
    "tiozin",
    [NoOpBatchRegistry, LinearJob, NoOpRunner, NoOpInput, NoOpOutput],
)
def test_is_transform_should_not_pass_when_role_is_not_transform(tiozin: type):
    # Act
    result = tiozin.is_transform()

    # Assert
    assert not result


def test_is_output_should_pass_when_role_is_output():
    # Act
    result = NoOpOutput.is_output()

    # Assert
    assert result


@pytest.mark.parametrize(
    "tiozin",
    [NoOpBatchRegistry, LinearJob, NoOpRunner, NoOpInput, NoOpTransform],
)
def test_is_output_should_not_pass_when_role_is_not_output(tiozin: type):
    # Act
    result = tiozin.is_output()

    # Assert
    assert not result
