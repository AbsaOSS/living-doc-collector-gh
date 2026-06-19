# Living Documentation Collector - for Developers

- [Project Setup](#project-setup)
- [Run Scripts Locally](#run-scripts-locally)
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

```shell
python3 --version
```

### Set Up Python Environment

```shell
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---
## SSL / TLS Certificate Verification

For environments with SSL/TLS interception (e.g., corporate proxies, Zscaler), you need to provide a custom CA bundle.

### Using Custom CA Bundle

Set the `REQUESTS_CA_BUNDLE` environment variable to the path of your CA certificate file:

```shell
export REQUESTS_CA_BUNDLE=/path/to/corporate-ca.pem
```

The Python `requests` library and GitHub API client will use this bundle to verify HTTPS connections.
If not set, the system default CA bundle will be used.

### Example with run_script.sh

The provided `run_script.sh` helper script handles CA bundle setup automatically:

```shell
# Set the path to your corporate CA certificate
export SSL_CERT_FILE=/path/to/corporate-ca.pem

# Run the script (it will combine certifi's CA bundle with your corporate CA)
./run_script.sh
```

The script exports `REQUESTS_CA_BUNDLE` with a combined CA bundle (system CAs + your corporate CA).

---

If you need to run the scripts locally, follow these steps:

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
Also make sure that the INPUT_GITHUB_TOKEN is configured in your environment variables.
```
# Essential environment variables for GitHub Action functionality
export INPUT_GITHUB_TOKEN=$(printenv GITHUB_TOKEN)
export INPUT_DOC_ISSUES=true
export INPUT_VERBOSE_LOGGING=true

# Environment variables for 'doc-issues' mode functionality
export INPUT_DOC_ISSUES_REPOSITORIES='[
  {
    "organization-name": "Organization Name",
    "repository-name": "example-project",
    "projects-title-filter": ["Project Title 1"]
  }
]'
export INPUT_DOC_ISSUES_PROJECT_STATE_MINING=true
```

### Running the script locally

For running the GitHub action locally, incorporate these commands into the shell script and save it.
```
python3 master.py
```
The whole script should look like this example:
```
#!/bin/sh

# Essential environment variables for GitHub Action functionality
export INPUT_GITHUB_TOKEN=$(printenv GITHUB_TOKEN)
export INPUT_DOC_ISSUES=true
export INPUT_VERBOSE_LOGGING=true

# Environment variables for 'doc-issues' mode functionality
export INPUT_DOC_ISSUES_REPOSITORIES='[
  {
    "organization-name": "Organization Name",
    "repository-name": "example-project",
    "projects-title-filter": ["Project Title 1"]
  }
]'
export INPUT_DOC_ISSUES_PROJECT_STATE_MINING=true

python3 master.py
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
pylint doc-issues/collector.py
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
black doc-issues/collector.py 
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
   mypy doc-issues/collector.py
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

The version appears in the JSON output under `metadata.generator.version`.

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
1. Validates the tag format
2. Verifies `pyproject.toml` matches the requested version
3. Creates the git tag
4. Generates release notes from commit history
5. Creates a draft release

### Step 5: Finalize and Publish

1. Review the generated draft release in GitHub
2. Edit the title and description if needed
3. Click **Publish release**
