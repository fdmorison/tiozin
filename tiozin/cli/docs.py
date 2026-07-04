JOB = """
The unique identifier of the job.

Used to resolve the job manifest and identify the batches associated with it.
"""

BATCH_ID = """
The unique identifier of the batch.
"""

NOMINAL_TIME = """
The nominal execution time represented by the batch.

The nominal time uniquely identifies a batch within a job. It represents
the logical execution window independently of when the batch was
registered or processed.

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
Custom batch attributes.

Each attribute must be provided as `key=value`. Multiple attributes may be
provided. Existing values with the same key are overwritten.
"""
