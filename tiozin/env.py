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
