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
#           Tiozin Customizations
# ===============================================
TIO_NAMESPACE_TEMPLATE = "{{org}}.{{region}}.{{domain}}.{{subdomain}}"
