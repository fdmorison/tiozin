import pytest

from tiozin import Context


@pytest.fixture()
def fake_taxonomy() -> dict:
    return dict(
        org="acme",
        region="latam",
        domain="ecommerce",
        layer="raw",
        product="sales",
        model="orders",
    )


@pytest.fixture()
def job_context(fake_taxonomy: dict) -> Context:
    return Context(
        name="test_job",
        kind="LinearJob",
        tiozin_kind="job",
        **fake_taxonomy,
        options={},
    )


@pytest.fixture()
def input_context(fake_taxonomy: dict, job_context: Context) -> Context:
    return Context(
        name="test_input",
        kind="TestInput",
        tiozin_kind="Input",
        parent=job_context,
        **fake_taxonomy,
        options={},
    )


@pytest.fixture()
def transform_context(fake_taxonomy: dict, job_context: Context) -> Context:
    return Context(
        name="test_transform",
        kind="TestTransform",
        tiozin_kind="Transform",
        parent=job_context,
        **fake_taxonomy,
        options={},
    )


@pytest.fixture()
def output_context(fake_taxonomy: dict, job_context: Context) -> Context:
    return Context(
        name="test_output",
        kind="TestOutput",
        tiozin_kind="Output",
        parent=job_context,
        **fake_taxonomy,
        options={},
    )
