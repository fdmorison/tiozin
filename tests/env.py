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
TIO_LOG_REDACT_MIN_LENGTH = 3

# ===============================================
#           Framework Settings
# ===============================================
TIO_NAMESPACE_TEMPLATE = "{{org}}.{{region}}.{{domain}}.{{subdomain}}"
TIO_DEFAULT_MAX_BATCHES_PER_RUN = 1
TIO_DEFAULT_BACKLOG_POLICY = "none"
