import pyarrow as pa
from pyiceberg.catalog import Catalog
from pyiceberg.table import Table
from pyiceberg.table.sorting import NullOrder
from pyiceberg.transforms import IdentityTransform

from tiozin.api.conventions import RESOURCE_FIELDS

from .... import config

MILLIS_PER_DAY = 24 * 60 * 60 * 1000

PRIMARY_KEY = "id"
SORT_KEY = "created_at"
PARTITION_KEY = RESOURCE_FIELDS


def create_table_if_not_exists(
    catalog: Catalog,
    table_id: tuple[str, ...],
    schema: pa.Schema,
    retention_days: int,
) -> Table:
    table = catalog.create_table_if_not_exists(
        table_id,
        schema,
        properties={
            **config.iceberg_default_table_properties,
            "history.expire.max-snapshot-age-ms": str(retention_days * MILLIS_PER_DAY),
        },
    )

    with table.update_schema() as update:
        update.union_by_name(schema)

    if table.spec().is_unpartitioned():
        with table.transaction() as txn:
            with txn.update_schema() as update:
                update.set_identifier_fields(PRIMARY_KEY)
            with txn.update_spec() as spec:
                for field in PARTITION_KEY:
                    spec.add_identity(field)
            with txn.update_sort_order() as sort:
                sort.asc(SORT_KEY, IdentityTransform(), NullOrder.NULLS_LAST)

    return table
