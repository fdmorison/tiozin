from typing import Any

import wrapt

from tiozin.api import Context, Executable, PlugIn
from tiozin.utils.helpers import generate_id, utcnow


class ExecutableProxy(wrapt.ObjectProxy):
    def setup(self, *args, **kwargs) -> None:
        plugin: PlugIn = self.__wrapped__
        plugin.setup(*args, **kwargs)

    def execute(self, context: Context, *args, **kwargs) -> Any:
        plugin: PlugIn | Executable = self.__wrapped__
        plugin.run_id = generate_id()

        try:
            self.setup(context, *args, **kwargs)
            plugin.info("▶️  Starting execution")
            plugin.executed_at = utcnow()
            result = plugin.execute(context, *args, **kwargs)
        except Exception:
            plugin.finished_at = utcnow()
            plugin.error(f"❌  Failed execution after {plugin.execution_time:.2f}s")
            raise
        else:
            plugin.finished_at = utcnow()
            plugin.info(f"✔️  Finished execution after {plugin.execution_time:.2f}s")
            return result
        finally:
            self.teardown(context, *args, **kwargs)

    def teardown(self, *args, **kwargs) -> None:
        plugin: PlugIn = self.__wrapped__
        try:
            plugin.teardown(*args, **kwargs)
        except Exception:
            plugin.warning("🚨 Teardown failed.", stack_info=True)

    def __repr__(self) -> str:
        return repr(self.__wrapped__)
