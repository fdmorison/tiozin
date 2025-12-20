import logging
import socket

from environs import Env

_env = Env()
_env.read_env()

# ===============================================
#           General
# ===============================================
# HOSTNAME - The application's hostname, also used as POD_NAME in K8S.
HOSTNAME = _env("HOSTNAME", socket.gethostname() or "localhost")

# LOG_LEVEL - The logging level for the application.
LOG_LEVEL = _env.log_level("LOG_LEVEL", logging.INFO)
