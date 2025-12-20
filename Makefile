export APP=$(shell basename "$$PWD")

clean:
	@find . -type d -name "__pycache__" -exec rm -rf {} +

install:
	@uv sync --all-groups
	@uv pip install -e .
	@uv run pre-commit install
	@rm -rf *.egg-info

format:
	@uv run isort .
	@uv run autoflake .
	@uv run black .

check:
	@uv run isort . --check-only
	@uv run flake8 .
	@uv run black . --check

test:
	@uv run pytest -vvv .

build:
	@DOCKER_BUILDKIT=1 docker build \
	-t local/${APP}:latest .
	@docker image ls local/${APP}:latest

deploy:
	@echo
