# Schema Conventions

These rules apply to the schema module in `tiozin/api/metadata/schema/`.

## 1. The Schema model is the canonical schema

**`Schema` and `Property` are the canonical schema, modeled on the Open Data Contract Standard (ODCS) v3.2.0. Their dump must stay a valid ODCS schema object.**

The standard's JSON Schema is `tests/mocks/schemas/odcs-json-schema-v3.2.0.json`. It is the only contract the converters share.

## 2. Type mappings go format -> canonical -> format

**A reader maps its format to the canonical schema, and a writer maps the canonical schema to its format.**

A converter never imports another converter and never uses another format's type names or keys. It looks only at the canonical schema, so one format never breaks another.

```python
# ✔ Correct (spark/writer.py)
case Property(logicalType=LogicalType.STRING, binary=True):
    return SparkType(const.SPARK_BINARY_TYPE)

# ❌ Incorrect
from ..avro.constants import AVRO_FORMATS
```

## 3. `physicalType` is the type as the source writes it

**Readers set `physicalType` to the type exactly as the source schema writes it. It is for debugging and manual reading only, and writers never read it to choose a type.**

- Avro: a type name as is, and any other type as its JSON, unions and references to named types included, such as `'["null", "string"]'`.
- Spark: a simple type as is, such as `"decimal(10,2)"`, and a complex type as its JSON.

No writer preserves another format's `physicalType` on a property. The Avro writer never puts it under `odcs`, and the Spark writer never puts it in the field metadata. After crossing formats, the `physicalType` of a property reflects the last format read. A schema-level `physicalType`, such as "table", is still preserved.

The Avro writer reads the `physicalType` of a property only to keep the keys of each type definition in the order the source wrote them (`in_written_order`). The values always come from the generated type.

```python
# ❌ Incorrect
if property.physicalType == "bytes":
    return SparkType("binary")
```

## 4. Writers pick the type from the logical type, its options and the conventions

**A writer chooses the type only from `logicalType`, `logicalTypeOptions` and the Tiozin conventions (rule 6).**

Read an option only when it was set, through `option_value`, which checks `model_fields_set`. `IntegerOptions.format` defaults to "i32" as ODCS declares, but an unset option must fall back to the Tiozin default (rule 8).

```python
# ✔ Correct (avro/writer.py)
size_format = default(self.option_value(property, "format"), default_format)

# ❌ Incorrect
size_format = property.logicalTypeOptions.format
```

## 5. Prefer what ODCS already defines

**Use the `logicalTypeOptions` keys ODCS defines before adding anything.**

- `format` for the size of an integer. ODCS allows "i8" to "i128" and "u8" to "u128". The writers map "i8", "i16", "i32", "i64", "u8", "u16" and "u32", and raise `SchemaError` for the rest.
- `format` for the size of a number ("f32", "f64") and for a UUID string ("uuid").
- `minLength` and `maxLength` for the length of a string.
- `timezone` for whether a timestamp carries its timezone.

Never add keys to the per-type options. ODCS declares them with `additionalProperties: false`, and `StringOptions`, `IntegerOptions`, `NumberOptions`, `DateOptions`, `TimestampOptions`, `ObjectOptions`, `ArrayOptions` and `VectorOptions` use `extra="forbid"`. An extra key fails validation.

```python
# ✔ Correct
Property(name="id", logicalType="integer", logicalTypeOptions={"format": "i32"})

# ❌ Incorrect
Property(name="price", logicalType="number", logicalTypeOptions={"precision": 10})
```

## 6. The Tiozin conventions

**What ODCS has no place for is a Tiozin convention. These are the current ones:**

| Name        | Lives on             | Type                                  | Meaning                                                   |
|-------------|----------------------|---------------------------------------|-----------------------------------------------------------|
| `typeName`  | `Schema`, `Property` | `str`                                 | Name of the type, such as an Avro record, enum or fixed type. |
| `namespace` | `Schema`, `Property` | `str`                                 | Namespace of the type, such as com.acme.                  |
| `binary`    | `Property`           | `bool`                                | A string holds raw bytes.                                 |
| `precision` | `Property`           | `int`, at least 1                     | Number of digits of a decimal number.                     |
| `scale`     | `Property`           | `int`, at least 0                     | Number of digits after the point of a decimal number.     |
| `typeSize`  | `Property`           | `int`, at least 1                     | Size in bytes of a fixed-size binary type.                |
| `timeUnit`  | `Property`           | `"millis"`, `"micros"` or `"nanos"`   | Unit of a timestamp or a time.                            |

Each one is written as a custom property of the same name, without vendor, and left out when not set. Every converter reads and writes them with the same meaning.

## 7. Adding a convention

**A new convention is an explicit model field, never a custom property looked up by name.**

1. Declare the field with `exclude=True`.
2. Say in its `Field` description that it is a Tiozin convention, written as the custom property of the same name, and left out when not set.
3. Add its name to the `custom_fields` ClassVar, declared at the top of the class. `Property` extends `Element.custom_fields`.
4. Add it to the table in rule 6.

`Element` handles the rest. Its serializer writes every set field as a custom property without vendor. Its validator moves a custom property with only `property` and `value` back to the field, and a field given directly wins.

```python
typeSize: int | None = pyd.Field(
    None,
    ge=1,
    exclude=True,
    description=(
        "Size in bytes of a fixed-size binary type. A Tiozin convention, written as "
        "the `typeSize` custom property, and left out when not set."
    ),
)
```

Converters read conventions as attributes, so they get validated values.

