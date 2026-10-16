# Living Documentation Collector for GitHub: developer guide

## Purpose

Anyone who changes this repository reads this page. It covers setup, the quality gates, the two local runs,
versioning, the release, and the rules for writing documentation.

Read before: [README](README.md)

## Contents

- [Setup](#setup)
- [Gates](#gates)
- [Debug run](#debug-run)
- [Local Integration Run](#local-integration-run)
- [Versioning](#versioning)
- [Release](#release)
- [Writing documentation](#writing-documentation)

## Setup

1. Use Python 3.10 or later: `python3 --version`.
2. Create and activate a virtual environment: `python3 -m venv .venv`, then `source .venv/bin/activate`.
3. Run `make install`: `pip install -r requirements-dev.txt`, which pulls in `requirements.txt` → `Makefile::install`

- The supported floor is 3.10, and runtime code must work on it → `pyproject.toml::requires-python`
  - Why: the action pins no interpreter; it builds its venv from whatever Python ≥ 3.10 is on the caller's `PATH`.
- CI tests Python 3.10 through 3.14 → `.github/workflows/test.yml::3.14`

| File | What it holds | Who installs it |
|---|---|---|
| `requirements.txt` | Runtime only: what `main.py` and the active modules import (`living-doc-utilities`, `pydantic`, and `tomli` below Python 3.11) | `action.yml`, into the venv it creates under `$RUNNER_TEMP` on every run |
| `requirements-dev.txt` | `-r requirements.txt`, the gate and test tools, `PyYAML` for the documentation checks, and `PyGithub` and `requests` for the kept-aside `doc_issues/` | `make install`, `test.yml` and `integration_test.yml` |

- A test, lint or type tool in `requirements.txt` would download on every run of every caller; `make qa` fails on one → `tools/check_runtime_requirements.py::DENIED_NAMES`
- Dependabot covers both files from its single `pip` entry: it scans the configured `directory` for every requirements file → `.github/dependabot.yml::pip`

## Gates

`make qa` runs `format-check`, `lint`, `types`, `no-vendored-schemas`, `retired-names`, `runtime-requirements` and
`coverage`, and stops at the first failure → `Makefile::qa`. Run it before opening a pull request.

<!-- over limit: one row per target; the columns are what each gate needs and cannot be shortened -->
| Target | Runs | Gate | One file |
|---|---|---|---|
| `make format` | ruff autofix, then Black, rewriting files | line length 120 | `black doc_source/collector.py` |
| `make format-check` | Black in check mode | clean | `black --check doc_source/collector.py` |
| `make lint` | ruff, then Pylint; Pylint skips `tests/` | Pylint ≥ 9.5 / 10 (`PYLINT_MIN`) | `pylint doc_source/collector.py` |
| `make types` | mypy over the project; `tests/` is excluded | clean | `mypy doc_source/collector.py --check-untyped-defs` |
| `make test` | pytest over `tests/`, `tests/integration` excluded | pass | `pytest tests/utils/test_utils.py::test_sanitize_filename` |
| `make coverage` | pytest with coverage; `tests/` is not measured | ≥ 80 % (`COV_MIN`) | `pytest --ignore=tests/integration --cov=. tests/ --cov-fail-under=80 --cov-report=html`, then open `htmlcov/index.html` |
| `make no-vendored-schemas` | `living-doc-utilities`' vendored-schema check (R12 check 1) | no committed contract schema file | not scoped |
| `make retired-names` | a `git grep` for the names and keys of the pre-0.5.0 artifacts | no hit | not scoped |
| `make runtime-requirements` | `tools/check_runtime_requirements.py` | no test, lint or type tool in `requirements.txt` | not scoped |

- `test.yml` calls the same targets, so local runs and CI never drift → `.github/workflows/test.yml::coverage`
- Black, ruff and Pylint take their files from `git ls-files`, so a new file is checked once it is tracked → `Makefile::PY_FILES`
- Black, ruff and mypy read their settings from `pyproject.toml`; Pylint reads `.pylintrc` → `.pylintrc::ignore-paths`
- `make install` installs the development dependencies; `make help` lists every target → `Makefile::help`
- `doc-issues` is PLANNED: `doc_issues/`, the modules only it uses and their tests are kept aside unchanged for the port. Every gate excludes them → `Makefile::KEPT_ASIDE`
  - Each exclusion is one commented line in `Makefile`, `pyproject.toml` or `.pylintrc`.
- Each mode's full-sample test runs the collector over `tests/fixtures/full_sample/<mode>/`. It fails when a contract field outside its `NOT_PRODUCED` list stays empty → `tests/doc_source/test_full_sample.py::test_every_contract_field_outside_not_produced_is_occupied`
- New modules must meet the project-wide 80 % coverage gate → `Makefile::COV_MIN`
- The documentation checks are pytest tests, so `make test` and `make coverage` run them → [Checks](#checks)

## Debug run

The hand-written run of `main.py` in the development venv, for a debugger or one changed input. To run over a
real checkout in a repeatable way, with a validated and reported result, use the [Local Integration Run](#local-integration-run).

```shell
export INPUT_PROJECT_ID=aul                       # required
export INPUT_OUTPUT_PATH=./output/collector-gh    # the default
export INPUT_VERBOSE_LOGGING=true
export GITHUB_OUTPUT=/dev/null                    # main.py writes the output-path line here
export INPUT_DOC_SOURCE=true
export INPUT_DOC_SOURCE_REPOSITORIES='[{"organization-name": "absa-group", "repository-name": "aul-ui",
  "us-paths": ["/abs/path/aul-ui/playwright/features/liv_doc_us"],
  "func-paths": ["/abs/path/aul-ui/playwright/features/liv_doc_func"],
  "pages-paths": ["/abs/path/aul-ui/playwright/pages"]}]'
export INPUT_UI_TESTS=true
export INPUT_UI_TESTS_REPOSITORIES='[{"organization-name": "absa-group", "repository-name": "aul-ui",
  "paths": ["/abs/path/aul-ui/playwright/features"]}]'
python3 main.py
```

- Each input is an `INPUT_<NAME>` variable, upper case with `_` for `-`, as `action.yml` passes it → `action.yml::INPUT_DOC_SOURCE_REPOSITORIES`
- `GITHUB_OUTPUT` must be set, or the run fails on its last step with a `KeyError`; only a runner provides it → `main.py::run`
- The modes read local checkouts only: a debug run makes no network request and needs no token → `action_inputs.py::ActionInputs`
- `INPUT_DOC_ISSUES=true` fails the run at start → [Documentation Issues](doc_issues/README.md)
- Parsing is `living-doc-utilities`' `authoring`; the collectors only discover files and assemble the contract result, which `write_artifact` validates before writing → `utils/artifact.py::store_artifact`

## Local Integration Run

`local-integration.sh` runs the real collector over a real checkout, on the machine that has that checkout, a
private repository included, which no workflow of this repository can reach. It runs both modes in a venv of its
own, re-reads every artifact with `read_artifact`, and prints what ran and what came out. No workflow runs it; like
any local run, it is a development and operator-check affordance, not a second supported deployment target.

### What You Prepare

The script checks the Python version and nothing else of the environment → `local-integration.sh::--check`. The rest is yours:

- **Python ≥ 3.10**, with its `venv` module and whatever system libraries it needs. The script uses `PYTHON` from `.env.local` when set, else `python3`, else `python` from `PATH`, the order `action.yml` uses.
  - On Git Bash for Windows, `python3` may be the Microsoft Store alias, which does not run: set `PYTHON=python`.
- **`git`** on `PATH`, and a checkout of the target repository.
- **Network and pip configuration** that lets `pip install -r requirements.txt` succeed: `pip.conf`, `PIP_INDEX_URL`, `PIP_FIND_LINKS`, a proxy. The script leaves them as they are.
- **A POSIX shell**: bash 3.2 or later; Linux, macOS, or Git Bash on Windows.

No token: both modes read the local checkout and call no API, so the script reads no credential.

- It unsets `GITHUB_TOKEN`, `GH_TOKEN` and every inherited `INPUT_*` before it starts anything → `local-integration.sh::GH_TOKEN`
- `.env.local` is read as data, never sourced. A token left in it is ignored; the script reports its line by number, never its text.

### Configure It

```shell
cp .env.local.example .env.local      # .env.local is git-ignored
```

As committed, the example targets the public [`AbsaOSS/living-doc-testbed`](https://github.com/AbsaOSS/living-doc-testbed)
project `projects/core/`, checked out beside this repository; with that checkout in place it runs unchanged.

| Key | Required | What it sets |
|---|---|---|
| `PROJECT_ID` | yes | `project-id`, written to every artifact's `metadata.source.project_id` |
| `TARGET_CHECKOUT` | yes | the target's local checkout; relative to this repository's root, `~/` for home |
| `ORGANIZATION_NAME`, `REPOSITORY_NAME` | yes | the target's GitHub organization and name, for `source_ref.url` and `metadata.source` |
| `DOC_SOURCE_US_PATHS` | yes | `doc-source` `us-paths` |
| `DOC_SOURCE_FUNC_PATHS`, `DOC_SOURCE_PAGES_PATHS` | no | `doc-source` `func-paths` and `pages-paths` |
| `UI_TESTS_PATHS` | yes | `ui-tests` `paths` |
| `GITHUB_SERVER_URL` | no | `github-server-url`, for GitHub Enterprise Server permalinks; empty means `https://github.com` |
| `OUT_DIR` | no | the output root, default `./output` (git-ignored); relative to this repository's root |
| `PYTHON` | no | the interpreter the venv is built from |

- Each mode path is relative to `TARGET_CHECKOUT`; several are separated by commas.
- One `KEY=value` per line; a line starting with `#` is a comment, and values are taken literally.

### Run It

```shell
./local-integration.sh --check   # Python, git, the configuration and every path; creates no venv, runs nothing
./local-integration.sh           # the run
```

A run, in order:

1. **Checks** what `--check` checks. A missing variable or path, or a Python below 3.10, stops it with one line that names it.
2. **Builds its venv**, `.venv-local-integration/` (git-ignored), separate from the development `.venv`. It installs only `requirements.txt` (`pip install -r`): a runtime requirement missing from that file fails here, as on a runner.
   - It follows `action.yml`: `PIP_TARGET`, `PIP_PREFIX`, `PIP_USER` and `PYTHONPATH` unset, an import check after the install, and `main.py` run with `-E`.
   - The venv is reused only when the same interpreter built it from the same `requirements.txt`.
3. **Prints what runs**: the collector commit, the installed `living-doc-utilities` version, the Python version and the target commit. A commit is marked when tracked files differ from it.
4. **Runs `doc-source`, then `ui-tests`**, each as its own `main.py` run into `$OUT_DIR/collector-gh/<mode>/`, having cleared both mode directories first. Each command is echoed before it runs.
5. **Validates and reports** each artifact → `tools/local_integration.py::report`
   - It re-reads the artifact with `read_artifact`, then prints its contract, run time, size and `metadata.stats` counts (cardinality and field occupancy).
   - It prints the warnings by code: each code's count and its first ten occurrences.

- It exits non-zero when a check, the install, the collector or a validation fails → `tools/local_integration.py::main`
- For an issue or a report, keep the whole output: `set -o pipefail; ./local-integration.sh 2>&1 | tee local-integration.log`.

## Versioning

- `version` under `[project]` in `pyproject.toml` is the single source of truth, read the same way locally and in GitHub Actions → `utils/constants.py::get_package_version`
- It appears in every artifact as `metadata.producer.version` → `utils/artifact.py::build_metadata`
- It follows Semantic Versioning, MAJOR.MINOR.PATCH:
  - MAJOR: a breaking change to a schema or API contract.
  - MINOR: a new feature or a non-breaking enhancement.
  - PATCH: a bug fix or an internal improvement.
- To check it locally: `python3 -c "from utils.constants import get_package_version; print(get_package_version())"`.

## Release

The release is semi-automated: the `release_draft.yml` workflow and the branch protection rules.

1. Set `version` in `pyproject.toml` on a branch such as `release/vX.Y.Z`, commit `chore: bump version to X.Y.Z`, and push it.
2. Open a pull request, get the approvals branch protection requires, and merge it to `master`.
3. Actions → **Draft Release** → **Run workflow**, with the tag name (e.g. `v1.0.1`) and, optionally, the previous tag for the changelog diff → `.github/workflows/release_draft.yml::from-tag-name`
   - From the CLI: `gh workflow run release_draft.yml -f tag-name=vX.Y.Z -f from-tag-name=vX.Y.Z-1`.
4. The workflow validates the tag format and that the tag is new. It collects the release notes from the merged pull requests, then creates the git tag and a draft release.
5. Review the draft release, edit its title and description if needed, and click **Publish release**.

- The workflow does not check `pyproject.toml` against the tag, so the step-1 bump is on you → `.github/workflows/release_draft.yml::tag-name`
  - Why: a forgotten bump ships a release whose artifacts all carry the previous `metadata.producer.version`.
- Each merged pull request contributes the bullet lines directly under its `## Release Notes` heading, one line each → `.github/workflows/release_draft.yml::release-notes-title`
  - Why: `AbsaOSS/generate-release-notes` defaults to `[Rr]elease [Nn]otes:`, with a colon these headings do not carry.
- A pull request labelled `no RN`, `duplicate`, `invalid` or `wontfix` contributes nothing → `.github/workflows/release_draft.yml::skip-release-notes-labels`

## Writing documentation

> **Provisional.** These rules are a pilot; the owner tunes them after this first rebuild, and a skill may replace
> this section. This section is their only copy in the repository.

### Depth

Depth is where a page sits in the folder tree. Deeper means more detail.

| Depth | Pages | Rule |
|---|---|---|
| 1 | `README.md`; `DEVELOPER.md`, `CONTRIBUTING.md` and `SPEC.md` | `README.md` is the entry: overview, inputs and outputs at a glance, usage tip, "where next". The other three are solo: one page each, no child pages |
| 2 | `docs/<topic>.md` | a hub: principle, decision list, routing to depth 3; it names and links facts, and defines none |
| 2 leaf | `docs/<topic>.md` with no `docs/<topic>/` folder; a mode's `<mode>/README.md`, beside its code | a leaf may define, like a depth-3 page |
| 3 | `docs/<topic>/<page>.md` | detail: fact lists, option lists, examples |

- One fact, one page: define a fact on the deepest page that needs it; shallower pages name it and link.

### Every page

1. `# Title`.
2. `## Purpose`: 1 to 3 sentences, who reads the page and what they get; then `Read before:` and `Next:` links where the page sits on a reading path.
3. `## Contents`: links to every other `##` chapter of the page, and nothing else.
4. Only the parts the page needs.

### Parts

| Part | Form | Checked against |
|---|---|---|
| Principle | at most 5 short sentences: the core idea | review |
| Decision list | one line per decision: `decision → path::symbol` where the code realises it | code |
| Fact list | one line per fact the code relies on: `fact → path::symbol`, or a test | code |
| Why | one indented `Why:` line under a rule, decision or fact, at most 20 words | review |
| Option list | every available option with a one-line meaning; complete | the input, output, field or code list in code |
| Example | at most 20 lines; run or parsed by a test | tests |
| Prose | only in Purpose, Principle and one-line list lead-ins; a block is at most 4 lines | review |
| Language | sentences of at most 20 words; active voice; one term per idea, the glossary's | review |

### Limits

- The limits (prose block 4 lines, sentence 20 words, example 20 lines) are targets, not hard caps.
- Exceed one only with a reason, stated next to the block: `<!-- over limit: <reason> -->`.
- Keep the overrun small; split the block when you can.

### Anchors

- `path` is relative to the repository root: `utils/artifact.py::store_artifact`.
- `symbol` is a module-level name, or a dotted one for a member: `ActionInputs._validate`.
- A test is `tests/<path>.py::test_name`; a non-Python file names a text it contains: `Makefile::qa`.
- Never use line numbers; they drift.
- A rule another component must realise names that component instead of an anchor: `→ utilities`, `→ toolkit`.
- On a depth-2 or depth-3 page, every top-level list item ends in `→` and an anchor, a component or a link.
- Items under a lead-in that carries `→` inherit it, e.g. a lead-in `` What this mode fills → `…::build_result`: ``.
- `README.md` is no PyPI description, so it links repository files relatively: `docs/action.md`.

### Examples

- A `yaml` block must parse; every `with:` key it gives this action must be an `action.yml` input.
- Every `uses:` of this action names the same release, so a release bump changes them all.
- A `json` block must parse; a test runs every `python` block, each in a fresh namespace and a temporary directory.
- A `shell` block is a command line, not an example; it is not run.

### Checks

| Check | Where |
|---|---|
| page list and depths, `Purpose` then `Contents`, Contents links, no orphan page, README links relative | `tests/docs/test_page_structure.py` |
| every `path::symbol` resolves; no line-number anchor; every depth-2 list item says where it is realised | `tests/docs/test_anchors.py` |
| every example parses or runs; every `with:` key is an `action.yml` input; one release named | `tests/docs/test_examples.py` |
| the input and output lists equal `action.yml`; every code a page names is in `ALL_CODES` | `tests/docs/test_option_lists.py` |
| links and `#fragments` resolve | `.github/workflows/link-check.yml::lychee` |
| a pull request that changes only a page, `action.yml` or a file a page anchors still runs these tests | `.github/workflows/test.yml::docs_changed`, `tests/docs/test_ci_filter.py` |

To add a page: put it at its depth, add it to `tests/docs/pages.py::APPROVED_PAGES`, and link it from `README.md`.
