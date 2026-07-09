from pathlib import Path
from unittest.mock import MagicMock, patch

from tiozin.family.tio_kernel.registries.batch.iceberg.catalogs import IcebergCatalogFactory


# ============================================================================
# IcebergCatalogFactory.build()
# ============================================================================
@patch.object(IcebergCatalogFactory, "_dummy", create=True)
def test_build_should_resolve_factory_method_by_type(dummy: MagicMock):
    # Arrange
    dummy.return_value = {
        "type": "dummy",
    }

    # Act
    result = IcebergCatalogFactory.build("dummy", "s3://bucket/lake")

    # Assert
    actual = result
    expected = {
        "type": "dummy",
    }
    assert actual == expected


@patch.object(IcebergCatalogFactory, "_dummy", create=True)
def test_build_should_resolve_factory_method_when_options_are_provided(dummy: MagicMock):
    # Arrange
    dummy.return_value = {
        "type": "dummy",
        "extra": 12345,
    }

    # Act
    result = IcebergCatalogFactory.build("dummy", "s3://bucket/lake", extra=12345)

    # Assert
    actual = result
    expected = {
        "type": "dummy",
        "extra": 12345,
    }
    assert actual == expected


def test_build_should_fallback_when_catalog_type_has_no_factory_method():
    # Act
    result = IcebergCatalogFactory.build("unknown", "s3://bucket/lake")

    # Assert
    actual = result
    expected = {
        "type": "unknown",
    }
    assert actual == expected


# ============================================================================
# IcebergCatalogFactory.build() --> _sqlite
# ============================================================================
def test_build_should_resolve_sqlite_catalog(tmp_path: Path):
    # Act
    result = IcebergCatalogFactory.build("sqlite", str(tmp_path))

    # Assert
    actual = result
    expected = {
        "type": "sql",
        "uri": f"sqlite:///{tmp_path}/catalog.db",
        "warehouse": f"file://{tmp_path}",
    }
    assert actual == expected


# ============================================================================
# IcebergCatalogFactory.build() --> _rest
# ============================================================================
def test_build_should_resolve_rest_catalog():
    # Act
    result = IcebergCatalogFactory.build("rest", "https://catalog.example.com")

    # Assert
    actual = result
    expected = {
        "type": "rest",
        "uri": "https://catalog.example.com",
    }
    assert actual == expected
