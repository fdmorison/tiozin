from pathlib import Path

import pytest

from tests.mocks.schemas.user.spark import SPARK_SCHEMA
from tiozin.api.metadata.schema.model import Schema

_TIOZIN_SCHEMA_YAML = Path("tests/mocks/schemas/user/tiozin.odcs.yaml").read_text()
_TIOZIN_SCHEMA_SPARK_YAML = Path("tests/mocks/schemas/user/spark.odcs.yaml").read_text()


def test_export_should_build_spark_schema():
    # Arrange
    tiozin_schema = Schema.from_yaml(_TIOZIN_SCHEMA_YAML)

    # Act
    spark_schema = tiozin_schema.export("spark")

    # Assert
    actual = spark_schema
    expected = SPARK_SCHEMA
    assert actual == expected


def test_import_should_parse_spark_schema():
    # Arrange
    tiozin_schema = Schema.from_yaml(_TIOZIN_SCHEMA_SPARK_YAML)

    # Act
    spark_schema = Schema.import_("spark", SPARK_SCHEMA)

    # Assert
    actual = spark_schema.model_dump()
    expected = tiozin_schema.model_dump()
    assert actual == expected


@pytest.mark.xfail(
    reason="""
    datacontract-cli roundtrip is lossy. Observed example:
    - physicalType is not preserved
    - IntegerType is widened to LongType
    """,
    strict=True,
)
def test_roundtrip_should_be_lossless():
    # Arrange
    original = Schema.from_yaml(_TIOZIN_SCHEMA_SPARK_YAML)

    # Act
    restored = Schema.import_("spark", original.export("spark"))

    # Assert
    actual = restored.model_dump()
    expected = original.model_dump()
    assert actual == expected
