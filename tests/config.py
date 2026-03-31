import logging
from pathlib import Path
from tempfile import gettempdir
from zoneinfo import ZoneInfo

from tests import env

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
app_identifier = f"{app_name}/{app_version}"
app_host = env.HOSTNAME
app_description = "Test"
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
log_redact_min_length = env.TIO_LOG_REDACT_MIN_LENGTH
# ===============================================
#           Tiozin Plugins
# ===============================================
tiozin_family_group = "tiozin.family"
tiozin_family_prefixes = ["tio_", "tia_"]
tiozin_family_unknown = "tio_unknown"

# ===============================================
#           Tiozin Registries
# ===============================================
registry_default_timeout = 3
registry_default_readonly = False
registry_default_cache = False

# ===============================================
#           Tiozin Configs
# ===============================================
tiozin_lineage_job_enabled = env.TIO_LINEAGE_JOB_ENABLED
tiozin_lineage_step_enabled = env.TIO_LINEAGE_STEP_ENABLED
tiozin_job_namespace_template = env.TIO_JOB_NAMESPACE_TEMPLATE
tiozin_schema_subject_template = env.TIO_SCHEMA_SUBJECT_TEMPLATE
tiozin_schema_default_version = env.TIO_SCHEMA_DEFAULT_VERSION
tiozin_settings_search_paths = ()
