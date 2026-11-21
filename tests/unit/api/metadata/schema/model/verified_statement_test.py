import pytest

from tiozin.api.metadata.schema.model import VerifiedStatement
from tiozin.exceptions import ModelError


def test_verified_statement_should_hold_question():
    # Act
    result = VerifiedStatement(question="How many orders?")

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {"question": "How many orders?"}
    assert actual == expected


def test_verified_statement_should_raise_model_error_when_question_is_missing():
    # Act / Assert
    with pytest.raises(ModelError):
        VerifiedStatement()
