import logging
import socket

from environs import Env

_env = Env(expand_vars=True)
_env.read_env()

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
