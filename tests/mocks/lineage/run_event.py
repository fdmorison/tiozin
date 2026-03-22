import pendulum

from tiozin.api.metadata.lineage.model import (
    LineageJob,
    LineageParentRun,
    LineageRunEvent,
    LineageRunEventType,
)

_2024_01_01 = pendulum.datetime(2024, 1, 1, tz="UTC")

job_start_event = LineageRunEvent(
    type=LineageRunEventType.START,
    timestamp=_2024_01_01,
    run_id="job_018f1a2b-3c4d-7e8f-9a0b-1c2d3e4f5a6b",
    producer="tiozin/test",
    nominal_time=_2024_01_01,
    job=LineageJob(
        namespace="acme.latam.ecommerce.checkout.raw",
        name="test_job",
        job_type="JobStub",
        processing_type="BATCH",
        integration="test_runner",
    ),
    parent=None,
    inputs=[],
    outputs=[],
    tags={"org": "acme", "layer": "raw"},
)

step_start_event = LineageRunEvent(
    type=LineageRunEventType.START,
    timestamp=_2024_01_01,
    run_id="step_aabbccdd-eeff-0011-2233-445566778899",
    producer="tiozin/test",
    nominal_time=_2024_01_01,
    job=LineageJob(
        namespace="acme.latam.ecommerce.checkout.raw",
        name="test_input",
        job_type="InputStub",
        processing_type="BATCH",
        integration="test_runner",
    ),
    parent=LineageParentRun(
        run_id="job_018f1a2b-3c4d-7e8f-9a0b-1c2d3e4f5a6b",
        job_name="test_job",
        namespace="acme.latam.ecommerce.checkout.raw",
    ),
    inputs=[],
    outputs=[],
    tags={"org": "acme", "layer": "raw"},
)
