from pathlib import Path

import pytest

from tiozin.api.metadata.job_manifest import (
    InputManifest,
    JobManifest,
    OutputManifest,
    RunnerManifest,
    TransformManifest,
)
from tiozin.exceptions import JobNotFoundError
from tiozin.family.tio_kernel import FileJobRegistry


# ============================================================================
# Access Tests
# ============================================================================
def test_get_should_read_from_public_s3_bucket():
    # Arrange
    path = "s3://1000genomes/i_dont_exist.yaml"

    # Act/Assert
    with pytest.raises(JobNotFoundError):
        FileJobRegistry(anon=True).get(path)


# ============================================================================
# Read tests
# ============================================================================


@pytest.mark.parametrize("ext", ["json", "yaml"])
def test_get_should_load_manifest_from_local_file(ext: str):
    # Arrange
    path = f"tests/mocks/manifests/mini.{ext}"

    # Act
    manifest = FileJobRegistry().get(path)

    # Assert
    actual = manifest
    expected = JobManifest(
        kind="Job",
        name="test_job",
        org="tiozin",
        region="latam",
        domain="quality",
        subdomain="pipeline",
        product="test_cases",
        model="some_case",
        layer="test",
        runner=RunnerManifest(kind="TestRunner"),
        inputs=[InputManifest(kind="TestInput", name="reader")],
        transforms=[TransformManifest(kind="TestTransform", name="transformer")],
        outputs=[OutputManifest(kind="TestOutput", name="writer")],
    )
    assert actual == expected


# ============================================================================
# Write tests
# ============================================================================


@pytest.mark.parametrize("ext", ["json", "yaml"])
def test_register_should_write_manifest_to_local_file(ext: str, tmp_path: Path):
    # Arrange
    output_path = tmp_path / f"job.{ext}"
    manifest = JobManifest(
        kind="Job",
        name="test_job",
        org="tiozin",
        region="latam",
        domain="quality",
        subdomain="pipeline",
        product="test_cases",
        model="some_case",
        layer="test",
        runner=RunnerManifest(kind="TestRunner"),
        inputs=[InputManifest(kind="TestInput", name="reader")],
        transforms=[TransformManifest(kind="TestTransform", name="transformer")],
        outputs=[OutputManifest(kind="TestOutput", name="writer")],
    )

    # Act
    FileJobRegistry().register(str(output_path), manifest)

    # Assert
    actual = output_path.read_text(encoding="utf8")
    expected = Path(f"tests/mocks/manifests/mini.{ext}").read_text(encoding="utf8")
    assert actual == expected
