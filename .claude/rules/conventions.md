# Conventions

## 1. Optional parameters default to `None`

Plugin constructor parameters must default to `None`, never to a concrete value.

```python
# ✔ Correct
def __init__(self, sampling_ratio: float = None, **options) -> None:

# ❌ Incorrect
def __init__(self, sampling_ratio: float = 1.0, **options) -> None:
```

Concrete defaults hide behavior from the user. Optional parameters are resolved
in the method body, falling back to library or engine defaults when `None`.

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

## 4. No magic numbers

Numeric literals must be assigned to a named constant at module level.

```python
# ✔ Correct
DEFAULT_SAMPLING_RATIO = 1.0

sampling_ratio = self.sampling_ratio or DEFAULT_SAMPLING_RATIO

# ❌ Incorrect
sampling_ratio = self.sampling_ratio or 1.0
```
