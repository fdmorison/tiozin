import pytest

from tests.stubs import InputStub, OutputStub, RunnerStub, TransformStub
from tiozin import Input, Job, Output, Registry, Runner, Tiozin, Transform
from tiozin.compose.reflection import detect_family_name, detect_tiozin_role, is_tiozin
from tiozin.family.tio_kernel import NoOpInput


# ============================================================================
# Testing detect_role()
# ============================================================================
@pytest.mark.parametrize(
    "tiozin,role",
    [
        (InputStub, Input),
        (OutputStub, Output),
        (TransformStub, Transform),
        (RunnerStub, Runner),
    ],
)
def test_detect_tiozin_role_should_resolve_role_from_class(tiozin: type, role: type):
    # Act
    result = detect_tiozin_role(tiozin)

    # Assert
    actual = result
    expected = role
    assert actual == expected


def test_detect_tiozin_role_should_fail_when_non_class():
    # Arrange
    not_a_class = "string"

    # Act & Assert
    with pytest.raises(TypeError, match="Expected a Tiozin subclass"):
        detect_tiozin_role(not_a_class)


def test_detect_tiozin_role_should_fail_when_not_a_tiozin_subclass():
    # Arrange
    class NotATiozin:
        pass

    # Act & Assert
    with pytest.raises(TypeError, match="Expected a Tiozin subclass"):
        detect_tiozin_role(NotATiozin)


# ============================================================================
# Testing detect_family()
# ============================================================================
def test_detect_family_name_should_resolve_from_plugin_class():
    # Act
    result = detect_family_name(NoOpInput)

    # Assert
    actual = result
    expected = "tio_kernel"
    assert actual == expected


def test_detect_family_name_should_fallback_to_unknown_when_family_not_found():
    # Act
    result = detect_family_name(InputStub)

    # Assert
    actual = result
    expected = "tio_unknown"
    assert actual == expected


# ============================================================================
# Testing is_tiozin()
# ============================================================================


def test_is_tiozin_should_return_true_when_concrete_tiozin_class():
    # Act
    result = is_tiozin(InputStub)

    # Assert
    actual = result
    expected = True
    assert actual == expected


def test_is_tiozin_should_return_false_when_base_tiozin_class():
    # Act
    result = is_tiozin(Tiozin)

    # Assert
    actual = result
    expected = False
    assert actual == expected


@pytest.mark.parametrize(
    "abstrat_class",
    [Job, Runner, Input, Output, Transform, Registry],
)
def test_is_tiozin_should_return_false_when_abstract_tiozin_class(abstrat_class: type):
    # Act
    result = is_tiozin(abstrat_class)

    # Assert
    actual = result
    expected = False
    assert actual == expected


def test_is_tiozin_should_return_false_when_not_a_class():
    # Arrange
    not_a_class = "string"

    # Act
    result = is_tiozin(not_a_class)

    # Assert
    actual = result
    expected = False
    assert actual == expected


def test_is_tiozin_should_return_false_when_not_a_tiozin_subclass():
    # Arrange
    class NotATiozin:
        pass

    # Act
    result = is_tiozin(NotATiozin)

    # Assert
    actual = result
    expected = False
    assert actual == expected
