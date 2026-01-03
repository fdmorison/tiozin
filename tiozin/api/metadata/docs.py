"""Documentation strings for manifest fields."""

# Common fields
KIND = "Type of plugin, e.g., 'spark', 'kafka', 'bigquery'"

# RunnerManifest
RUNNER_NAME = "Unique identifier for this runner (optional)"
RUNNER_DESCRIPTION = "Short description of the runner's execution backend (optional)"
RUNNER_STREAMING = "Whether this runner executes streaming workloads (optional, defaults to False)"

# InputManifest
INPUT_NAME = "Unique identifier for this input within the job"
INPUT_DESCRIPTION = "Short description of the data source (optional)"
INPUT_ORG = "Organization owning the source data (optional)"
INPUT_REGION = "Business region of the source data domain (optional)"
INPUT_DOMAIN = "Domain team owning the source data (optional)"
INPUT_PRODUCT = "Data product being consumed (optional)"
INPUT_MODEL = "Data model being read (e.g., table, topic, collection) (optional)"
INPUT_LAYER = "Data layer of the source (e.g., raw, trusted, refined) (optional)"
INPUT_SCHEMA = "The schema definition of input data (optional)"
INPUT_SCHEMA_SUBJECT = "Schema registry subject name (optional)"
INPUT_SCHEMA_VERSION = "Specific schema version (optional)"

# TransformManifest
TRANSFORM_NAME = "Unique identifier for this transform within the job"
TRANSFORM_DESCRIPTION = "Short description of the transformation logic (optional)"
TRANSFORM_ORG = "Organization owning the transformation logic (optional)"
TRANSFORM_REGION = "Business region of the transformation domain (optional)"
TRANSFORM_DOMAIN = "Domain team owning the transformation (optional)"
TRANSFORM_PRODUCT = "Data product being transformed (optional)"
TRANSFORM_MODEL = "Data model being transformed (optional)"
TRANSFORM_LAYER = "Data layer of the transformation output (optional)"

# OutputManifest
OUTPUT_NAME = "Unique identifier for this output within the job"
OUTPUT_DESCRIPTION = "Short description of the data destination (optional)"
OUTPUT_ORG = "Organization owning the destination data (optional)"
OUTPUT_REGION = "Business region of the destination data domain (optional)"
OUTPUT_DOMAIN = "Domain team owning the destination (optional)"
OUTPUT_PRODUCT = "Data product being produced (optional)"
OUTPUT_MODEL = "Data model being written (e.g., table, topic, collection) (optional)"
OUTPUT_LAYER = "Data layer of the destination (e.g., raw, trusted, refined) (optional)"

# JobManifest - Identity & Ownership
JOB_NAME = "Unique name for the job (it is not the execution ID)"
JOB_DESCRIPTION = "Short description of the pipeline (optional)"
JOB_OWNER = "Team that required for the job (optional)"
JOB_MAINTAINER = "Team that maintains this job (optional)"
JOB_COST_CENTER = "Team that pays for this job (optional)"
JOB_LABELS = "Additional metadata as key-value pairs (optional, defaults to empty dict)"
JOB_ORG = "Organization producing the data product"
JOB_REGION = "Business region of the domain team"
JOB_DOMAIN = "Domain team following the Data Mesh concept"
JOB_PRODUCT = "Data product being produced"
JOB_MODEL = "Data model being produced (e.g., table, topic, collection)"
JOB_LAYER = "Data layer this job represents (e.g., raw, trusted, refined)"
JOB_RUNNER = "Runtime environment where the job runs"
JOB_INPUTS = "Sources that provide data to the job"
JOB_TRANSFORMS = "Steps that modify the data (optional, defaults to empty list)"
JOB_OUTPUTS = "Destinations where data is written (optional, defaults to empty list)"
