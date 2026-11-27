from __future__ import annotations

from typing import Any, ClassVar, Self

import pydantic as pyd

from .authoritative_definition import AuthoritativeDefinition
from .custom_property import CustomProperty
from .enums import LogicalType, TiozinCustomProperty
from .model import Model
from .quality import Quality
from .relationship import Relationship
from .stable_id import StableId
from .synonym import Synonym


class Element(Model):
    """
    What a schema and a property have in common.

    Every attribute here works the same on a `Schema` and on a `Property`.

    Examples:

        ```python
        schema = Schema(
            name="users",
            description="People who signed up.",
            tags=["crm"],
        )
        property = Property(
            name="email",
            logicalType="string",
            businessName="Email address",
            synonyms=[Synonym(synonym="mail")],
        )
        ```
    """

    custom_fields: ClassVar[tuple[str, ...]] = (
        TiozinCustomProperty.TYPE_NAME,
        TiozinCustomProperty.NAMESPACE,
    )

    id: StableId | None = pyd.Field(
        None,
        description="Stable identifier, unique among the schemas or properties around it.",
    )
    name: str | None = pyd.Field(
        None,
        description="Name of the schema or property.",
    )
    logicalType: LogicalType | None = pyd.Field(
        None,
        description=(
            "Type of the schema or property in the Open Data Contract Standard, "
            "such as string, integer or object."
        ),
    )
    physicalType: str | None = pyd.Field(
        None,
        description="Type of the schema or property in storage, such as table, view or VARCHAR(2).",
    )
    physicalName: str | None = pyd.Field(
        None,
        description="Name of the schema or property in storage.",
    )
    description: str | None = pyd.Field(
        None,
        description="What the schema or property holds.",
    )
    businessName: str | None = pyd.Field(
        None,
        description="Name of the schema or property for business people.",
    )
    deprecated: bool = pyd.Field(
        False,
        description="Whether the schema or property should no longer be used.",
    )
    synonyms: list[Synonym] | None = pyd.Field(
        None,
        description="Other names of the schema or property.",
    )
    authoritativeDefinitions: list[AuthoritativeDefinition] | None = pyd.Field(
        None,
        description="Links to sources with more details.",
    )
    tags: list[str] | None = pyd.Field(
        None,
        description="Tags of the schema or property.",
    )
    customProperties: list[CustomProperty] | None = pyd.Field(
        None,
        description="Properties that the standard does not define.",
    )
    relationships: list[Relationship] | None = pyd.Field(
        None,
        description="Links from the schema or property to other properties, such as foreign keys.",
    )
    quality: list[Quality] | None = pyd.Field(
        None,
        description="Data quality rules of the schema or property.",
    )
    typeName: str | None = pyd.Field(
        None,
        exclude=True,
        description=(
            "Name of the type, such as an Avro record, enum or fixed type. A Tiozin "
            "convention, not part of the standard: it is written as the `typeName` custom "
            "property, and left out when not set."
        ),
    )
    namespace: str | None = pyd.Field(
        None,
        exclude=True,
        description=(
            "Namespace of the type, such as com.acme. A Tiozin convention, not part of "
            "the standard: it is written as the `namespace` custom property, and left out "
            "when not set."
        ),
    )

    def clone(self) -> Self:
        """
        An independent copy of this schema or property.

        Examples:

            ```python
            draft = schema.clone().string("nickname")
            "nickname" in schema
            # False
            ```
        """
        return self.model_copy(deep=True)

    def rename(self, name: str) -> Self:
        """
        Renames this schema or property.

        Examples:

            ```python
            schema.rename("customers").name
            # 'customers'

            schema["email"].rename("mail")
            ```
        """
        self.name = name
        return self

    @pyd.model_validator(mode="before")
    @classmethod
    def takes_custom_fields_from_custom_properties(cls, data: Any) -> Any:
        """
        Moves the custom properties named after a Tiozin convention, such
        as `typeName` or `precision`, to the attribute of the same name. Only a
        custom property with nothing but a name and a value is moved. An
        attribute given directly wins over the custom property.
        """
        if not isinstance(data, dict) or not data.get("customProperties"):
            return data

        custom_fields = {}
        custom_properties = []

        for custom_property in data["customProperties"]:
            declared = (
                custom_property.model_dump(exclude_unset=True)
                if isinstance(custom_property, CustomProperty)
                else custom_property
            )
            is_custom_field = (
                isinstance(declared, dict)
                and declared.keys() == {"property", "value"}
                and declared["property"] in cls.custom_fields
            )

            if is_custom_field:
                custom_fields[declared["property"]] = declared["value"]
            else:
                custom_properties.append(custom_property)

        data = {key: value for key, value in data.items() if key != "customProperties"}

        if custom_properties:
            data["customProperties"] = custom_properties

        return {**custom_fields, **data}

    @pyd.model_serializer(mode="wrap")
    def writes_custom_fields_as_custom_properties(
        self,
        handler: pyd.SerializerFunctionWrapHandler,
        info: pyd.SerializationInfo,
    ) -> Any:
        """
        Writes the Tiozin conventions that are set, such as `typeName` or
        `precision`, as custom properties, so the result stays a valid Open
        Data Contract Standard document.

        Pydantic may run this twice on the same element, such as on the
        properties of a schema, so a custom property already written is not
        written again.
        """
        data = handler(self)

        if not isinstance(data, dict) or "customProperties" in (info.exclude or set()):
            return data

        custom_properties = data.get("customProperties") or []
        custom_fields = [
            {"property": name, "value": getattr(self, name)}
            for name in self.custom_fields
            if getattr(self, name) is not None
        ]
        new_fields = [field for field in custom_fields if field not in custom_properties]

        if not new_fields:
            return data

        return {**data, "customProperties": [*new_fields, *custom_properties]}
