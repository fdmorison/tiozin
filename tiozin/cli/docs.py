"""
Shared documentation for the batch CLI.
"""

JOB = """
Job identifier.

The job manifest is resolved to determine the resource whose batches will
be queried or modified.
"""

BATCH_ID = """
Batch identifier.

The identifier must belong to a batch registered for the selected job.
"""

NOMINAL_TIME = """
Nominal execution time represented by the batch.

The nominal time identifies the logical execution window of the batch,
independently of when it was registered or processed. It is commonly used
as a watermark during incremental ingestion.

The value must be provided as an ISO 8601 datetime.
"""

LIMIT = """
Maximum number of batches to return.

Results are ordered from the most recently registered batch to the oldest.
"""

SINCE = """
Only include batches registered at or after this timestamp.

The value must be provided as an ISO 8601 datetime.
"""

ATTRIBUTES = """
Additional batch attributes.

Each attribute must be provided as `key=value`. This option may be specified
multiple times. Existing attributes with the same key are overwritten.
"""
