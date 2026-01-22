APP := $(shell basename "$$PWD")

clean:
	@rm -rf *.egg-info build dist .ruff_cache .pytest_cache
	@find . -type d -name "__pycache__" -exec rm -rf {} +

hooks:
	@uv run pre-commit install

install:
	@uv sync
	@uv pip install -e .

install-dev:
	@uv sync --all-groups
	@uv pip install -e .
	@uv run pre-commit install
	@rm -rf *.egg-info

format:
	@uv run ruff format
	@uv run ruff check . --fix --show-fixes

check:
	@uv run ruff check .
	@uv run ruff format --check

test:
	@uv run pytest -vvv .

build:
	@uv build

deploy:
	@uv publish