```python
# ✔ Correct
case Property(logicalType=LogicalType.NUMBER, precision=int() as precision):

# ❌ Incorrect
precision = next(cp.value for cp in property.customProperties if cp.property == "precision")
```

## 8. Defaults when the canonical schema says nothing

**Every writer fills the same gap with the same default.**

- An integer is "i64" (`DEFAULT_INTEGER_FORMAT`).
- A number is "f64" (`DEFAULT_NUMBER_FORMAT`).
- A timestamp or time unit is "micros" (`DEFAULT_TIME_UNIT`).
- A timestamp carries its timezone unless its `timezone` option is false.

Import these constants from `tiozin/api/metadata/schema/converters/conventions.py`. Never redefine them in a format package.

## 9. Conventions win over format attributes

**When a Tiozin convention exists for an attribute, the convention is always used, without vendor, even when the attribute comes from a format. The vendor is only for attributes that have no convention. The table in rule 6 lists the conventions.**

An Avro type's `name` and `namespace` become the `typeName` and `namespace` conventions. An Avro decimal's `precision` and `scale`, and a fixed type's `size`, become `precision`, `scale` and `typeSize`. A Spark `decimal(10,2)` becomes `precision` and `scale`.

```python
# ✔ Correct
{"type": "fixed", "name": "Hash", "namespace": "com.acme", "size": 16}
# -> {"property": "typeName", "value": "Hash"}
# -> {"property": "namespace", "value": "com.acme"}
# -> {"property": "binary", "value": True}
# -> {"property": "typeSize", "value": 16}

# ❌ Incorrect
{"property": "namespace", "value": "com.acme", "vendor": "avro"}
```

## 10. Attributes without a convention keep their source name

**An attribute with no convention and no canonical meaning keeps the name it has in the source.**

- On a type, it becomes a custom property whose vendor is the format.
- On a field or a record, it becomes a custom property without vendor.

Avro aliases become synonyms whose source is "avro". `default` and `order` are generic, so they are custom properties without vendor.

```python
{"type": "string", "avro.java.string": "String"}
# -> {"property": "avro.java.string", "value": "String", "vendor": "avro"}
```

## 11. Optional Avro fields default to null

**In Avro, the writer gives `"default": null` to every field whose type is a union with null and that has no default.**

The reader therefore stores no `default` custom property for `"default": null` on such a field. Any other default is stored as the `default` custom property.

```python
{"name": "email", "type": ["null", "string"], "default": None}
# -> no `default` custom property

{"name": "score", "type": ["int", "null"], "default": 0}
# -> {"property": "default", "value": 0}
```

This default is intentional, so never remove it. Without a default, a new optional field is not backward compatible in [Confluent Schema Registry](https://docs.confluent.io/platform/current/schema-registry/fundamentals/schema-evolution.html), and Avro requires the default to conform to the first branch of the union, so "null" comes first with `"default": null`.

Adding `"default": null` to a field that already exists is safe. A Confluent Schema Registry in BACKWARD mode accepts `{"name": "email", "type": ["null", "string"]}` followed by the same field with `"default": null` as compatible, because a default is "only used when reading instances that lack the field" ([Avro specification](https://avro.apache.org/docs/1.12.0/specification/#schema-resolution)). The registry stores it as a new version, because [Confluent's schema normalization](https://docs.confluent.io/platform/current/schema-registry/fundamentals/serdes-develop/index.html) keeps `default`.

## 12. No data is lost in a round trip

**What a format cannot express goes to its extension point, and comes back intact.**

- Avro: the `odcs` key on the record and on each field.
- Spark: the field metadata, and the `metadata` key on the struct for schema attributes. `StructType.fromJson()` drops the struct key, so schema attributes survive only in the JSON form.

Additions on the way back, such as an implied `format` or `timeUnit`, are acceptable. Losses are not. The `physicalType` of a property is the exception: it is not carried across formats (rule 3).

Round-trip tests are mandatory. Every converter that both loads and dumps has one, and every attribute or convention added to it gets one in the same change, such as `test_load_should_round_trip_avro_schema` and `test_load_should_round_trip_spark_schema`.

## 13. Cross-format round trips are tested in `tests/integration`

**`tests/integration/api/metadata/schema/cross_format_round_trip_test.py` runs over the mocks in `tests/mocks/schemas`, named `avro_record_with_<content>.json` and `spark_struct_with_<content>.json`.**

Each direction has two tests:

- The Schema after the other format's hop equals the Schema read from the mock, ignoring `physicalType` (rule 3).
- The document written back equals the mock exactly. A Spark struct written back also has an empty `metadata` key, because the Spark writer always writes it.

Comparing the Schema after each hop makes a failure name the converter that lost data. Add a new mock to both parametrize lists of its direction.

## 14. Converters only work with serializable schemas

**`dump` returns, and `load` accepts, the schema as a serializable document: a dict in the format's JSON form, or a string holding that document. Never an object from the format's library.**

The schema module never imports a format's library, such as pyspark or openlineage-python. Turning the document into a library object is the caller's job, at the place that already depends on that library.

```python
# ✔ Correct (avro/converter.py)
def dump(self, schema: Schema, **options) -> dict[str, Any]:
    return AvroSchemaWriter().write(schema)

def load(self, schema: dict[str, Any] | str, **options) -> Schema:
    record = json.loads(schema) if isinstance(schema, str) else schema
    return AvroSchemaReader().read(record)

# ✔ Correct (caller)
StructType.fromJson(schema.to_spark())

# ❌ Incorrect
def dump(self, schema: Schema, **options) -> SchemaDatasetFacet:
    ...

# ❌ Incorrect
def load(self, schema: StructType, **options) -> Schema:
    ...
```
