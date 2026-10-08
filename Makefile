# Quality-gate command vocabulary for living-doc-collector-gh.
#
# These targets are the single source of truth for local and CI checks -
# .github/workflows/test.yml calls the same targets so the
# two never drift. Run `make qa` before opening a pull request.

PYTHON      ?= python3
PIP         ?= $(PYTHON) -m pip
# `doc-issues` PLANNED after v0.1.0, kept aside unchanged for the port: doc_issues/, the modules only it uses and
# their tests are left out of formatting and linting.
KEPT_ASIDE   = ':!doc_issues/**' ':!tests/doc_issues/**' ':!utils/github_project_queries.py' ':!tests/utils/test_github_project_queries.py'
PY_FILES     = $(shell git ls-files '*.py' $(KEPT_ASIDE))
PYLINT_MIN  ?= 9.5
COV_MIN     ?= 80

.DEFAULT_GOAL := help
.PHONY: help install qa lint format format-check types test coverage no-vendored-schemas retired-names \
        runtime-requirements

help: ## Show this help.
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

install: ## Install the development dependencies (requirements-dev.txt, which pulls in requirements.txt).
	$(PIP) install -r requirements-dev.txt

qa: format-check lint types no-vendored-schemas retired-names runtime-requirements coverage ## Run the full quality gate (format, lint, types, contract checks, tests + coverage).

format: ## Reformat all tracked Python files (ruff autofix + Black).
	ruff check --fix $(PY_FILES)
	black $(PY_FILES)

format-check: ## Check Black formatting without modifying files.
	black --check $(PY_FILES)

lint: ## Run ruff and Pylint (enforce the minimum score).
	ruff check $(PY_FILES)
	pylint --fail-under=$(PYLINT_MIN) $(PY_FILES)

types: ## Run the mypy static type checker.
	mypy .

# R12 check 1: contract schemas come from living-doc-utilities, never committed here.
# `doc-issues` PLANNED after v0.1.0, kept aside unchanged for the port: its schema file is allowed until then.
no-vendored-schemas: ## Fail on any committed contract schema file (R12 check 1).
	$(PYTHON) -m living_doc_utilities.contracts.check_no_vendored_schemas --allow doc_issues

# Names of the pre-0.5.0 artifacts, each pattern written so it never matches itself. `doc-issues` PLANNED after
# v0.1.0, kept aside unchanged for the port: doc_issues/ is not searched.
retired-names: ## Fail on any reference to a retired artifact name or key.
	@if git grep -nE 'doc-issues[.]json|items[[][]]|"item[s]"|original_[m]etadata|descoped_[a]t|future_[r]elease' \
		-- ':!tests/**' ':!CHANGELOG*' ':!doc_issues/**'; then exit 1; fi

# The action installs requirements.txt into its venv on every run, so it stays runtime-only; the dev tools
# live in requirements-dev.txt.
runtime-requirements: ## Fail when requirements.txt names a test, lint or type tool.
	$(PYTHON) tools/check_runtime_requirements.py

test: ## Run the unit test suite (integration tests excluded).
	pytest --ignore=tests/integration -v tests/

coverage: ## Run the unit test suite with the coverage gate.
	pytest --ignore=tests/integration --cov=. -v tests/ --cov-fail-under=$(COV_MIN)
