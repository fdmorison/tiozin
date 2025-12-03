export APP=$(shell basename "$$PWD")
export UV_INDEX_PRIVATE_PASSWORD=${ARTIFACTORY_PASSWORD}
export UV_INDEX_PRIVATE_USERNAME=${ARTIFACTORY_USERNAME}

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
	--build-arg ARTIFACTORY_USERNAME=${ARTIFACTORY_USERNAME} \
	--build-arg ARTIFACTORY_PASSWORD=${ARTIFACTORY_PASSWORD} \
	-t local/${APP}:latest .
	@docker image ls local/${APP}:latest

deploy:
	@echo
