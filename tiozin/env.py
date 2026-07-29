import logging
import socket
import sys
from pathlib import Path

from environs import Env

IS_TERMINAL = sys.stdout.isatty()

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

# TIO_LOG_JSON - Enable JSON logging format. Defaults to console on a terminal, JSON otherwise.
TIO_LOG_JSON = _env.bool("TIO_LOG_JSON", not IS_TERMINAL)

# TIO_LOG_JSON_ENSURE_ASCII - Ensure ASCII encoding in JSON logs.
TIO_LOG_JSON_ENSURE_ASCII = _env.bool("TIO_LOG_JSON_ENSURE_ASCII", False)

# TIO_LOG_SHOW_LOCALS - Show local variables in exception tracebacks.
TIO_LOG_SHOW_LOCALS = _env.bool("TIO_LOG_SHOW_LOCALS", False)

# TIO_LOG_REDACT_MIN_LENGTH - Minimum secret length to qualify for redaction in logs.
TIO_LOG_REDACT_MIN_LENGTH = _env.int("TIO_LOG_REDACT_MIN_LENGTH", 3)

# ===============================================
#           Framework Settings
# ===============================================
# TIO_NAMESPACE_TEMPLATE - Jinja template for the job namespace.
# Available variables: org, region, domain, subdomain, layer, product, model.
TIO_NAMESPACE_TEMPLATE = _env.str(
    "TIO_JOB_NAMESPACE_TEMPLATE",
    "{{org}}.{{region}}.{{domain}}.{{subdomain}}",
)

# TIO_DEFAULT_MAX_BATCHES_PER_RUN - Default cap on batches consumed per job execution.
# Defaults to 1, so each batch is consumed in its own execution.
TIO_DEFAULT_MAX_BATCHES_PER_RUN = _env.int("TIO_DEFAULT_MAX_BATCHES_PER_RUN", 1)

# TIO_DEFAULT_BACKLOG_POLICY - Where a job gets its batches: `stateless`, `incremental`,
# or `consumer`. Defaults to `stateless`, so a job runs without batches.
TIO_DEFAULT_BACKLOG_POLICY = _env.str("TIO_DEFAULT_BACKLOG_POLICY", "stateless")
