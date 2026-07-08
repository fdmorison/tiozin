"""
Shared documentation for the batch CLI.
"""

JOB = """
The unique identifier of the job.

Used to locate the batches associated with the job.
"""

BATCH_ID = """
The unique identifier of the batch.
"""

NOMINAL_TIME = """
The nominal execution time of the batch.

The nominal time uniquely identifies a batch within a job. It represents
the logical execution window independently of when the batch was
registered or processed.

The value must be an ISO 8601 datetime.
"""

LIMIT = """
The maximum number of batches to show.
"""

SINCE = """
Only include batches registered on or after this timestamp.

The value must be an ISO 8601 datetime.
"""

ATTRIBUTES = """
Custom batch attributes.

Provide each attribute as `key=value`. Multiple attributes may be
provided. Existing values with the same key are overwritten.
"""
