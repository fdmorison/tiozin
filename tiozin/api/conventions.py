"""
Shared naming conventions used across Tiozin.
"""

SYSTEM_PREFIX = "_tio_"
INTERNAL_PREFIX = "__tio_"

CONTENT_COLUMN = "value"

DIRPATH_COLUMN = "dirpath"
DIRNAME_COLUMN = "dirname"

FILESIZE_COLUMN = "filesize"
FILEPATH_COLUMN = "filepath"
FILENAME_COLUMN = "filename"
FILESTEM_COLUMN = "filestem"
FILETYPE_COLUMN = "filetype"

DOMAIN_FIELDS = (
    "org",
    "region",
    "domain",
    "subdomain",
)

PRODUCT_FIELDS = (
    "layer",
    "product",
    "model",
)

RESOURCE_FIELDS = (
    *DOMAIN_FIELDS,
    *PRODUCT_FIELDS,
)
