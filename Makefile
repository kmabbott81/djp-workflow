.PHONY: help install test test-fast test-full test-e2e test-all clean build lint format up down logs

help:  ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install dependencies
	pip install --upgrade pip
	pip install -e ".[dev,dashboards]"
	pre-commit install

test:  ## Run unit tests (fast subset, no slow tests)
	pytest -v -m "not slow" --ignore=tests_e2e

test-fast:  ## Run unit tests with parallel execution
	pytest -v -m "not slow" --ignore=tests_e2e -n auto || pytest -v -m "not slow" --ignore=tests_e2e

test-full:  ## Run entire test suite (no markers excluded)
	pytest -v

test-e2e:  ## Run e2e smoke tests
	pytest -m e2e -v

test-all:  ## Run all tests including slow ones (alias for test-full)
	pytest -v

clean:  ## Clean build artifacts and cache
	rm -rf build/ dist/ *.egg-info .pytest_cache .mypy_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build:  ## Build distribution packages
	python -m build

lint:  ## Run linters
	ruff check .
	mypy src/ --ignore-missing-imports

format:  ## Format code with black
	black .

# Docker targets (delegate to docker/Makefile)
up:  ## Start Docker services
	$(MAKE) -C docker up

down:  ## Stop Docker services
	$(MAKE) -C docker down

logs:  ## View Docker logs
	$(MAKE) -C docker logs

docker-build:  ## Build Docker images
	$(MAKE) -C docker build

docker-test:  ## Run tests in Docker
	$(MAKE) -C docker test

docker-clean:  ## Clean Docker resources
	$(MAKE) -C docker clean

# Performance budget targets
perf-baseline:  ## Generate performance baseline report
	pytest -q --durations=25 -m "not slow" | tee durations.txt
	python scripts/ci_perf_budget.py
	@echo "Review perf-report.md; if acceptable, copy JSON metrics into dashboards/ci/baseline.json and commit."
