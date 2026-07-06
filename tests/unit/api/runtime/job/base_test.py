import pytest

from tests.stubs import InputStub, JobStub, RunnerStub
from tiozin import config

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


def test_job_should_derive_namespace_from_domain_fields_when_namespace_is_not_provided(
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
    expected = "acme.latam.ecommerce.checkout"
    assert actual == expected


def test_job_should_render_namespace_template_when_namespace_is_a_jinja_string(
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
    expected = "acme-checkout"
    assert actual == expected


def test_job_should_render_namespace_from_custom_config_template(
    monkeypatch: pytest.MonkeyPatch,
    fake_domain: dict,
    fake_governance: dict,
    runner_stub: RunnerStub,
    input_stub: InputStub,
):
    # Arrange
    monkeypatch.setattr(config, "tiozin_namespace_template", "{{org}}.{{domain}}")

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
    expected = "acme.ecommerce"
    assert actual == expected
