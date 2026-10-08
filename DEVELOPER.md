# Living Documentation Collector - for Developers

- [Project Setup](#project-setup)
- [Quality Gate (Makefile)](#quality-gate-makefile)
- [Run the Action Locally](#run-the-action-locally)
- [Run Pylint Check Locally](#run-pylint-check-locally)
- [Run Black Tool Locally](#run-black-tool-locally)
- [Run mypy Tool Locally](#run-mypy-tool-locally)
- [Run Unit Test](#run-unit-test)
- [Code Coverage](#code-coverage)
- [Versioning](#versioning)
- [Releasing](#releasing)

## Project Setup

If you need to build the action locally, follow these steps for project setup:

### Prepare the Environment

The supported Python floor is **3.10** (`requires-python = ">=3.10"` in `pyproject.toml`).
The action pins no interpreter: it builds its venv from whatever Python ≥ 3.10 is on the caller's `PATH`,
so runtime code must work on 3.10. The CI matrix covers 3.10 through 3.14.

```shell
python3 --version
```

### Set Up Python Environment

```shell
python3 -m venv .venv
source .venv/bin/activate
make install          # or: pip install -r requirements-dev.txt
```

### The Two Requirements Files

| File | What it holds | Who installs it |
|---|---|---|
| `requirements.txt` | Runtime only: what `main.py` and the active modules import (`living-doc-utilities`, `pydantic`, and `tomli` below Python 3.11) | `action.yml`, into the venv it creates under `$RUNNER_TEMP` on every run |
| `requirements-dev.txt` | `-r requirements.txt` plus the quality gate and test tools (Black, Pylint, mypy, ruff, pytest and its plugins) and the dependencies only the kept-aside `doc_issues/` imports (`PyGithub`, `requests`) | `make install`, `test.yml` and `integration_test.yml` |

The action installs `requirements.txt` on every run of every caller, so a test, lint or type tool named
there would be downloaded on every run. `make qa` fails when one is (`make runtime-requirements`, which
runs `tools/check_runtime_requirements.py`); add such a pin to `requirements-dev.txt` instead.

Dependabot covers both files from its single `pip` entry in `.github/dependabot.yml`: the `pip` ecosystem
scans the configured `directory` for every requirements file in it.

---
## Quality Gate (Makefile)

The `Makefile` is the single source of truth for quality checks — the
`test.yml` workflow calls the same targets, so local runs and
CI never drift. Run the full gate before opening a pull request:

```shell
make qa
```

Individual targets:

| Target | What it does |
|---|---|
| `make install` | Install the dev dependencies from `requirements-dev.txt` (which pulls in `requirements.txt`) |
| `make format` | Reformat tracked Python files (ruff autofix, then Black) |
| `make format-check` | Check Black formatting without writing changes |
| `make lint` | Run ruff, then Pylint, and enforce the minimum score (`PYLINT_MIN`, default `9.5`) |
| `make types` | Run the mypy type checker |
| `make test` | Run the unit test suite (integration tests excluded) |
| `make coverage` | Run the unit suite with the coverage gate (`COV_MIN`, default `80`) |
| `make no-vendored-schemas` | R12 check 1: fail on any committed contract schema file |
| `make retired-names` | Fail on any reference to a pre-0.5.0 artifact name or key |
| `make runtime-requirements` | Fail when `requirements.txt` names a test, lint or type tool |
| `make qa` | `format-check` + `lint` + `types` + `no-vendored-schemas` + `retired-names` + `runtime-requirements` + `coverage` |
| `make help` | List available targets |

`doc-issues` is PLANNED after v0.1.0: `doc_issues/`, the modules only it uses
(`utils/github_project_queries.py`) and their tests are kept aside unchanged for the port. Every gate
above excludes them; each exclusion is one commented line in `Makefile`, `pyproject.toml` or `.pylintrc`.

The sections below explain each tool in more detail; the raw commands they show are
what the corresponding `make` target runs under the hood.

---
## Run the Action Locally

The `doc-source` and `ui-tests` modes read local checkouts only: a local run makes no network request and needs
no token. If you need to run the scripts locally, follow these steps:

### Create the Shell Script

Create the shell file in the root directory. We will use `run_script.sh`.
```shell
touch run_script.sh
```
Add the shebang line at the top of the sh script file.
```
#!/bin/sh
```

### Set the Environment Variables

Set the configuration environment variables in the shell script following the structure below.
The collector supports mining in multiple modes, so you can use just the environment variables you need.
`INPUT_PROJECT_ID` is required; the artifacts land under `INPUT_OUTPUT_PATH` (default `./output/collector-gh`).
```
# Essential environment variables for GitHub Action functionality
export INPUT_PROJECT_ID=aul
export INPUT_OUTPUT_PATH=./output/collector-gh
export INPUT_VERBOSE_LOGGING=true
```

Each mode is enabled by its switch and given its repository list as JSON. The `doc-issues` mode is
PLANNED: `INPUT_DOC_ISSUES=true` fails the run at start.

```
# Environment variables for 'doc-source' mode functionality
export INPUT_DOC_SOURCE=true
export INPUT_DOC_SOURCE_REPOSITORIES='[
  {
    "organization-name": "absa-group",
    "repository-name": "aul-ui",
    "us-paths":   ["/abs/path/aul-ui/playwright/features/liv_doc_us"],
    "func-paths": ["/abs/path/aul-ui/playwright/features/liv_doc_func"],
    "pages-paths":["/abs/path/aul-ui/playwright/pages"]
  }
]'

# Environment variables for 'ui-tests' mode functionality
export INPUT_UI_TESTS=true
export INPUT_UI_TESTS_REPOSITORIES='[
  {
    "organization-name": "absa-group",
    "repository-name": "aul-ui",
    "paths": ["/abs/path/aul-ui/playwright/features"]
  }
]'
```

Parsing is `living-doc-utilities`' (`authoring`); the collectors only discover files and assemble the
contract result, which `write_artifact` validates before writing. Each mode's full-sample test
(`tests/<mode>/test_full_sample.py`) runs the collector over `tests/fixtures/full_sample/<mode>/` and
fails when a contract field outside its `NOT_PRODUCED` list stays empty. New modules must meet the
project-wide 80 % coverage gate (`make coverage`).

### Running the script locally

For running the GitHub action locally, incorporate these commands into the shell script and save it.
```
python3 main.py
```
The whole script should look like this example:
```
#!/bin/sh

# Essential environment variables for GitHub Action functionality
export INPUT_PROJECT_ID=aul
export INPUT_VERBOSE_LOGGING=true

# Environment variables for 'doc-source' mode functionality
export INPUT_DOC_SOURCE=true
export INPUT_DOC_SOURCE_REPOSITORIES='[
  {
    "organization-name": "absa-group",
    "repository-name": "aul-ui",
    "us-paths": ["/abs/path/aul-ui/playwright/features/liv_doc_us"]
  }
]'

python3 main.py
```

### Make the Script Executable

From the terminal, at the root of this project, make the script executable:
```shell
chmod +x run_script.sh
```

### Run the Script

```shell
./run_script.sh
```

---
## Run Pylint Check Locally

This project uses the [Pylint](https://pypi.org/project/pylint/) tool for static code analysis.
Pylint analyses your code without actually running it.
It checks for errors, enforces coding standards, looks for code smells, etc.
We do exclude the `tests/` file from the Pylint check.

Pylint displays a global evaluation score for the code, rated out of a maximum score of 10.0.
We are aiming to keep our code quality high above the score 9.5.

Follow these steps to run Pylint check locally:

- Perform the [setup of python venv](#set-up-python-environment).

### Run Pylint

Run Pylint on all files that are currently tracked by Git in the project.
```shell
pylint $(git ls-files '*.py')
```

To run Pylint on a specific file, follow the pattern `pylint <path_to_file>/<name_of_file>.py`.

Example:
```shell
pylint doc_source/collector.py
``` 

### Expected Output

This is an example of the expected console output after running the tool:
```
************* Module master
master.py:30:0: C0116: Missing function or method docstring (missing-function-docstring)

------------------------------------------------------------------
Your code has been rated at 9.41/10 (previous run: 8.82/10, +0.59)
```

---
## Run Black Tool Locally

This project uses the [Black](https://github.com/psf/black) tool for code formatting.
Black aims for consistency, generality, readability and reducing git diffs.
The coding style used can be viewed as a strict subset of PEP 8.

The root project file `pyproject.toml` defines the Black tool configuration.
In this project we are accept a line length of 120 characters.
We also exclude the `tests/` files from black formatting.

Follow these steps to format your code with Black locally:

- Perform the [setup of python venv](#set-up-python-environment).

### Run Black

Run Black on all files that are currently tracked by Git in the project.
```shell
black $(git ls-files '*.py')
```

To run Black on a specific file, follow the pattern `black <path_to_file>/<name_of_file>.py`.

Example:
```shell
black doc_source/collector.py
``` 

### Expected Output

This is an example of the expected console output after running the tool:
```
All done! ✨ 🍰 ✨
1 file reformatted.
```

---

## Run mypy Tool Locally

This project uses the [my[py]](https://mypy.readthedocs.io/en/stable/) 
tool which is a static type checker for Python.

> Type checkers help ensure that you’re using variables and functions in your code correctly.
> With mypy, add type hints (PEP 484) to your Python programs, 
> and mypy will warn you when you use those types incorrectly.

my[py] configuration is in `pyptoject.toml` file.

Follow these steps to format your code with my[py] locally:

### Run my[py]

Run my[py] on all files in the project.
```shell
  mypy .
```

To run my[py] check on a specific file, follow the pattern `mypy <path_to_file>/<name_of_file>.py --check-untyped-defs`.

Example:
```shell
   mypy doc_source/collector.py
``` 

### Expected Output

This is an example of the expected console output after running the tool:
```
Success: no issues found in 1 source file
```

---


## Run Unit Test

Unit tests are written using the Pytest framework. To run all the tests, use the following command:
```shell
pytest --ignore=tests/integration tests/
```

You can modify the directory to control the level of detail or granularity as per your needs.

To run a specific test, run the command following the pattern below:
```shell
pytest tests/utils/test_utils.py::test_make_issue_key
```

---
## Code Coverage

This project uses the [pytest-cov](https://pypi.org/project/pytest-cov/) plugin to generate test coverage reports.
The objective of the project is to achieve a minimum score of 80 %. We do exclude the `tests/` file from the coverage report.

To generate the coverage report, run the following command:
```shell
pytest --ignore=tests/integration --cov=. tests/ --cov-fail-under=80 --cov-report=html
```

See the coverage report on the path:

```shell
open htmlcov/index.html
```

---
## Versioning

The project version is defined in **`pyproject.toml`** under the `[project]` section and is the **single source of truth**.
It follows **Semantic Versioning (MAJOR.MINOR.PATCH)**:

- **MAJOR**: Breaking changes to schema or API contracts
- **MINOR**: New features or non-breaking enhancements
- **PATCH**: Bug fixes or internal improvements

### Version Source

The version is **always read from `pyproject.toml`** — both locally and in GitHub Actions.
This ensures consistency between:
- Local development
- Package distribution
- CI/CD workflows
- Generated JSON output

The version appears in the JSON output under `metadata.producer.version`.

### Local Development

To check the version locally:

```shell
python3 -c "from utils.constants import get_package_version; print(get_package_version())"
```

---

## Releasing

The release process is semi-automated using the `release_draft.yml` workflow and branch protection rules.

### Step 1: Create a Pull Request with Version Bump

Edit `pyproject.toml` and update the version:

```toml
[project]
name = "living-doc-collector-gh"
version = "X.Y.Z"  # Update this (e.g., "1.0.1", "1.1.0", "2.0.0")
```

Commit and push to a feature branch:

```shell
git checkout -b release/vX.Y.Z
git add pyproject.toml
git commit -m "chore: bump version to X.Y.Z"
git push origin release/vX.Y.Z
```

### Step 2: Merge via Branch Protection

- Create a Pull Request from your feature branch
- Request required approvals (configured in branch protection rules)
- Merge to `master` once approved

This ensures version changes are reviewed before release.

### Step 3: Trigger Release Draft Workflow

Manually trigger `release_draft.yml` via GitHub Actions UI or CLI:

```bash
gh workflow run release_draft.yml \
  -f tag-name=vX.Y.Z \
  -f from-tag-name=vX.Y.Z-1
```

Or in GitHub UI:
1. Go to **Actions** → **Draft Release**
2. Click **Run workflow**
3. Enter the tag name (e.g., `v1.0.1`)
4. Enter the previous tag (optional, for changelog diff)
5. Click **Run workflow**

### Step 4: Automated Processing

The `release_draft.yml` workflow automatically:
1. Validates the tag format and that the tag does not already exist
2. Collects the release notes from the merged pull requests
3. Creates the git tag
4. Creates a draft release

The workflow does **not** check `pyproject.toml` against the tag, so the Step 1 version bump is on you: a
forgotten bump ships a release whose artifacts all carry the previous `metadata.producer.version`.

#### Where the Release Notes Come From

Each merged pull request contributes the bullet lines written directly under its `## Release Notes`
heading, one line each. `release_draft.yml` passes
`release-notes-title: '## [Rr]elease [Nn]otes'` to `AbsaOSS/generate-release-notes`, because that action's
default pattern (`[Rr]elease [Nn]otes:`) expects a colon this repository's PR headings do not carry - left
at the default, the draft would take no line from any pull request. A PR labelled `no RN`, `duplicate`,
`invalid` or `wontfix` contributes nothing (`skip-release-notes-labels`).

### Step 5: Finalize and Publish

1. Review the generated draft release in GitHub
2. Edit the title and description if needed
3. Click **Publish release**
