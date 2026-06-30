"""
Iceberg schema for the state registry table.

Field IDs are permanent identifiers embedded in every data file. Once a table exists,
changing or reusing an ID will cause existing data to be misread. To add a new column,
always assign a new ID higher than all existing ones.

Next available ID: 16
"""

from pyiceberg.schema import Schema as IcebergSchema
from pyiceberg.types import MapType, NestedField, StringType, TimestamptzType

FID_ID = 1
FID_ORG = 2
FID_REGION = 3
FID_DOMAIN = 4
FID_SUBDOMAIN = 5
FID_LAYER = 6
FID_PRODUCT = 7
FID_MODEL = 8
FID_NOMINAL_TIME = 9
FID_STATUS = 10
FID_ATTRIBUTES = 11
FID_CREATED_AT = 12
FID_UPDATED_AT = 13
FID_ATTRIBUTES_KEY = 14
FID_ATTRIBUTES_VALUE = 15

IcebergBatchSchema = IcebergSchema(
    NestedField(FID_ID, "id", StringType(), required=True),
    NestedField(FID_ORG, "org", StringType(), required=True),
    NestedField(FID_REGION, "region", StringType(), required=True),
    NestedField(FID_DOMAIN, "domain", StringType(), required=True),
    NestedField(FID_SUBDOMAIN, "subdomain", StringType(), required=True),
    NestedField(FID_LAYER, "layer", StringType(), required=True),
    NestedField(FID_PRODUCT, "product", StringType(), required=True),
    NestedField(FID_MODEL, "model", StringType(), required=True),
    NestedField(FID_NOMINAL_TIME, "nominal_time", TimestamptzType(), required=True),
    NestedField(FID_STATUS, "status", StringType(), required=True),
    NestedField(
        FID_ATTRIBUTES,
        "attributes",
        MapType(
            key_id=FID_ATTRIBUTES_KEY,
            key_type=StringType(),
            value_id=FID_ATTRIBUTES_VALUE,
            value_type=StringType(),
        ),
        required=True,
    ),
    NestedField(FID_CREATED_AT, "created_at", TimestamptzType(), required=True),
    NestedField(FID_UPDATED_AT, "updated_at", TimestamptzType(), required=True),
)
