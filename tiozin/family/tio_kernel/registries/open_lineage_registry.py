import json
import urllib.request

from tiozin.api import LineageRegistry, RunEvent


class OpenLineageRegistry(LineageRegistry):
    """
    OpenLineage-compatible lineage registry.

    Emits run events to any OpenLineage-compatible backend (e.g. Marquez, OpenMetadata)
    via the standard HTTP API at ``POST /api/v1/lineage``.

    Attributes:
        location: Base URL of the OpenLineage backend (e.g. ``http://localhost:5000``).
    """

    def __init__(self, location: str, **options) -> None:
        super().__init__(location=location, **options)

    def get(self, identifier: str = None, version: str = None) -> RunEvent:
        return None

    def register(self, identifier: str, value: RunEvent) -> None:
        """POST a run event to the OpenLineage API."""
        payload = self._serialize(value)
        url = f"{self.location.rstrip('/')}/api/v1/lineage"
        request = urllib.request.Request(
            url=url,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.timeout or 10) as response:
            if response.status >= 400:
                self.warning(f"OpenLineage backend returned {response.status} for run {identifier}")
            else:
                self.info(f"Emitted {value.state} event for run {identifier}")

    @staticmethod
    def _serialize(event: RunEvent) -> dict:
        return {
            "eventType": event.state,
            "eventTime": event.event_time.isoformat(),
            "run": {"runId": event.run_id},
            "job": {"namespace": event.namespace, "name": event.job},
            "inputs": [{"namespace": event.namespace, "name": ds} for ds in event.inputs],
            "outputs": [{"namespace": event.namespace, "name": ds} for ds in event.outputs],
            "producer": "tiozin",
        }
