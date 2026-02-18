from typing import TYPE_CHECKING

import wrapt
from duckdb import DuckDBPyRelation

if TYPE_CHECKING:
    from ...typehints import DuckdbEtlStep, DuckdbPlan


class DuckdbStepProxy(wrapt.ObjectProxy):
    """
    DuckDB-specific proxy for ETL steps.

    This proxy layers DuckDB execution semantics on top of generic ETL steps, allowing them to
    participate in SQL-first pipelines without leaking DuckDB-specific concerns into step
    implementations.

    The proxy is responsible for mediating how step results are exposed to the DuckDB execution
    environment.
    """

    def __repr__(self) -> str:
        return repr(self.__wrapped__)

    def read(self) -> DuckDBPyRelation:
        """
        Executes the input step and exposes its result as a DuckDB view.

        The resulting relation is registered under the step name, making
        it available for downstream SQL-based steps.
        """
        step: DuckdbEtlStep = self.__wrapped__
        relation: DuckDBPyRelation = step.read()
        return self._register_view(relation)

    def transform(self, *data: DuckDBPyRelation) -> DuckDBPyRelation:
        """
        Executes the transform step and exposes its result as a DuckDB view.

        Registering the result allows subsequent steps to reference the
        transformation by name in SQL queries.
        """
        step: DuckdbEtlStep = self.__wrapped__
        relation: DuckDBPyRelation = step.transform(*data)
        return self._register_view(relation)

    def write(self, data: DuckDBPyRelation) -> "DuckdbPlan":
        """
        Executes the output step.

        Write steps are treated as terminal actions and are not exposed
        as DuckDB views. This avoids registering side-effecting operations
        (such as COPY statements) in the relational namespace.
        """
        step: DuckdbEtlStep = self.__wrapped__
        relation_or_command: DuckdbPlan = step.write(data)
        return self._register_view(relation_or_command)

    def _register_view(self, relation: DuckDBPyRelation) -> DuckDBPyRelation:
        """
        Registers a Relation as a DuckDB temporary view using the step slug.
        """
        if not isinstance(relation, DuckDBPyRelation):
            return relation

        step: DuckdbEtlStep = self.__wrapped__
        view_name = step.slug

        step.duckdb.register(view_name, relation)
        relation = relation.set_alias(view_name)
        return relation
