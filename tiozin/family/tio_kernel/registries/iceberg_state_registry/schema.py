from pyiceberg.schema import Schema as IcebergSchema
from pyiceberg.types import MapType, NestedField, StringType, TimestamptzType

IcebergStateSchema = IcebergSchema(
    NestedField(1, "id", StringType(), required=True),
    NestedField(2, "org", StringType(), required=True),
    NestedField(3, "region", StringType(), required=True),
    NestedField(4, "domain", StringType(), required=True),
    NestedField(5, "subdomain", StringType(), required=True),
    NestedField(6, "layer", StringType(), required=True),
    NestedField(7, "product", StringType(), required=True),
    NestedField(8, "model", StringType(), required=True),
    NestedField(9, "batch_key", StringType(), required=True),
    NestedField(10, "status", StringType(), required=True),
    NestedField(
        11,
        "attributes",
        MapType(
            key_id=14,
            key_type=StringType(),
            value_id=15,
            value_type=StringType(),
        ),
        required=True,
    ),
    NestedField(12, "created_at", TimestamptzType(), required=True),
    NestedField(13, "updated_at", TimestamptzType(), required=True),
)
