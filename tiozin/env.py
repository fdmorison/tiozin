import logging
import socket
from pathlib import Path

from environs import Env

# ===============================================
#           Load environment variables
# ===============================================
# System-wide
_env = Env(expand_vars=True)
_env.read_env("/etc/tiozin/.env", recurse=False)

# User-level
_env.read_env(Path.home() / ".env", recurse=False)
_env.read_env(Path.home() / ".config/tiozin/.env", recurse=False)

# Container / mount
_env.read_env("/config/.env", recurse=False)
_env.read_env("/tiozin/.env", recurse=False)

# Project-level (PWD + parents)
_env.read_env(recurse=True)

# ===============================================
#           General
# ===============================================
# HOSTNAME - The application's hostname, also used as POD_NAME in K8S.
HOSTNAME = _env("HOSTNAME", socket.gethostname() or "localhost")

# ===============================================
#           Logging
# ===============================================
# LOG_LEVEL - The logging level for the application.
LOG_LEVEL = _env.log_level("LOG_LEVEL", logging.INFO)

# TIO_LOG_DATE_FORMAT - The date format for log timestamps.
TIO_LOG_DATE_FORMAT = _env.str("TIO_LOG_DATE_FORMAT", "iso")

# TIO_LOG_JSON - Enable JSON logging format.
TIO_LOG_JSON = _env.bool("TIO_LOG_JSON", False)

# TIO_LOG_JSON_ENSURE_ASCII - Ensure ASCII encoding in JSON logs.
TIO_LOG_JSON_ENSURE_ASCII = _env.bool("TIO_LOG_JSON_ENSURE_ASCII", False)

# TIO_LOG_SHOW_LOCALS - Show local variables in exception tracebacks.
TIO_LOG_SHOW_LOCALS = _env.bool("TIO_LOG_SHOW_LOCALS", False)

# TIO_LOG_REDACT_MIN_LENGTH - Minimum secret length to qualify for redaction in logs.
TIO_LOG_REDACT_MIN_LENGTH = _env.int("TIO_LOG_REDACT_MIN_LENGTH", 3)

# ===============================================
#           Registry configurations (all attribute defaults are null)
# ===============================================
TIO_SETTING_REGISTRY_KIND = _env.str("TIO_SETTING_REGISTRY_KIND", "tio_kernel:FileSettingRegistry")
TIO_SETTING_REGISTRY_LOCATION = _env.str("TIO_SETTING_REGISTRY_LOCATION", None)
TIO_SETTING_REGISTRY_TIMEOUT = _env.int("TIO_SETTING_REGISTRY_TIMEOUT", None)
TIO_SETTING_REGISTRY_READONLY = _env.bool("TIO_SETTING_REGISTRY_READONLY", None)
TIO_SETTING_REGISTRY_CACHE = _env.bool("TIO_SETTING_REGISTRY_CACHE", None)

TIO_JOB_REGISTRY_KIND = _env.str("TIO_JOB_REGISTRY_KIND", "tio_kernel:FileJobRegistry")
TIO_JOB_REGISTRY_LOCATION = _env.str("TIO_JOB_REGISTRY_LOCATION", None)
TIO_JOB_REGISTRY_TIMEOUT = _env.int("TIO_JOB_REGISTRY_TIMEOUT", None)
TIO_JOB_REGISTRY_READONLY = _env.bool("TIO_JOB_REGISTRY_READONLY", None)
TIO_JOB_REGISTRY_CACHE = _env.bool("TIO_JOB_REGISTRY_CACHE", None)

TIO_SCHEMA_REGISTRY_KIND = _env.str("TIO_SCHEMA_REGISTRY_KIND", "tio_kernel:NoOpSchemaRegistry")
TIO_SCHEMA_REGISTRY_LOCATION = _env.str("TIO_SCHEMA_REGISTRY_LOCATION", None)
TIO_SCHEMA_REGISTRY_TIMEOUT = _env.int("TIO_SCHEMA_REGISTRY_TIMEOUT", None)
TIO_SCHEMA_REGISTRY_READONLY = _env.bool("TIO_SCHEMA_REGISTRY_READONLY", None)
TIO_SCHEMA_REGISTRY_CACHE = _env.bool("TIO_SCHEMA_REGISTRY_CACHE", None)

TIO_SECRET_REGISTRY_KIND = _env.str("TIO_SECRET_REGISTRY_KIND", "tio_kernel:EnvSecretRegistry")
TIO_SECRET_REGISTRY_LOCATION = _env.str("TIO_SECRET_REGISTRY_LOCATION", None)
TIO_SECRET_REGISTRY_TIMEOUT = _env.int("TIO_SECRET_REGISTRY_TIMEOUT", None)
TIO_SECRET_REGISTRY_READONLY = _env.bool("TIO_SECRET_REGISTRY_READONLY", None)
TIO_SECRET_REGISTRY_CACHE = _env.bool("TIO_SECRET_REGISTRY_CACHE", None)

TIO_TRANSACTION_REGISTRY_KIND = _env.str(
    "TIO_TRANSACTION_REGISTRY_KIND", "tio_kernel:NoOpTransactionRegistry"
)
TIO_TRANSACTION_REGISTRY_LOCATION = _env.str("TIO_TRANSACTION_REGISTRY_LOCATION", None)
TIO_TRANSACTION_REGISTRY_TIMEOUT = _env.int("TIO_TRANSACTION_REGISTRY_TIMEOUT", None)
TIO_TRANSACTION_REGISTRY_READONLY = _env.bool("TIO_TRANSACTION_REGISTRY_READONLY", None)
TIO_TRANSACTION_REGISTRY_CACHE = _env.bool("TIO_TRANSACTION_REGISTRY_CACHE", None)

TIO_LINEAGE_REGISTRY_KIND = _env.str("TIO_LINEAGE_REGISTRY_KIND", "tio_kernel:NoOpLineageRegistry")
TIO_LINEAGE_REGISTRY_LOCATION = _env.str("TIO_LINEAGE_REGISTRY_LOCATION", None)
TIO_LINEAGE_REGISTRY_TIMEOUT = _env.int("TIO_LINEAGE_REGISTRY_TIMEOUT", None)
TIO_LINEAGE_REGISTRY_READONLY = _env.bool("TIO_LINEAGE_REGISTRY_READONLY", None)
TIO_LINEAGE_REGISTRY_CACHE = _env.bool("TIO_LINEAGE_REGISTRY_CACHE", None)

TIO_METRIC_REGISTRY_KIND = _env.str("TIO_METRIC_REGISTRY_KIND", "tio_kernel:NoOpMetricRegistry")
TIO_METRIC_REGISTRY_LOCATION = _env.str("TIO_METRIC_REGISTRY_LOCATION", None)
TIO_METRIC_REGISTRY_TIMEOUT = _env.int("TIO_METRIC_REGISTRY_TIMEOUT", None)
TIO_METRIC_REGISTRY_READONLY = _env.bool("TIO_METRIC_REGISTRY_READONLY", None)
TIO_METRIC_REGISTRY_CACHE = _env.bool("TIO_METRIC_REGISTRY_CACHE", None)
