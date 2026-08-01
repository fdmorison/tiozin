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
BATCH_REGISTRY_RETRIES = (
    "Maximum number of times a failed batch is retried before being escalated to QUARANTINED. "
    "Default: 3"
)
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
INPUT_SCHEMA = "The schema definition of input data (optional)"
INPUT_SCHEMA_SUBJECT = "Schema registry subject name (optional)"
INPUT_SCHEMA_VERSION = "Specific schema version (optional)"

# TransformManifest
TRANSFORM_NAME = "Unique identifier for this transform within the job"
TRANSFORM_DESCRIPTION = "Short description of the transformation logic (optional)"
TRANSFORM_SCHEMA_SUBJECT = "Schema registry subject name (optional)"
TRANSFORM_SCHEMA_VERSION = "Specific schema version (optional)"

# OutputManifest
OUTPUT_NAME = "Unique identifier for this output within the job"
OUTPUT_DESCRIPTION = "Short description of the data destination (optional)"
OUTPUT_SCHEMA_SUBJECT = "Schema registry subject name (optional)"
OUTPUT_SCHEMA_VERSION = "Specific schema version (optional)"

# JobManifest - Identity & Ownership
JOB_NAME = "Unique name for the job (it is not the execution ID)"
JOB_DESCRIPTION = "Short description of the pipeline (optional)"
JOB_CADENCE = "Frequency at which the job runs (defaults to minutely)"
JOB_MAX_BATCHES_PER_RUN = "Maximum number of batches consumed per job execution (defaults to 1)"
JOB_BACKLOG_POLICY = (
    "Where the job gets its batches: stateless, incremental, or consumer (defaults to stateless)"
)
JOB_RUNNER = "Runtime environment where the job runs"
JOB_INPUTS = "Sources that provide data to the job"
JOB_TRANSFORMS = "Steps that modify the data (defaults  to empty list)"
JOB_OUTPUTS = "Destinations where data is written (defaults  to empty list)"
