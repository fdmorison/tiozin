import logging
from zoneinfo import ZoneInfo

# ===============================================
#           General
# ===============================================
artifact_name = "tiozin"
artifact_version = "test"

# ===============================================
#           API
# ===============================================
app_name = "tiozin"
app_title = "Tiozin"
app_version = artifact_version
app_host = "test"
app_description = "Test"
app_timezone = ZoneInfo("UTC")

# ===============================================
#           Logging
# ===============================================
log_level = logging.WARNING
log_level_name = logging._levelToName[log_level]
log_date_format = "iso"
log_json = False
log_json_ensure_ascii = False

# ===============================================
#           Plugins
# ===============================================
plugin_provider_group = "tiozin.family"
plugin_provider_prefixes = ["tio_", "tia_"]
plugin_provider_unknown = "tio_unknown"
