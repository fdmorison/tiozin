import sys

from tests import config

# Mock Tiozin Settings
# Importing config.py will actually immport tests/config.py
sys.modules[f"{config.package}.config"] = config
