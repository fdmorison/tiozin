from tiozin.utils.io import mkdirs


class IcebergCatalogFactory:
    """
    Factory that builds the properties to initialize an Iceberg catalog.

    The builder is chosen dynamically based on the catalog type: the private
    method named after the type builds the catalog properties, falling back
    to `fallback` for any other catalog type.
    """

    @staticmethod
    def build(type: str, location: str, **options) -> dict[str, str]:
        factory = getattr(IcebergCatalogFactory, f"_{type}", None)
        options = dict(options)

        if not factory:
            factory = IcebergCatalogFactory.fallback
            options["type"] = type

        return factory(location, **options)

    @staticmethod
    def _sqlite(location: str, **options) -> dict[str, str]:
        mkdirs(location)
        return {
            **options,
            "type": "sql",
            "uri": f"sqlite:///{location}/catalog.db",
            "warehouse": f"file://{location}",
        }

    @staticmethod
    def _rest(location: str, **options) -> dict[str, str]:
        return {
            **options,
            "type": "rest",
            "uri": location,
        }

    @staticmethod
    def fallback(location: str, type: str, **options) -> dict[str, str]:
        return {
            **options,
            "type": type,
        }
