import logging
from pathlib import Path
from zoneinfo import ZoneInfo

from single_source import get_version

from . import env

# ===============================================
#           General
# ===============================================
artifact_name = __package__
artifact_version = get_version(artifact_name, Path(__file__).parent.parent)

# ===============================================
#           API
# ===============================================
app_name = "tio-run"
app_title = "Tio Run"
app_version = artifact_version
app_host = env.HOSTNAME
app_description = "The core engine of Tio Run: Transform the Input to Output and Run :)"
app_timezone = ZoneInfo("America/Sao_Paulo")

# ===============================================
#           Logging
# ===============================================
log_level = env.LOG_LEVEL
log_level_name = logging._levelToName[log_level]
log_format = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
log_date_format = "%Y-%m-%dT%H:%M:%S%z"
