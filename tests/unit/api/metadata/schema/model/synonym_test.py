import pytest

from tiozin.api.metadata.schema.model import Synonym
from tiozin.exceptions import ModelError


def test_synonym_should_hold_synonym():
    # Act
    result = Synonym(synonym="purchases")

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {"synonym": "purchases"}
    assert actual == expected


def test_synonym_should_raise_model_error_when_synonym_is_missing():
    # Act / Assert
    with pytest.raises(ModelError):
        Synonym()
