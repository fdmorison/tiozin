from io import StringIO
import json
from pathlib import Path

from ruamel.yaml import YAML

from .model import JobManifest
from .registry import JobRegistry


class FileJobRegistry(JobRegistry):
    """Default implementation of JobRegistry for file-based job manifests.

    This is the most basic way for Tio to access job manifests. It reads and writes
    manifest files from local filesystem, GCS, or S3 in YAML or JSON format.

    This class serves as the default implementation of the JobRegistry contract.
    The community can extend this contract with custom implementations, such as
    database-backed registries or GitHub-based manifest storage.

    Supported formats: .yaml, .yml, .json
    """

    def __init__(self) -> None:
        super().__init__()
        self.yaml = YAML(typ="safe")
        self.yaml.allow_duplicate_keys = False
        self.yaml.explicit_start = False
        self.yaml.sort_base_mapping_type_on_output = False
        self.yaml.default_flow_style = False

    def get(self, name: str) -> JobManifest:
        content = Path(name).read_text(encoding="utf-8")
        manifest = self.yaml.load(content)
        return JobManifest.model_validate(manifest)

    def register(self, name: str, value: JobManifest) -> None:
        path = Path(name)
        obj = value.model_dump(mode="json", exclude_none=True)

        if path.suffix in {".yaml", ".yml"}:
            content = self._dump_yaml(obj)
        elif path.suffix == ".json":
            content = self._dump_json(obj)
        else:
            raise ValueError(f"Unsupported manifest format: {path.suffix}")

        path.write_text(content, encoding="utf-8")

    def _dump_yaml(self, obj: dict) -> str:
        buffer = StringIO()
        self.yaml.dump(obj, buffer)
        return buffer.getvalue()

    def _dump_json(self, obj: dict) -> str:
        return json.dumps(obj, indent=2, ensure_ascii=False)
