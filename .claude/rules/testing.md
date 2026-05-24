# Testing Rules

## 1. SUT execution

Act executes the SUT exactly once.

- Act cannot transform the result.
- Assert may transform result, but must not call the SUT again.

```python
# Act
result = hello_world("World")

# ✔ Correct
# Assert
actual = result.upper()
expected = "HELLO, WORLD!"
assert actual == expected

# ❌ Incorrect
actual = hello_world("World").upper()
expected = "HELLO, WORLD!"
assert actual == expected
```

---

## 2. Actual and expected variables

Assert must always include both `actual` and `expected` variables.

```python
# ✔ Correct
# Assert
actual = result.upper()
expected = "HELLO, WORLD!"
assert actual == expected

# ❌ Incorrect
assert result.upper() == "HELLO, WORLD!"
assert "HELLO, WORLD!" == result.upper()
```

Exception: When the testing a boolean condition, assert it directly without `actual` and `expected`.

```python
# ✔ Preferred
assert target.exists()

# ❌ Verbose
actual = target.exists()
expected = True
assert actual == expected
```

---

## 3. Expected values

Prefer explicit `expected` values.
Avoid transforming `expected` when its value can be written directly.

```python
# ✔ Correct
actual = result
expected = "s3://bucket/lake/date=2026-01-16"
assert actual == expected

# ✔ Correct
actual = result
expected = Path("s3://bucket/lake/date=2026-01-16").as_uri()
assert actual == expected

# ❌ Incorrect
actual = result
expected = Path(path).as_uri()
assert actual == expected
```

`expected` must be portable. Never hardcode local paths, usernames, or home directories.

```python
# ✔ Correct
actual = result
expected = f"{tmp_path}/data/file.csv"
assert actual == expected

# ❌ Incorrect
actual = result
expected = "/tmp/data/file.csv"
assert actual == expected

# ❌ Incorrect
actual = result
expected = "/home/john/data/file.csv"
assert actual == expected
```

---

## 4. Comparison tests

Compute both sides in Act, compare in Assert.

```python
# ✔ Correct
# Act
left = foo(x)
right = bar(x)

# Assert
actual = (left, right)
expected = (10, 10)
assert actual == expected

# ❌ Incorrect
assert foo(x) == bar(x)
```

---

## 5. Testing expected failures

Use `pytest.raises` with `match=` when the message is part of the contract.

```python
# ✔ Correct
with pytest.raises(ValueError, match="Division by zero"):
    divide(10, 0)

# ❌ Incorrect
try:
    divide(10, 0)
    assert False
```

---

## 6. Test file ordering

1. Happy path — minimum input, common case, all observable defaults
2. Success variations — optional inputs, alternate valid states
3. Error variations — invalid or missing inputs, constraint violations, exception raising scenarios

---

## 7. Ordering

When order is part of the contract, assert `actual` directly. Never sort it.

```python
# ✔ Correct — order is the contract
actual = result.fetchall()
expected = [("amet", 1), ("dolor", 2), ("lorem", 3)]
assert actual == expected

# ❌ Incorrect — sorting hides ordering bugs
actual = sorted(result.fetchall())
assert actual == expected
```

When order is not part of the contract, sort `actual` and write `expected` in that order.

```python
actual = sorted(result.fetchall())
expected = [("amet", 1), ("dolor", 2), ("lorem", 3)]
assert actual == expected
```
