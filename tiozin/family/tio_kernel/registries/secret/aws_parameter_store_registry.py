import boto3
import wrapt

from tiozin import Secret, SecretRegistry
from tiozin.exceptions import SecretNotFoundError


class AwsParameterStoreSecretRegistry(SecretRegistry):
    """
    Secret registry backed by AWS Systems Manager Parameter Store (SSM).

    Credentials are resolved through the standard AWS credential chain (environment variables,
    ~/.aws/credentials, IAM role, etc.).

    Attributes:
        location: Endpoint URL for the SSM client (e.g., ``http://localhost:4566`` for
            LocalStack). If not provided, the AWS endpoint is used.
        region_name: AWS region name (e.g., ``us-east-1``). If not provided,
            boto3 resolves the region from the environment or AWS config.
    """

    def __init__(self, location: str = None, region_name: str = None, **options) -> None:
        super().__init__(location=location, **options)
        self.region_name = region_name
        self.ssm = None

    @wrapt.synchronized
    def setup(self) -> None:
        self.ssm = boto3.client(
            "ssm",
            region_name=self.region_name,
            endpoint_url=self.location,
        )

    def get(self, identifier: str) -> Secret:
        try:
            response = self.ssm.get_parameter(
                Name=identifier,
                WithDecryption=True,
            )
            value = response["Parameter"]["Value"]
            return Secret(value)
        except self.ssm.exceptions.ParameterNotFound:
            raise SecretNotFoundError(identifier)

    def register(self, identifier: str, value: Secret) -> None:
        self.ssm.put_parameter(
            Name=identifier,
            Value=str(value),
            Type="SecureString",
            Overwrite=True,
        )
