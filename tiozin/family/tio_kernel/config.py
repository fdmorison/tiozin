# ===============================================
#           Iceberg Batch Registry
# ===============================================
iceberg_default_database = "default"
iceberg_default_table = "tiozin_batches"

iceberg_default_catalog = "tiozin"
iceberg_default_catalog_type = "sqlite"

iceberg_default_snapshot_retention_days = 30

iceberg_default_table_properties = {
    "format-version": "2",
    "history.expire.min-snapshots-to-keep": "7",
}
