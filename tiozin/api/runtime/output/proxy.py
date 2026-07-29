from __future__ import annotations

from typing import TYPE_CHECKING

import wrapt

from tiozin.api import Context
from tiozin.compose import TiozinTemplateOverlay
from tiozin.exceptions import AccessViolationError
from tiozin.utils import utcnow
from tiozin.utils.decorators import log_delay

from ..dataset import Dataset

if TYPE_CHECKING:
    from tiozin import Output


class OutputProxy(wrapt.ObjectProxy):
    """
    Wraps an Output to add Tiozin's runtime behavior.

    The wrapped step focuses on ETL logic. The proxy handles everything else:
    context propagation, template rendering, lifecycle hooks, logging, and timing.
    """

    def setup(self) -> None:
        raise AccessViolationError(self)

    def teardown(self) -> None:
        raise AccessViolationError(self)

    def write(self, *data: Dataset) -> Dataset:
        step: Output = self.__wrapped__

        with Context.for_step(step) as context:
            return self._write(step, context, *data)

    @log_delay("Data output")
    def _write(self, step: Output, context: Context, *data: Dataset) -> Dataset:
        catalog = context.catalog
        lineage = context.registries.lineage

        with TiozinTemplateOverlay(step, context.template_vars):
            try:
                step.debug(f"Temporary workdir is {context.temp_workdir}")

                external = step.external_datasets()
                unwrapped_data = [Dataset.unwrap(a) for a in data]

                if step.schema_subject:
                    context.output_schema = context.registries.schema.get(
                        step.schema_subject,
                        step.schema_version,
                    )

                catalog.register(step, inputs=[*external.inputs, *data])
                lineage.run_started(inputs=catalog.get_inputs(step))

                context.setup_at = utcnow()
                step.setup()

                context.executed_at = utcnow()
                result = step.write(*unwrapped_data)

            except Exception:
                lineage.run_failed(outputs=catalog.get_outputs(step))
                raise

            else:
                output_dataset = (
                    Dataset.wrap(result)
                    .merge(external.outputs[0] if external.outputs else None)
                    .with_namespace(context.namespace)
                    .with_name(context.qualified_slug)
                    .with_schema(context.output_schema)
                )
                catalog.register(step, output=output_dataset)
                lineage.run_completed(outputs=catalog.get_outputs(step))
                return output_dataset.tiozin_data

            finally:
                context.teardown_at = utcnow()
                try:
                    step.teardown()
                except Exception as e:
                    step.error(f"🚨 {context.kind} teardown failed because {e}")
                context.finished_at = utcnow()

    def __repr__(self) -> str:
        return repr(self.__wrapped__)
