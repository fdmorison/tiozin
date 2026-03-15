TIOZIN TEST RULES (AGENT VERSION)

1. NAMING (MANDATORY)
---------------------

Pattern:
    test_<subject>_should_<expected>(_when_<condition>)?

Must describe observable behavior.
Must not reference implementation details.

✔ Correct:
    test_add_should_return_sum_when_numbers_are_valid()

❌ Incorrect:
    test_add_internal_logic()


2. AAA STRUCTURE (MANDATORY)
----------------------------

All tests MUST contain:

    # Arrange
    # Act
    # Assert

✔ Correct:
    # Arrange
    x = 1

    # Act
    result = foo(x)

    # Assert
    actual = result
    expected = 2
    assert actual == expected

❌ Incorrect:
    result = foo(1)
    assert result == 2


3. DEFINE THE SUT (MANDATORY)
-----------------------------

Each test defines a Primary SUT (Unit Under Test).

The Act section MUST execute the SUT exactly once.
The Assert section must NOT re-execute the SUT.

✔ Correct:
    # Act
    result = hello_world("World")

    # Assert
    actual = result
    expected = "Hello, World!"
    assert actual == expected

❌ Incorrect:
    # Act
    result = hello_world("World")

    # Assert
    actual = hello_world("World")  # ❌ SUT re-executed
    assert actual == "Hello, World!"


4. PRIMARY VS DERIVED OPERATIONS
--------------------------------

Only the Primary SUT appears in Act.

The Assert MAY:
- Transform the result (str, tuple, field access)
- Extract attributes
- Format values

The Assert MUST NOT:
- Call the SUT again
- Execute new behavior chains

✔ Correct:
    # Act
    result = hello_world("World")

    # Assert
    actual = result.upper()
    expected = "HELLO, WORLD!"
    assert actual == expected

❌ Incorrect:
    # Assert
    actual = hello_world("World").upper()  # ❌ SUT inside Assert
    assert actual == "HELLO, WORLD!"


5. ASSERTION FORMAT (MANDATORY)
--------------------------------

Use:

    actual = <derived_from_result>
    expected = <explicit_value>
    assert actual == expected

Avoid:
    assert something
    assert isinstance(...)
    assert foo is not None

✔ Correct:
    actual = result
    expected = 5
    assert actual == expected

❌ Incorrect:
    assert result == 5

Exception — boolean existence checks:

When the assertion is a boolean predicate whose name already makes
the intent unambiguous (e.g. path.exists(), target.is_dir()), the
short form is preferred. Wrapping it in actual/expected = True adds
verbosity without clarity.

✔ Preferred:
    assert target.exists()
    assert target.is_dir()

❌ Avoid (overly verbose):
    actual = target.exists()
    expected = True
    assert actual == expected

Apply this exception only when the predicate name is self-explanatory.
For any result that carries a non-trivial value, the full pattern is
still required.


6. ASSERT COUNT
---------------

Prefer a single assert per test.

If multiple observable values define one contract,
group them into a tuple.

✔ Correct:
    actual = (a, b)
    expected = (1, 2)
    assert actual == expected

❌ Incorrect:
    assert a == 1
    assert b == 2


7. EQUIVALENCE TEST RULE
------------------------

If testing equivalence (A == B):

- Act must compute both A and B.
- Assert compares derived representations.
- Do not mix with value correctness.

✔ Correct:
    # Act
    left = foo(x)
    right = bar(x)

    # Assert
    actual = (left, right)
    expected = (10, 10)
    assert actual == expected

❌ Incorrect:
    assert foo(x) == bar(x)  # ❌ SUT re-executed in Assert


8. SINGLE BEHAVIOR RULE
-----------------------

Each test validates one behavioral contract only.

✔ Correct:
    test_add_should_return_sum()

❌ Incorrect:
    test_add_should_return_sum_and_raise_error()


9. EXCEPTION TESTS
------------------

Exception tests MAY omit actual/expected pattern.

Always use `match=` when the exception message is part of the contract.

✔ Correct:
    with pytest.raises(ValueError, match="Division by zero"):
        divide(10, 0)

❌ Incorrect:
    try:
        divide(10, 0)
        assert False


10. TEST CONSOLIDATION (MANDATORY FOR AGENT)
--------------------------------------------

After generating tests, the agent MUST:

- Remove duplicates
- Use @pytest.mark.parametrize when variation is input-only
- Avoid redundant coverage
- Prefer behavior over implementation detail


11. TEST FILE ORDERING
----------------------

Within a test file, tests must follow this reading order:

1. Happy path — construct the SUT with minimum required input and
   assert all observable defaults. Establishes the baseline contract.
2. Success variations — parametrized tests covering optional inputs,
   accepted values, or alternate valid states.
3. Error cases — rejection tests (invalid types, missing required
   fields, constraint violations).

This order allows a reader to understand what the SUT does before
understanding what it rejects.


12. QUALITY REQUIREMENTS
------------------------

Tests must be:
- Deterministic
- Isolated
- Behavior-focused
- Readable
- Minimal but complete

Avoid:
- Testing implementation details
- Asserting private state
- Testing multiple contracts in one test
- Over-mocking
- Asserting object identity (`result is sut`) when observable state is available

Object identity is an implementation detail. Prefer asserting `.kind`, `.path`,
`.value`, or other observable attributes that define the behavioral contract.

✔ Correct:
    actual = (result.path, result.kind)
    expected = (None, "FileSettingRegistry")
    assert actual == expected

❌ Incorrect:
    assert result is registry  # ❌ asserts identity, not behavior
