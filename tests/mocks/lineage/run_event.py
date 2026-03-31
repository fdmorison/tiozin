import pendulum

from tiozin.api.metadata.lineage.model import (
    LineageJob,
    LineageParentRun,
    LineageRunEvent,
)

_2024_01_01 = pendulum.datetime(2024, 1, 1, tz="UTC")

job_start_event = LineageRunEvent(
    type="START",
    timestamp=_2024_01_01,
    run_id="018f1a2b-3c4d-7e8f-9a0b-1c2d3e4f5a6b",
    producer="tiozin/test",
    nominal_time=_2024_01_01,
    job=LineageJob(
        namespace="acme.latam.ecommerce.checkout",
        name="test_job",
        type="JOB",
        processing_type="BATCH",
        integration="test_runner",
    ),
    parent=None,
    inputs=[],
    outputs=[],
    tags={"org": "acme", "layer": "raw"},
)

step_start_event = LineageRunEvent(
    type="START",
    timestamp=_2024_01_01,
    run_id="aabbccdd-eeff-0011-2233-445566778899",
    producer="tiozin/test",
    nominal_time=_2024_01_01,
    job=LineageJob(
        namespace="acme.latam.ecommerce.checkout",
        name="test_input",
        type="TASK",
        processing_type="BATCH",
        integration="test_runner",
    ),
    parent=LineageParentRun(
        run_id="018f1a2b-3c4d-7e8f-9a0b-1c2d3e4f5a6b",
        name="test_job",
        namespace="acme.latam.ecommerce.checkout",
    ),
    inputs=[],
    outputs=[],
    tags={"org": "acme", "layer": "raw"},
)
