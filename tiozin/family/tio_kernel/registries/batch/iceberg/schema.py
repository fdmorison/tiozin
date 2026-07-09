"""
Iceberg schema for the batch registry table.

Field IDs are permanent identifiers embedded in every data file. Once a table exists,
changing or reusing an ID will cause existing data to be misread. To add a new column,
always assign a new ID higher than all existing ones.

`attributes` is stored as a JSON-encoded string rather than a typed struct, so its
keys can vary freely between batches without requiring schema evolution.

Next available ID: 21
"""

from pyiceberg.partitioning import PartitionField, PartitionSpec
from pyiceberg.schema import Schema as IcebergSchema
from pyiceberg.transforms import IdentityTransform
from pyiceberg.types import (
    IntegerType,
    MapType,
    NestedField,
    StringType,
    StructType,
    TimestamptzType,
)

from tiozin.api.conventions import RESOURCE_FIELDS

ID_INDEX = 1
ORG_INDEX = 2
REGION_INDEX = 3
DOMAIN_INDEX = 4
SUBDOMAIN_INDEX = 5
LAYER_INDEX = 6
PRODUCT_INDEX = 7
MODEL_INDEX = 8
NOMINAL_TIME_INDEX = 9
STATUS_INDEX = 10
FAILURE_COUNT_INDEX = 11
STATE_INDEX = 12
STATE_START_INDEX = 13
STATE_END_INDEX = 14
STATE_WATERMARKS_INDEX = 15
STATE_WATERMARKS_KEY_INDEX = 16
STATE_WATERMARKS_VALUE_INDEX = 17
ATTRIBUTES_INDEX = 18
CREATED_AT_INDEX = 19
UPDATED_AT_INDEX = 20

IcebergBatchSchema = IcebergSchema(
    NestedField(ID_INDEX, "id", StringType(), required=True),
    NestedField(ORG_INDEX, "org", StringType(), required=True),
    NestedField(REGION_INDEX, "region", StringType(), required=True),
    NestedField(DOMAIN_INDEX, "domain", StringType(), required=True),
    NestedField(SUBDOMAIN_INDEX, "subdomain", StringType(), required=True),
    NestedField(LAYER_INDEX, "layer", StringType(), required=True),
    NestedField(PRODUCT_INDEX, "product", StringType(), required=True),
    NestedField(MODEL_INDEX, "model", StringType(), required=True),
    NestedField(NOMINAL_TIME_INDEX, "nominal_time", TimestamptzType(), required=True),
    NestedField(STATUS_INDEX, "status", StringType(), required=True),
    NestedField(FAILURE_COUNT_INDEX, "failure_count", IntegerType(), required=True),
    NestedField(
        STATE_INDEX,
        "state",
        StructType(
            NestedField(STATE_START_INDEX, "start", TimestamptzType(), required=False),
            NestedField(STATE_END_INDEX, "end", TimestamptzType(), required=False),
            NestedField(
                STATE_WATERMARKS_INDEX,
                "watermarks",
                MapType(
                    key_id=STATE_WATERMARKS_KEY_INDEX,
                    key_type=StringType(),
                    value_id=STATE_WATERMARKS_VALUE_INDEX,
                    value_type=StringType(),
                    value_required=False,
                ),
                required=False,
            ),
        ),
        required=True,
    ),
    NestedField(ATTRIBUTES_INDEX, "attributes", StringType(), required=True),
    NestedField(CREATED_AT_INDEX, "created_at", TimestamptzType(), required=True),
    NestedField(UPDATED_AT_INDEX, "updated_at", TimestamptzType(), required=True),
    identifier_field_ids=[ID_INDEX],
)

FIELD_TO_ID = {field.name: field.field_id for field in IcebergBatchSchema.fields}

IcebergBatchPartitionSpec = PartitionSpec(
    *(
        PartitionField(
            source_id=FIELD_TO_ID[field],
            field_id=1000 + index,
            transform=IdentityTransform(),
            name=field,
        )
        for index, field in enumerate(RESOURCE_FIELDS)
    )
)
