"""Documentation strings for job manifest fields."""

# Manifest (base class)
KIND = "Type of plugin, e.g., 'spark', 'kafka', 'bigquery'"
MANIFEST_NAME = "Unique identifier for this resource"
DESCRIPTION = "Short human-friendly explanation of what this resource does"
ORG = "Organization handling the resource"
REGION = "Business region of the domain team"
DOMAIN = "Domain team handling this resource"
PRODUCT = "Data product handled by this resource"
MODEL = "Data model handled by this resource"
LAYER = "Data layer, e.g., raw, trusted, or refined"

# RunnerManifest
STREAMING = "Whether this job processes data in streaming mode"

# TransformManifest
TRANSFORM_NAME = "Unique identifier for this transform within the job"

# OutputManifest
OUTPUT_NAME = "Unique identifier for this output within the job"

# InputManifest
INPUT_NAME = "Unique identifier for this input within the job"
SCHEMA = "The schema definition of input data"
SCHEMA_SUBJECT = "Schema registry subject name"
SCHEMA_VERSION = "Specific schema version"

# JobManifest - Identity & Ownership
NAME = "Unique name for the job (it is not the execution ID)"
OWNER = "Team that required for the job"
MANTAINER = "Team that maintains this job"
COST_CENTER = "Team that pays for this job"
LABELS = "Additional metadata as key-value pairs"

# JobManifest - Business Taxonomy
JOB_ORG = "Organization producing the data product"
JOB_REGION = "Business region of the domain team"
JOB_DOMAIN = "Domain team following the Datamesh concept"
JOB_PRODUCT = "Data product being produced "
JOB_MODEL = "Data model being produced, e.g., table, topic, or collection"
JOB_LAYER = "Data layer this job represents, e.g., raw, trusted, or refined"

# JobManifest - Pipeline Components
RUNNER = "Runtime environment where the job runs"
INPUTS = "Sources that provide data to the job"
TRANSFORMS = "Steps that modify the data"
OUTPUTS = "Destinations where data is written"
