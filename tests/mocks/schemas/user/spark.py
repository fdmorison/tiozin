from pyspark.sql.types import ArrayType, IntegerType, StringType, StructField, StructType

SPARK_SCHEMA = StructType(
    [
        StructField("name", StringType(), nullable=True),
        StructField(
            "profile",
            StructType(
                [
                    StructField("age", IntegerType(), nullable=True),
                ]
            ),
            nullable=True,
        ),
        StructField(
            "friends",
            ArrayType(
                StructType(
                    [
                        StructField("name", StringType(), nullable=True),
                    ]
                )
            ),
            nullable=True,
        ),
    ]
)
