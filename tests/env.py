import logging

# ===============================================
#           General
# ===============================================
HOSTNAME = "localhost"

# ===============================================
#           Logging
# ===============================================
LOG_LEVEL = logging.WARNING
TIO_LOG_DATE_FORMAT = "iso"
TIO_LOG_JSON = False
TIO_LOG_JSON_ENSURE_ASCII = False
TIO_LOG_SHOW_LOCALS = False

# ===============================================
#           Registry configurations
# ===============================================
TIO_SETTING_REGISTRY_KIND = "tio_kernel:FileSettingRegistry"
TIO_SETTING_REGISTRY_LOCATION = "tests/mocks/settings/default.yaml"
TIO_SETTING_REGISTRY_TIMEOUT = None
TIO_SETTING_REGISTRY_READONLY = None
TIO_SETTING_REGISTRY_CACHE = None

TIO_JOB_REGISTRY_KIND = "tio_kernel:FileJobRegistry"
TIO_JOB_REGISTRY_LOCATION = None
TIO_JOB_REGISTRY_TIMEOUT = None
TIO_JOB_REGISTRY_READONLY = None
TIO_JOB_REGISTRY_CACHE = None

TIO_SECRET_REGISTRY_KIND = "tio_kernel:NoOpSecretRegistry"
TIO_SECRET_REGISTRY_LOCATION = None
TIO_SECRET_REGISTRY_TIMEOUT = None
TIO_SECRET_REGISTRY_READONLY = None
TIO_SECRET_REGISTRY_CACHE = None

TIO_LINEAGE_REGISTRY_KIND = "tio_kernel:NoOpLineageRegistry"
TIO_LINEAGE_REGISTRY_LOCATION = None
TIO_LINEAGE_REGISTRY_TIMEOUT = None
TIO_LINEAGE_REGISTRY_READONLY = None
TIO_LINEAGE_REGISTRY_CACHE = None

TIO_SCHEMA_REGISTRY_KIND = "tio_kernel:NoOpSchemaRegistry"
TIO_SCHEMA_REGISTRY_LOCATION = None
TIO_SCHEMA_REGISTRY_TIMEOUT = None
TIO_SCHEMA_REGISTRY_READONLY = None
TIO_SCHEMA_REGISTRY_CACHE = None

TIO_TRANSACTION_REGISTRY_KIND = "tio_kernel:NoOpTransactionRegistry"
TIO_TRANSACTION_REGISTRY_LOCATION = None
TIO_TRANSACTION_REGISTRY_TIMEOUT = None
TIO_TRANSACTION_REGISTRY_READONLY = None
TIO_TRANSACTION_REGISTRY_CACHE = None

TIO_METRIC_REGISTRY_KIND = "tio_kernel:NoOpMetricRegistry"
TIO_METRIC_REGISTRY_LOCATION = None
TIO_METRIC_REGISTRY_TIMEOUT = None
TIO_METRIC_REGISTRY_READONLY = None
TIO_METRIC_REGISTRY_CACHE = None
