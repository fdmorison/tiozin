# Pull Request Rules

## Title

Describes the primary behavioral change. Used in the changelog.

- Sentence case, no trailing period
- Understandable without opening the PR

```
# ✔ Correct
feat(core): Add connection retry on transient failures
feat(core): Prevent duplicate rows when output mode is append
refactor(core): Registry lookup no longer requires explicit version

# ❌ Incorrect
feat(core): Updated the code
refactor(core): Code cleanup
```

---

## Branch

Short, hyphen-separated, prefixed by type.

```bash
# ✔ Correct
git checkout -b feat/runner-retry
git checkout -b fix/output-duplicate-rows

# ❌ Incorrect
git checkout -b my-branch
git checkout -b fix-the-bug-where-output-duplicates-rows-in-append-mode
```

---

## Commit

Lowercase, conventional commits format, short. Wording does not need to match the Title.

```bash
# ✔ Correct
git commit -m "feat(runner): add connection retry on transient failures"
git commit -m "refactor(schema): simplify registry lookup"

# ❌ Incorrect
git commit -m "Fixed the output bug"
```

---

## Description

- First sentence: what the system now does
- Optional follow-up (max 3 lines): what changed from previous behavior
- No implementation details, no opinions, no bullet points
- If no behavior change, state it explicitly

```
# ✔ Correct
The runner now retries automatically on transient connection failures.

Previously, any connection error caused the job to fail immediately. The retry logic is transparent to the job definition.

# ✔ Correct (no behavior change)
Internal restructuring of the schema registry lookup. No behavioral changes.

# ❌ Incorrect
Replaced the try/except block with a retry decorator and added exponential backoff using the tenacity library.
```

---

## What

Specific behavioral changes that extend the Description, not repeat it.

- One bullet per change
- Add scope, conditions, constraints
- No implementation details, no unaffected behavior

```
# ✔ Correct
- deduplication in append mode is based on primary key columns only
- deduplication occurs only within a single execution session

# ❌ Incorrect
- duplicate rows no longer occur when output mode is append
- truncate and overwrite modes are unaffected
```

---

## Notes

- Runtime behavior change: Yes or No
- Breaking change: Yes or No
- Scope limitations and clarifications that are not changes

---

## References

Real links only. If none: `None.`

---

## Checklist

Check only what applies.

```
- [x] Code follows project standards
- [x] Tests added/updated
- [ ] Documentation added
```
