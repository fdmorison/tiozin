from io import StringIO
import json
from pathlib import Path

from ruamel.yaml import YAML
from ruamel.yaml.constructor import DuplicateKeyError

from tiozin.exceptions import JobManifestException
from tiozin.model.model.job_manifest import JobManifest
from tiozin.model.registries.job_registry import JobRegistry


class FileJobRegistry(JobRegistry):
    """
    File-based job manifest storage.

    Reads and writes manifests from filesystem, GCS, or S3.
    Default JobRegistry implementation. Supports YAML and JSON formats.
    """

    def __init__(self) -> None:
        super().__init__()
        self.yaml = YAML(typ="safe")
        self.yaml.allow_duplicate_keys = False
        self.yaml.explicit_start = False
        self.yaml.sort_base_mapping_type_on_output = False
        self.yaml.default_flow_style = False

    def get(self, name: str) -> JobManifest:
        try:
            content = Path(name).read_text(encoding="utf-8")
            manifest = self.yaml.load(content)
            return JobManifest.model_validate(manifest)
        except DuplicateKeyError as e:
            raise JobManifestException.from_ruamel(e, name)

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
