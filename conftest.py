import re
import sys

import pytest

from tests import config, env
from tests.integration.family.tio_duckdb import env as duckdb_env

# Mock Settings
# Importing config.py will actually import tests/config.py
sys.modules[f"{config.artifact_name}.config"] = config

# Importing env.py will actually import tests/env.py
sys.modules[f"{config.artifact_name}.env"] = env

# Importing tio_duckdb/env.py will actually get tests/integration/family/tio_duckdb/env.py
sys.modules[f"{config.artifact_name}.family.tio_duckdb.env"] = duckdb_env


# Lint Tiozin Tests
def pytest_collection_modifyitems(session, config, items) -> None:
    violations = []
    pattern = re.compile(r"^test_[a-z0-9_]+_should_[a-z0-9_]+(_when_[a-z0-9_]+)?$")

    for item in items:
        testcase = item.originalname or item.name
        if not pattern.match(testcase):
            file, line, _ = item.location
            violations.append(f"{file}:{line + 1} {testcase}")

    if violations:
        message = (
            "\n[LINT ERROR] Tests do not match Tiozin's test naming convention.\n\n"
            "Expected:\n"
            "  - test_<subject>_should_<expected>\n"
            "  - test_<subject>_should_<expected>_when_<condition>\n\n"
            "Invalid test names found:\n"
            + "\n".join(f"  - {v}" for v in violations)
            + f"\n\nTotal violations: {len(violations)}"
        )
        pytest.exit(message, returncode=1)
