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
)

SUBDOMAIN_FIELDS = (
    *DOMAIN_FIELDS,
    "subdomain",
)

PRODUCT_FIELDS = (
    "layer",
    "product",
    "model",
)

RESOURCE_FIELDS = (
    *SUBDOMAIN_FIELDS,
    *PRODUCT_FIELDS,
)
