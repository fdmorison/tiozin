from __future__ import annotations

from typing import Literal

import pydantic as pyd

from .logical_type_options import LogicalTypeOptions


class VectorOptions(LogicalTypeOptions):
    """
    Options of the vector logical type.

    Examples:

        ```python
        Property(
            name="embedding",
            logicalType="vector",
            logicalTypeOptions=VectorOptions(
                dimensions=1536,
                distanceMetric="cosine",
                embeddingModel="text-embedding-3-small",
            ),
        )
        ```
    """

    model_config = pyd.ConfigDict(extra="forbid")

    dimensions: int | None = pyd.Field(
        None,
        ge=1,
        description="Number of elements of the vector.",
    )
    elementType: Literal[
        "bfloat16",
        "binary",
        "float16",
        "float32",
        "float64",
        "int8",
        "uint8",
    ] = pyd.Field(
        "float32",
        description="Type of each element of the vector.",
    )
    distanceMetric: (
        Literal[
            "cosine",
            "dotProduct",
            "euclidean",
            "hamming",
            "manhattan",
        ]
        | None
    ) = pyd.Field(
        None,
        description="How the distance between two vectors is measured.",
    )
    embeddingModel: str | None = pyd.Field(
        None,
        description="Model that produced the vectors.",
    )
    embeddingModelVersion: str | None = pyd.Field(
        None,
        description="Version of the model that produced the vectors.",
    )
    normalized: bool = pyd.Field(
        False,
        description="Whether the vectors are normalized to unit length.",
    )
