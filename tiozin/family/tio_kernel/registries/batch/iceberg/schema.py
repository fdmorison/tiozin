"""
Iceberg schema for the batch registry table.

Columns are declared by name using a PyArrow schema. Iceberg assigns the field IDs
it embeds in every data file at creation time, so no ID is chosen by hand. Partition,
sort, and identifier fields are referenced by name in the registry's create-table
transaction.

`attributes` is stored as a JSON-encoded string rather than a typed struct, so its
keys can vary freely between batches without requiring schema evolution.
"""

import pyarrow as pa

String = pa.string()
Integer = pa.int32()
Timestamptz = pa.timestamp("us", tz="UTC")
StringMap = pa.map_(String, String)


IcebergStateSchema = pa.struct(
    [
        pa.field("start", Timestamptz, nullable=True),
        pa.field("end", Timestamptz, nullable=True),
        pa.field("watermarks", StringMap, nullable=True),
    ]
)


IcebergBatchSchema = pa.schema(
    [
        pa.field("id", String, nullable=False),
        pa.field("org", String, nullable=False),
        pa.field("region", String, nullable=False),
        pa.field("domain", String, nullable=False),
        pa.field("subdomain", String, nullable=False),
        pa.field("layer", String, nullable=False),
        pa.field("product", String, nullable=False),
        pa.field("model", String, nullable=False),
        pa.field("nominal_time", Timestamptz, nullable=False),
        pa.field("status", String, nullable=False),
        pa.field("attempts", Integer, nullable=False),
        pa.field("state", IcebergStateSchema, nullable=False),
        pa.field("attributes", String, nullable=False),
        pa.field("created_at", Timestamptz, nullable=False),
        pa.field("updated_at", Timestamptz, nullable=False),
    ]
)
