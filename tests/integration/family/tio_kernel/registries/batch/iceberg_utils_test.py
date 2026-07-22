from pathlib import Path

import pyarrow as pa
from pyiceberg.catalog import load_catalog

from tiozin.family.tio_kernel.registries.batch.iceberg.schema import IcebergBatchSchema
from tiozin.family.tio_kernel.registries.batch.iceberg.utils import create_table_if_not_exists


def test_create_table_should_evolve_existing_table_schema(tmp_path: Path):
    # Arrange: an existing table, and a schema that later gains a nullable field.
    table_id = "default.test_table"
    old_schema = IcebergBatchSchema
    new_column = pa.field("foo", pa.string(), nullable=True)
    new_schema = pa.schema([*old_schema, new_column])

    catalog = load_catalog(
        "tiozin",
        type="sql",
        uri=f"sqlite:///{tmp_path}/catalog.db",
        warehouse=f"file://{tmp_path}",
    )
    catalog.create_namespace_if_not_exists(("default",))
    create_table_if_not_exists(catalog, table_id, old_schema, 7)

    # Act
    table = create_table_if_not_exists(catalog, table_id, new_schema, 7)

    # Assert
    assert "foo" in table.schema().column_names
