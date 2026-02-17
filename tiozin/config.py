import logging
from pathlib import Path
from tempfile import gettempdir
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
app_name = "tiozin"
app_title = "Tiozin"
app_version = artifact_version
app_host = env.HOSTNAME
app_description = "Tiozin, your friendly ETL framework"
app_timezone = ZoneInfo("UTC")

app_temp_workdir = Path(gettempdir()) / app_name
app_temp_workdir.mkdir(parents=True, exist_ok=True)

# ===============================================
#           Logging
# ===============================================
log_level = env.LOG_LEVEL
log_level_name = logging._levelToName[log_level]
log_date_format = env.TIO_LOG_DATE_FORMAT
log_json = env.TIO_LOG_JSON
log_json_ensure_ascii = env.TIO_LOG_JSON_ENSURE_ASCII
log_show_locals = env.TIO_LOG_SHOW_LOCALS

# ===============================================
#           Tiozin Plugins
# ===============================================
tiozin_family_group = "tiozin.family"
tiozin_family_prefixes = ["tio_", "tia_"]
tiozin_family_unknown = "tio_unknown"
