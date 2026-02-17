import pytest

from tests.stubs.input import InputStub
from tests.stubs.output import OutputStub
from tests.stubs.runner import RunnerStub
from tests.stubs.transform import TransformStub
from tiozin import Input, Output, Runner, Transform
from tiozin.compose.reflection import detect_family, detect_role


# ============================================================================
# Testing detect_role()
# ============================================================================
@pytest.mark.parametrize(
    "tiozin_class,expected_role",
    [
        (InputStub, Input),
        (OutputStub, Output),
        (TransformStub, Transform),
        (RunnerStub, Runner),
    ],
)
def test_detect_role_should_return_role_class(tiozin_class: type, expected_role: type):
    # Act
    result = detect_role(tiozin_class)

    # Assert
    actual = result
    expected = expected_role
    assert actual == expected


def test_detect_role_should_raise_type_error_when_not_a_class():
    # Arrange
    not_a_class = "string"

    # Act & Assert
    with pytest.raises(TypeError, match="Expected a Tiozin subclass"):
        detect_role(not_a_class)


def test_detect_role_should_raise_type_error_when_not_a_tiozin_subclass():
    # Arrange
    class NotATiozin:
        pass

    # Act & Assert
    with pytest.raises(TypeError, match="Expected a Tiozin subclass"):
        detect_role(NotATiozin)


# ============================================================================
# Testing detect_family()
# ============================================================================
def test_detect_family_should_return_unknown_when_no_prefix_matches():
    # Act
    result = detect_family(InputStub)

    # Assert
    actual = result
    expected = "tio_unknown"
    assert actual == expected
