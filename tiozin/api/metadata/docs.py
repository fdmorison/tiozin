"""Documentation strings for manifest fields."""

# Common fields
KIND = "Type of Tiozin plugin, e.g., 'spark', 'kafka', 'bigquery'"

# Registry Common fields
REGISTRY_NAME = "Unique identifier for this registry (optional)"
REGISTRY_LOCATION = (
    "Location of the registry backend. Accepts HTTP/HTTPS URLs, FTP URLs, local file paths, "
    "or cloud storage URIs (e.g., s3://, gs://, az://)"
)
REGISTRY_TIMEOUT = "Request timeout in seconds"
REGISTRY_READONLY = "Whether the registry rejects write operations (defaults  to False)"
REGISTRY_CACHE = "Whether to cache retrieved metadata in memory (defaults  to False)"
REGISTRY_FAILFAST = "Whether to raise an error when metadata is not found (defaults  to False)"
REGISTRY_READY = "Whether the registry has been initialized and is ready to serve requests"
REGISTRY_DESCRIPTION = "Short description of the registry (optional)"

LINEAGE_REGISTRY_EMIT_LEVEL = "Lineage emission level. VAlues: job, step or all"
SCHEMA_REGISTRY_SHOW_SCHEMA = "Print the schema to the console after retrieval. Default: false"
SCHEMA_REGISTRY_SUBJECT_TEMPLATE = (
    "Jinja template used to resolve the schema subject when none is provided. "
    "Available variables: org, region, domain, subdomain, layer, product, model"
)
SCHEMA_REGISTRY_DEFAULT_VERSION = "Default schema version when none is specified. Default: latest."


# RunnerManifest
RUNNER_NAME = "Unique identifier for this runner (optional)"
RUNNER_DESCRIPTION = "Short description of the runner's execution backend (optional)"
RUNNER_STREAMING = "Whether this runner executes streaming workloads (defaults  to False)"

# InputManifest
INPUT_NAME = "Unique identifier for this input within the job"
INPUT_DESCRIPTION = "Short description of the data source (optional)"
INPUT_ORG = "Organization owning the source data (optional)"
INPUT_REGION = "Business region of the source data domain (optional)"
INPUT_DOMAIN = "Domain team owning the source data (optional)"
INPUT_SUBDOMAIN = "Subdomain within the domain team owning the source data (optional)"
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
TRANSFORM_SUBDOMAIN = "Subdomain within the domain team owning the transformation (optional)"
TRANSFORM_PRODUCT = "Data product being transformed (optional)"
TRANSFORM_MODEL = "Data model being transformed (optional)"
TRANSFORM_LAYER = "Data layer of the transformation output (optional)"
TRANSFORM_SCHEMA_SUBJECT = "Schema registry subject name (optional)"
TRANSFORM_SCHEMA_VERSION = "Specific schema version (optional)"

# OutputManifest
OUTPUT_NAME = "Unique identifier for this output within the job"
OUTPUT_DESCRIPTION = "Short description of the data destination (optional)"
OUTPUT_ORG = "Organization owning the destination data (optional)"
OUTPUT_REGION = "Business region of the destination data domain (optional)"
OUTPUT_DOMAIN = "Domain team owning the destination (optional)"
OUTPUT_SUBDOMAIN = "Subdomain within the domain team owning the destination (optional)"
OUTPUT_PRODUCT = "Data product being produced (optional)"
OUTPUT_MODEL = "Data model being written (e.g., table, topic, collection) (optional)"
OUTPUT_LAYER = "Data layer of the destination (e.g., raw, trusted, refined) (optional)"
OUTPUT_SCHEMA_SUBJECT = "Schema registry subject name (optional)"
OUTPUT_SCHEMA_VERSION = "Specific schema version (optional)"

# JobManifest - Identity & Ownership
JOB_NAME = "Unique name for the job (it is not the execution ID)"
JOB_DESCRIPTION = "Short description of the pipeline (optional)"
JOB_OWNER = "Team that required for the job (optional)"
JOB_MAINTAINER = "Team that maintains this job (optional)"
JOB_COST_CENTER = "Team that pays for this job (optional)"
JOB_LABELS = "Additional metadata as key-value pairs (defaults  to empty dict)"
JOB_ORG = "Organization producing the data product"
JOB_REGION = "Business region of the domain team"
JOB_DOMAIN = "Domain team following the Data Mesh concept"
JOB_SUBDOMAIN = "Subdomain within the domain team producing the data product"
JOB_PRODUCT = "Data product being produced"
JOB_MODEL = "Data model being produced (e.g., table, topic, collection)"
JOB_LAYER = "Data layer this job represents (e.g., raw, trusted, refined)"
JOB_RUNNER = "Runtime environment where the job runs"
JOB_INPUTS = "Sources that provide data to the job"
JOB_TRANSFORMS = "Steps that modify the data (defaults  to empty list)"
JOB_OUTPUTS = "Destinations where data is written (defaults  to empty list)"
