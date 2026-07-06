from google.api_core.exceptions import AlreadyExists, NotFound
from google.cloud import secretmanager

from tiozin import Secret, SecretRegistry
from tiozin.exceptions import RequiredArgumentError, SecretNotFoundError


class GoogleSecretManagerRegistry(SecretRegistry):
    """
    Secret registry backed by Google Cloud Secret Manager.

    Credentials are resolved through Application Default Credentials (ADC).

    Attributes:
        project_id: Google Cloud project ID.
        location: API endpoint override (e.g., ``http://localhost:6174`` for emulators).
    """

    def __init__(self, project_id: str = None, location: str = None, **options) -> None:
        super().__init__(location=location, **options)
        RequiredArgumentError.raise_if_missing(
            project_id=project_id,
        )
        self.project_id = project_id
        self._client = None

    def setup(self) -> None:
        if self.location:
            self._client = secretmanager.SecretManagerServiceClient(
                client_options={"api_endpoint": self.location}
            )
        else:
            self._client = secretmanager.SecretManagerServiceClient()

    def get(self, identifier: str) -> Secret:
        try:
            name = f"projects/{self.project_id}/secrets/{identifier}/versions/latest"
            response = self._client.access_secret_version(request={"name": name})
            return Secret(response.payload.data.decode("utf-8"))
        except NotFound:
            raise SecretNotFoundError(identifier)

    def register(self, identifier: str, value: Secret) -> None:
        parent = f"projects/{self.project_id}"

        try:
            self._client.create_secret(
                request={
                    "parent": parent,
                    "secret_id": identifier,
                    "secret": {"replication": {"automatic": {}}},
                }
            )
        except AlreadyExists:
            pass

        self._client.add_secret_version(
            request={
                "parent": f"{parent}/secrets/{identifier}",
                "payload": {"data": str(value).encode("utf-8")},
            }
        )
