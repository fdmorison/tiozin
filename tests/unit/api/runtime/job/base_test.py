import pytest

from tests.stubs import InputStub, JobStub, RunnerStub
from tiozin.api import BacklogPolicy, Cadence

# =============================================================================
# Testing Job.namespace
# =============================================================================


def test_job_should_use_explicit_namespace_when_provided(
    fake_domain: dict,
    fake_governance: dict,
    runner_stub: RunnerStub,
    input_stub: InputStub,
):
    # Act
    job = JobStub(
        name="test_job",
        namespace="my-custom-namespace",
        runner=runner_stub,
        inputs=[input_stub],
        **fake_domain,
        **fake_governance,
    )

    # Assert
    actual = job.namespace
    expected = "my-custom-namespace"
    assert actual == expected


def test_job_should_keep_namespace_unrendered_when_namespace_is_a_jinja_template(
    fake_domain: dict,
    fake_governance: dict,
    runner_stub: RunnerStub,
    input_stub: InputStub,
):
    # Act
    job = JobStub(
        name="test_job",
        namespace="{{org}}-{{subdomain}}",
        runner=runner_stub,
        inputs=[input_stub],
        **fake_domain,
        **fake_governance,
    )

    # Assert
    actual = job.namespace
    expected = "{{org}}-{{subdomain}}"
    assert actual == expected


def test_job_should_default_namespace_to_config_template_when_not_provided(
    fake_domain: dict,
    fake_governance: dict,
    runner_stub: RunnerStub,
    input_stub: InputStub,
):
    # Act
    job = JobStub(
        name="test_job",
        runner=runner_stub,
        inputs=[input_stub],
        **fake_domain,
        **fake_governance,
    )

    # Assert
    actual = job.namespace
    expected = "{{org}}.{{region}}.{{domain}}.{{subdomain}}"
    assert actual == expected


# =============================================================================
# Testing Job.cadence
# =============================================================================


def test_job_should_default_cadence_to_minutely_when_not_provided(
    fake_domain: dict,
    fake_governance: dict,
    runner_stub: RunnerStub,
    input_stub: InputStub,
):
    # Act
    job = JobStub(
        name="test_job",
        runner=runner_stub,
        inputs=[input_stub],
        **fake_domain,
        **fake_governance,
    )

    # Assert
    actual = job.cadence
    expected = Cadence.MINUTELY
    assert actual == expected


# =============================================================================
# Testing Job.backlog_policy
# =============================================================================


@pytest.mark.parametrize(
    "backlog",
    [BacklogPolicy.INCREMENTAL, "incremental"],
)
def test_job_should_resolve_backlog(
    backlog,
    fake_domain: dict,
    fake_governance: dict,
    runner_stub: RunnerStub,
    input_stub: InputStub,
):
    # Act
    job = JobStub(
        name="test_job",
        runner=runner_stub,
        inputs=[input_stub],
        backlog_policy=backlog,
        **fake_domain,
        **fake_governance,
    )

    # Assert
    actual = job.backlog_policy
    expected = BacklogPolicy.INCREMENTAL
    assert actual == expected


def test_job_should_have_default_backlog(
    fake_domain: dict,
    fake_governance: dict,
    runner_stub: RunnerStub,
    input_stub: InputStub,
):
    # Act
    job = JobStub(
        name="test_job",
        runner=runner_stub,
        inputs=[input_stub],
        **fake_domain,
        **fake_governance,
    )

    # Assert
    actual = job.backlog_policy
    expected = BacklogPolicy.STATELESS
    assert actual == expected


# =============================================================================
# Testing Job.to_resource_dict
# =============================================================================


def test_job_should_expose_resource_fields(job_stub: JobStub):
    # Act
    result = job_stub.to_resource_dict()

    # Assert
    actual = result
    expected = {
        "org": "acme",
        "region": "latam",
        "domain": "ecommerce",
        "subdomain": "checkout",
        "layer": "raw",
        "product": "sales",
        "model": "orders",
    }
    assert actual == expected


# =============================================================================
# Testing Job.qualified_domain
# =============================================================================


def test_job_should_expose_qualified_domain(job_stub: JobStub):
    # Act
    result = job_stub.qualified_domain

    # Assert
    actual = result
    expected = "acme.latam.ecommerce"
    assert actual == expected


# =============================================================================
# Testing Job.qualified_subdomain
# =============================================================================


def test_job_should_expose_qualified_subdomain(job_stub: JobStub):
    # Act
    result = job_stub.qualified_subdomain

    # Assert
    actual = result
    expected = "acme.latam.ecommerce.checkout"
    assert actual == expected


# =============================================================================
# Testing Job.qualified_product
# =============================================================================


def test_job_should_expose_qualified_product(job_stub: JobStub):
    # Act
    result = job_stub.qualified_product

    # Assert
    actual = result
    expected = "raw.sales.orders"
    assert actual == expected
