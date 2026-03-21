# flake8: noqa
from tiozin.exceptions.base import (
    TiozinError,
    TiozinInternalError,
    TiozinUsageError,
)
from tiozin.exceptions.categories import (
    TiozinConflictError,
    TiozinForbiddenError,
    TiozinInputError,
    TiozinNotFoundError,
    TiozinNotImplementedError,
    TiozinPreconditionError,
    TiozinTimeoutError,
    TiozinUnavailableError,
)
from tiozin.exceptions.misc import (
    AccessViolationError,
    AlreadyFinishedError,
    AlreadyRunningError,
    ManifestError,
    NotInitializedError,
    PolicyViolationError,
    ProxyError,
    RequiredArgumentError,
)
from tiozin.api.metadata.secret.exceptions import (
    SecretError,
    SecretNotFoundError,
)
from tiozin.api.metadata.job.exceptions import (
    JobAlreadyExistsError,
    JobError,
    JobNotFoundError,
)
from tiozin.api.metadata.schema.exceptions import (
    SchemaError,
    SchemaNotFoundError,
    SchemaViolationError,
)
from tiozin.api.metadata.setting.exceptions import (
    SettingsError,
    SettingsNotFoundError,
)
from tiozin.compose.exceptions import (
    PluginConflictError,
    PluginError,
    PluginNotFoundError,
)

__all__ = [
    # Base
    "TiozinError",
    "TiozinUsageError",
    "TiozinInternalError",
    # Categories
    "TiozinNotFoundError",
    "TiozinConflictError",
    "TiozinTimeoutError",
    "TiozinForbiddenError",
    "TiozinInputError",
    "TiozinPreconditionError",
    "TiozinUnavailableError",
    "TiozinNotImplementedError",
    # Domain
    "ManifestError",
    "JobError",
    "JobNotFoundError",
    "JobAlreadyExistsError",
    "SchemaError",
    "SchemaViolationError",
    "SchemaNotFoundError",
    "SettingsError",
    "SettingsNotFoundError",
    "SecretError",
    "SecretNotFoundError",
    "PluginError",
    "PluginNotFoundError",
    "PluginConflictError",
    # Misc
    "AlreadyRunningError",
    "AlreadyFinishedError",
    "PolicyViolationError",
    "RequiredArgumentError",
    "ProxyError",
    "NotInitializedError",
    "AccessViolationError",
]
