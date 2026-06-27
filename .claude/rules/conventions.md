# Conventions

## 1. Optional parameters default to `None`

Optional parameters in any Python function or method must default to `None`, never to a concrete value.

Optional parameters are resolved in the method body, falling back to library or engine defaults when `None`.

```python
# ✔ Correct
from tiozin.utils import default

def __init__(self, value: float = None) -> None:
    value = default(value, 1.0)

def foo(timezone: str = None) -> Any:
    timezone = default(timezone, "UTC")

# ❌ Incorrect
def __init__(self, value: float = 1.0) -> None:
    ...

def foo(timezone: str = "UTC") -> Any:
    ...
```

## 2. `sf.col()` only when necessary

Use `sf.col()` only when a `Column` object is required. Functions that accept a column name as a
string must receive the string directly.

```python
# ✔ Correct
sf.from_json(column, schema)
data.select(column)

# ❌ Incorrect
sf.from_json(sf.col(column), schema)
data.select(sf.col(column))
```

## 3. Import alias for `pyspark.sql.functions`

Always import `pyspark.sql.functions` as `sf`.

```python
# ✔ Correct
from pyspark.sql import functions as sf

# ❌ Incorrect
from pyspark.sql import functions as F
from pyspark.sql import functions as f
```

## 4. `as_list` for single-or-list parameters

Use `as_list` from `tiozin.utils` when a parameter can be a single value or a list.

```python
# ✔ Correct
from tiozin.utils import as_list

self.columns = as_list(columns)

# ❌ Incorrect
self.columns = [columns] if isinstance(columns, str) else columns
```

## 5. `default` for optional parameters with fallback values

Use `default` from `tiozin.utils` to resolve an optional parameter to a concrete value in the method body.


Unlike `or`, `default` checks for `None` explicitly, so falsy values like `0`, `False`, or `""` are preserved correctly.

```python
# ✔ Correct
from tiozin.utils import default

self.sampling_ratio = default(sampling_ratio, 0.10)  # sampling_ratio=0 stays 0

# ❌ Incorrect — sampling_ratio=0 is incorrectly replaced by 0.10
self.sampling_ratio = sampling_ratio or 0.10
self.sampling_ratio = sampling_ratio if sampling_ratio is not None else 0.10
```

`or` is acceptable when an empty collection or string is semantically equivalent to "not provided":

```python
# ✔ Acceptable — empty list means "no columns selected", same as None
self.columns = columns or []
```

## 6. Imports at the top of the file

All imports must be at the top of the file. The only exception is a local import inside a function or method to break a circular dependency.

```python
# ✔ Correct
from tiozin.utils import default

def foo():
    ...

# ✔ Correct — local import to avoid circular dependency
def foo():
    from tiozin.some_module import Bar
    ...

# ❌ Incorrect
def foo():
    from tiozin.utils import default
    ...

# ❌ Incorrect
def foo():
    ...

from tiozin.utils import default
```

## 7. Constants at the top of the file

All module-level constants must be declared at the top of the file, after imports.

```python
# ✔ Correct
from datetime import datetime

FOO = 1.0
BAR = "12345"

def my_function():
    ...

# ❌ Incorrect
FOO = 1.0
BAR = "12345"

def my_function():
    ...

# ❌ Incorrect
def my_function():
    ...

FOO = 1.0
BAR = "12345"
```

## 8. No magic values

Literals must be assigned to a named constant at module level.

This rule applies only to production code (`tiozin/`).

Tests are exempt. Test code should optimize for readability rather than reuse. Inline literals make the scenario self-contained, whereas extracting them into constants hides the behavior being verified and makes tests harder to understand.

```python
# ✔ Correct
DEFAULT_SAMPLING_RATIO = 1.0
sampling_ratio = self.sampling_ratio or DEFAULT_SAMPLING_RATIO

# ❌ Incorrect
sampling_ratio = self.sampling_ratio or 1.0

# ✔ Correct
STR_2024_01_15T10_30_00Z = "2024-01-15T10:30:00Z"
input = spark.createDataFrame(
    [{"created_at": STR_2024_01_15T10_30_00Z}],
    schema="created_at STRING",
)

# ❌ Incorrect
input = spark.createDataFrame(
    [{"created_at": "2024-01-15T10:30:00Z"}],
    schema="created_at STRING",
)

# ✔ Correct
OBJ_2024_01_15T10_30_00Z = datetime.fromisoformat("2024-01-15T10:30:00Z")
input = spark.createDataFrame(
    [{"created_at": OBJ_2024_01_15T10_30_00Z}],
    schema="created_at STRING",
)

# ❌ Incorrect
input = spark.createDataFrame(
    [{"created_at": datetime.fromisoformat("2024-01-15T10:30:00Z")}],
    schema="created_at STRING",
)
```
