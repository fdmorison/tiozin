from __future__ import annotations

from typing import TYPE_CHECKING

import wrapt

from tiozin.api import Context
from tiozin.compose import TiozinTemplateOverlay
from tiozin.exceptions import AccessViolationError
from tiozin.utils import utcnow

from .dataset import Dataset

if TYPE_CHECKING:
    from tiozin import EtlStep


class OutputProxy(wrapt.ObjectProxy):
    """
    Wraps an Input, Transform, or Output to add Tiozin's runtime behavior.

    The wrapped step focuses on ETL logic. The proxy handles everything else:
    context propagation, template rendering, lifecycle hooks, logging, and timing.
    """

    def __repr__(self) -> str:
        return repr(self.__wrapped__)

    def setup(self) -> None:
        raise AccessViolationError(self)

    def teardown(self) -> None:
        raise AccessViolationError(self)

    def write(self, *data: Dataset) -> Dataset:
        step: EtlStep = self.__wrapped__
        context = Context.for_step(step)
        catalog = context.catalog
        lineage = context.registries.lineage

        with context, TiozinTemplateOverlay(step, context.template_vars):
            try:
                step.info("▶️  Starting to write data")
                step.debug(f"Temporary workdir is {context.temp_workdir}")

                static = step.static_datasets()
                unwrapped_data = [Dataset.unwrap(a) for a in data]

                if step.schema_subject:
                    context.output_schema = context.registries.schema.try_get(
                        step.schema_subject,
                        step.schema_version,
                    )

                catalog.register(step, inputs=[*static.inputs, *data])
                lineage.start(inputs=catalog.get_inputs(step))

                context.setup_at = utcnow()
                step.setup()

                context.executed_at = utcnow()
                result = step.write(*unwrapped_data)

            except Exception:
                step.error(f"{context.kind} failed in {context.execution_delay:.2f}s")
                lineage.fail(outputs=catalog.get_outputs(step))
                raise

            else:
                step.info(f"{context.kind} finished in {context.execution_delay:.2f}s")
                output_dataset = (
                    Dataset.wrap(result)
                    .merge(static.outputs[0] if static.outputs else None)
                    .with_namespace(context.namespace)
                    .with_name(context.qualified_slug)
                    .with_schema(context.output_schema)
                )
                catalog.register(step, output=output_dataset)
                lineage.complete(outputs=catalog.get_outputs(step))
                return output_dataset.tiozin_data

            finally:
                context.teardown_at = utcnow()
                try:
                    step.teardown()
                except Exception as e:
                    step.error(f"🚨 {context.kind} teardown failed because {e}")
                context.finished_at = utcnow()
