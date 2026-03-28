import pytest

from tests import env
from tests.stubs import (
    InputStub,
    JobRegistryStub,
    JobStub,
    LineageRegistryStub,
    MetricRegistryStub,
    OutputStub,
    RunnerStub,
    SchemaRegistryStub,
    SecretRegistryStub,
    SettingRegistryStub,
    TransactionRegistryStub,
    TransformStub,
)
from tiozin import Context
from tiozin.api.metadata.bundle import Registries
from tiozin.api.metadata.setting.model import (
    JobRegistryManifest,
    LineageRegistryManifest,
    MetricRegistryManifest,
    SchemaRegistryManifest,
    SecretRegistryManifest,
    SettingsManifest,
    TransactionRegistryManifest,
)

# --------------------------------------------------
# Settings
# --------------------------------------------------


@pytest.fixture()
def default_settings_manifest() -> SettingsManifest:
    return SettingsManifest(
        registries=dict(
            job=JobRegistryManifest(
                kind=env.TIO_JOB_REGISTRY_KIND,
                name="my-job-registry-1",
            ),
            schema=SchemaRegistryManifest(
                kind=env.TIO_SCHEMA_REGISTRY_KIND,
                name="my-schema-registry-1",
            ),
            secret=SecretRegistryManifest(
                kind=env.TIO_SECRET_REGISTRY_KIND,
                name="my-secret-registry-1",
            ),
            transaction=TransactionRegistryManifest(
                kind=env.TIO_TRANSACTION_REGISTRY_KIND,
                name="my-transaction-registry-1",
            ),
            lineage=LineageRegistryManifest(
                kind=env.TIO_LINEAGE_REGISTRY_KIND,
                name="my-lineage-registry-1",
            ),
            metric=MetricRegistryManifest(
                kind=env.TIO_METRIC_REGISTRY_KIND,
                name="my-metric-registry-1",
            ),
        )
    )


# --------------------------------------------------
# Taxonomy
# --------------------------------------------------


@pytest.fixture()
def fake_domain() -> dict:
    return dict(
        org="acme",
        region="latam",
        domain="ecommerce",
        subdomain="checkout",
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


@pytest.fixture()
def setting_registry_stub() -> SettingRegistryStub:
    return SettingRegistryStub()


@pytest.fixture()
def secret_registry_stub() -> SecretRegistryStub:
    return SecretRegistryStub()


@pytest.fixture()
def schema_registry_stub() -> SchemaRegistryStub:
    return SchemaRegistryStub()


@pytest.fixture()
def transaction_registry_stub() -> TransactionRegistryStub:
    return TransactionRegistryStub()


@pytest.fixture()
def job_registry_stub() -> JobRegistryStub:
    return JobRegistryStub()


@pytest.fixture()
def metric_registry_stub() -> MetricRegistryStub:
    return MetricRegistryStub()


@pytest.fixture()
def lineage_registry_stub() -> LineageRegistryStub:
    return LineageRegistryStub()


# --------------------------------------------------
# Contexts
# --------------------------------------------------


@pytest.fixture()
def job_context(job_stub: JobStub):
    registries = Registries(
        setting=SettingRegistryStub(),
        secret=SecretRegistryStub(),
        schema=SchemaRegistryStub(),
        transaction=TransactionRegistryStub(),
        job=JobRegistryStub(),
        metric=MetricRegistryStub(),
        lineage=LineageRegistryStub(),
    )
    with Context.for_job(job_stub, registries) as ctx:
        yield ctx


@pytest.fixture()
def input_context(job_context: Context, input_stub: InputStub):
    with job_context.for_child_step(input_stub) as ctx:
        yield ctx


@pytest.fixture()
def transform_context(job_context: Context, transform_stub: TransformStub):
    with job_context.for_child_step(transform_stub) as ctx:
        yield ctx


@pytest.fixture()
def output_context(job_context: Context, output_stub: OutputStub):
    with job_context.for_child_step(output_stub) as ctx:
        yield ctx
