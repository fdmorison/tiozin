# Doc: Reference Page

## Overview

A reference page documents the API and behavior of a specific Tiozin component.

## Rules

-Always include a minimal working example with YAML and/or code.
- Additional sections may be created for:
  - properties that require substantial explanation;
  - accepted values that require documentation;
  - non-obvious component behavior;
  - constraints, side effects, validations, or integrations.
- Name each section after the documented subject.
- Verify every code example against source code or tests before publishing.
- Link to reference pages or conceptual pages instead of documenting them again.

## Template

```markdown
# <ComponentName>

[brief description]

[additional context if needed]

[example]

## Parameters

| Property | Required | Default | Description |
| -------- | -------- | ------- | ----------- |
| ...      | ...      | ...     | ...         |

## [Property]

[content + examples]

## [Behavior or Constraint]

[content + examples]

## Related

- How to ...
- Related component
- Related concept
```
