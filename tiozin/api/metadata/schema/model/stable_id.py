from typing import Annotated

import pydantic as pyd

STABLE_ID_PATTERN = r"^[A-Za-z0-9_-]+$"

StableId = Annotated[str, pyd.Field(pattern=STABLE_ID_PATTERN)]
