# Tiozin

## What This Repo Is

Tiozin is a runtime framework for defining and executing modular data jobs. It supports plugin-based
development, plugin sharing, and declarative or programmatic job definitions.

Tiozin is not a job orchestrator, scheduler, DAG manager, or compute engine. It is designed to run
standalone or within orchestration systems such as Airflow.

## Commands

```bash
make install      # Install dependencies
make install-dev  # Install everything needed to develop locally
make format       # Format and fix code
make check        # Verify code style — fails if violations are found
make test         # Run full test suite
make build        # Build a deployment-ready package
make clean        # Remove unnecessary files such as builds and caches
```

## Directory Structure

```
tiozin/          # Main package
tiozin/api/      # Core abstractions
tiozin/family/   # Provider implementations
tiozin/compose/  # Code to build jobs
docs/            # User guides and concepts
examples/        # Sample jobs and schemas
tests/           # Unit and integration tests
```

# Additional Instructions

- Tech stack: `@.claude/knowledge/tech-stack.md`
- Concepts and terminology: `@.claude/knowledge/glossary.md`
- Delegate all test-related work to the `tester` agent.
- Delegate all documentation-related work to the `technical-writer` agent.
- Delegate all PullRequest-related work to the `pr-writer` agent.
