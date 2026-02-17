import pytest

from tests.stubs.input import InputStub
from tests.stubs.job import JobStub
from tests.stubs.output import OutputStub
from tests.stubs.runner import RunnerStub
from tests.stubs.transform import TransformStub
from tiozin import Context

# --------------------------------------------------
# Taxonomy
# --------------------------------------------------


@pytest.fixture()
def fake_domain() -> dict:
    return dict(
        org="acme",
        region="latam",
        domain="ecommerce",
        layer="raw",
        product="sales",
        model="orders",
    )


@pytest.fixture()
def fake_governance() -> dict:
    return dict(
        owner="platform",
        maintainer="data-team",
        cost_center="cc-123",
        labels={"env": "test"},
    )


# --------------------------------------------------
# Stubs
# --------------------------------------------------


@pytest.fixture()
def runner_stub() -> RunnerStub:
    return RunnerStub(name="test_runner")


@pytest.fixture()
def input_stub(fake_domain: dict) -> InputStub:
    return InputStub(
        name="test_input",
        **fake_domain,
    )


@pytest.fixture()
def transform_stub(fake_domain: dict) -> TransformStub:
    return TransformStub(
        name="test_transform",
        **fake_domain,
    )


@pytest.fixture()
def output_stub(fake_domain: dict) -> OutputStub:
    return OutputStub(
        name="test_output",
        **fake_domain,
    )


@pytest.fixture()
def job_stub(
    fake_domain: dict,
    fake_governance: dict,
    runner_stub: RunnerStub,
    input_stub: InputStub,
    transform_stub: TransformStub,
    output_stub: OutputStub,
) -> JobStub:
    return JobStub(
        name="test_job",
        description="test job",
        **fake_governance,
        runner=runner_stub,
        inputs=[input_stub],
        transforms=[transform_stub],
        outputs=[output_stub],
        **fake_domain,
    )


# --------------------------------------------------
# Contexts
# --------------------------------------------------


@pytest.fixture()
def job_context(job_stub: JobStub) -> Context:
    return Context.for_job(job_stub)


@pytest.fixture()
def input_context(job_context: Context, input_stub: InputStub) -> Context:
    return job_context.for_child_step(input_stub)


@pytest.fixture()
def transform_context(job_context: Context, transform_stub: TransformStub) -> Context:
    return job_context.for_child_step(transform_stub)


@pytest.fixture()
def output_context(job_context: Context, output_stub: OutputStub) -> Context:
    return job_context.for_child_step(output_stub)
