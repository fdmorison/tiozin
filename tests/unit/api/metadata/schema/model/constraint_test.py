import pytest

from tiozin.api.metadata.schema.model import Constraint
from tiozin.exceptions import ModelError


def test_constraint_should_hold_constraint():
    # Act
    result = Constraint(constraint="Do not expose customer_id")

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {"constraint": "Do not expose customer_id"}
    assert actual == expected


def test_constraint_should_raise_model_error_when_constraint_is_missing():
    # Act / Assert
    with pytest.raises(ModelError):
        Constraint()
