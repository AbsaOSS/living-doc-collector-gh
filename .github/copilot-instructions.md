# Copilot Instructions — Living Documentation Collector for GitHub

This file tells a coding agent how to work in this repository. It describes this repo's
own layout, contract, and workflow; it is not shared with or copied from other repos.

**Section order** — keep the sections below in exactly this order:
Overview → Repo specifics → Coding guidelines → Inputs → Language and style →
Logging and string formatting → Docstrings and comments → Patterns → Testing →
Tooling and quality gates → Common pitfalls → Learned rules.

**House rules for this file**

- Must write every guidance bullet as a constraint led by one of `Must`, `Must not`, `Prefer`, `Avoid`.
- Must not put a colon after the leading keyword, and Must not use any other keyword style such as `Do`, `Should`, or a two-keyword `Do` / `Avoid` variant.
- Prefer bullet lists over paragraphs.
- Must end the file with a single trailing newline.

## Overview

`Living Documentation Collector for GitHub` is a composite GitHub Action that data-mines
GitHub Projects, Issues, and locally checked-out repositories for living-documentation
content and writes machine-readable JSON for the downstream `living-doc-*` generators.

- Must treat execution as a GitHub Action on a GitHub-hosted runner as the supported path; the `run_script.sh` / `python3 main.py` flow is a development and debugging affordance only.
- Must read action inputs from `INPUT_*` environment variables and nowhere else.
- Must keep the whole collect pipeline AI-free — deterministic Python only, no LLM call anywhere in that path.
- Prefer keeping environment access at the module boundary — `action_inputs.py` and `main.run()` — and Must keep the collectors and parsers free of environment reads.

## Repo specifics

Module map — a flat package per mode plus shared `utils/`:

| Path | Responsibility |
|---|---|
| `main.py` | Entry point — `run()`; fails at start when the PLANNED `doc-issues` mode is requested, then orchestrates user-config validation and the two mode collectors, sets the `output-path` Action output and maps any failure to exit code `1` |
| `action_inputs.py` | Input layer — `ActionInputs(BaseActionInputs)`, reads every `INPUT_*` via `living_doc_utilities.github.utils.get_action_input`, `_validate()` / `validate_user_configuration()` |
| `doc_issues/` | `doc-issues` mode — PLANNED after v0.1.0; kept aside unchanged for the port, imported by no active module and excluded from pytest, mypy, pylint, coverage and the R12 checks |
| `doc_source/` | `doc-source` mode — `collector.py` (`GHDocSourceCollector`: file discovery, `authoring` parsers, `derive_statuses` + `check_relations` once per run, `DocSourceResult`), `model/config_repository.py` |
| `ui_tests/` | `ui-tests` mode — `collector.py` (`GHUITestsCollector`: file discovery, `authoring.scenario`, `UITestsResult`), `model/config_repository.py` |
| `utils/` | Shared — `artifact.py` (metadata envelope, `source_ref`, warning location, `store_artifact` → `write_artifact`), `constants.py` (`Mode` enum, `INPUT_*` key names, per-mode output sub-paths), `exceptions.py`, `feature_file_discovery.py` (shared file discovery for the source modes), `utils.py` (`make_absolute_path`); `github_project_queries.py` is kept aside with `doc_issues/` |

- Must treat `main.py` function `run()` as the entry point — its step order is setup logging → exit `1` with `INVALID_CONFIGURATION` when `doc-issues` is requested → `ActionInputs().validate_user_configuration()` → for each mode `doc-source` / `ui-tests`: skip when disabled, else `collector_class(output_path).collect()` → `set_action_output("output-path", output_path)` → `sys.exit(1)` when any enabled mode failed.
- Must keep the step order and the `"Liv-Doc collector for GitHub - ..."` step logs in `run()` stable, since `tests/test_main.py` asserts on them.

Inputs — `INPUT_*` environment variables, parsed only in `ActionInputs` (key names in `utils/constants.py`):

| Input | Env var | Required | Notes |
|---|---|---|---|
| `project-id` | `INPUT_PROJECT_ID` | yes | validated against `PROJECT_ID_PATTERN` at start; written to `metadata.source.project_id` |
| `output-path` | `INPUT_OUTPUT_PATH` | no | output root, default `./output/collector-gh` |
| `allow-partial` | `INPUT_ALLOW_PARTIAL` | no | R13 partial mode; default `false` |
| `github-server-url` | `INPUT_GITHUB_SERVER_URL` | no | server of `source_ref.url` permalinks; default `https://github.com` |
| `github-token` | — | no | optional and unused: no v0.1.0 mode calls the GitHub API; not read |
| `doc-issues` | `INPUT_DOC_ISSUES` | no | PLANNED; `"true"` fails the run at start; default `false` |
| `doc-source` | `INPUT_DOC_SOURCE` | yes | mode switch; `"false"` when unset |
| `ui-tests` | `INPUT_UI_TESTS` | yes | mode switch; `"false"` when unset |
| `verbose-logging` | `INPUT_VERBOSE_LOGGING` | no | default `false` |
| `doc-source-repositories` | `INPUT_DOC_SOURCE_REPOSITORIES` | no | JSON array string, default `[]` |
| `ui-tests-repositories` | `INPUT_UI_TESTS_REPOSITORIES` | no | JSON array string, default `[]` |

Contract-sensitive outputs:

- Must keep the Action output key `output-path` stable — set via `set_action_output("output-path", ...)` and exposed by `action.yml` as `output-path`.
- Must keep the per-mode output sub-paths stable — `DOC_SOURCE_OUTPUT_PATH`, `UI_TESTS_OUTPUT_PATH` in `utils/constants.py`.
- Must write each artifact only through `living_doc_utilities.contracts.io.write_artifact` (via `utils.artifact.store_artifact`), and read one only through `read_artifact`; the artifact's shape is the `living-doc-utilities` contract (`doc-source-v1.0.0`, `ui-tests-v1.0.0`), not this repo's.
- Must keep exit-code behaviour stable — `0` on success, `1` on any failure (`doc-issues` requested, user-config validation, or an enabled mode's `collect()` returning `False`). There is no `2`–`5` taxonomy in this repo.
- Must keep the `"Liv-Doc collector for GitHub - ..."` log strings stable — tests assert exact text.

## Coding guidelines

- Must keep changes small and scoped to the task.
- Prefer explicit code over clever constructs.
- Must keep externally visible behaviour stable unless the task is an intentional contract change.
- Must not change existing log texts or error messages without a stated reason.
- Prefer pure functions for parsing and collection logic, and Avoid reading the environment outside `action_inputs.py` and `main.run()`.

## Inputs

- Must read every input through `ActionInputs`, and Must not call `get_action_input` or `os.getenv("INPUT_...")` from any other module.
- Must centralise parsing, defaulting, and validation in `ActionInputs` (`_validate()` / `validate_user_configuration()`).
- Avoid duplicating input validation across modules.
- Must not read any `doc-issues-*` input: the mode is PLANNED, and only its switch is read, to fail the run.

## Language and style

- Must target Python 3.10+ (the ecosystem floor; the action runs on whatever Python ≥ 3.10 is on the caller's `PATH`, and the CI matrix covers 3.10–3.14).
- Must add type hints for new public functions and classes.
- Must keep imports at module top — no imports inside functions or methods.
- Must guard any 3.11+ standard-library use behind a `sys.version_info` fallback, as `utils/constants.py` does for `tomllib` / `tomli`.
- Must not disable a linter rule inline unless this file records the exception under Learned rules.

## Logging and string formatting

- Must use `logging`, never `print`.
- Must use lazy `%` formatting in logging calls — `logger.info("msg %s", value)`.
- Must not use f-strings inside logging calls.
- Prefer the clearest formatting when constructing exception and failure messages, and Must keep contract-sensitive strings stable.

## Docstrings and comments

- Must match the existing module docstring style — a short summary of what the module contains.
- Prefer a one-line docstring summary for functions, with `@param` / `@return` / `@raise` lines where they add information, matching the surrounding code.
- Prefer self-explanatory code, and Prefer comments only for intent, edge cases, and the "why".
- Avoid tutorial-style prose or long examples in docstrings.

## Patterns

- Prefer leaf modules raising the typed exceptions in `utils/exceptions.py`.
- Must let `main.run()` be the only place that translates a failure into an Action-failure exit code.
- Prefer private helpers (`_name`) for internal collector behaviour (`_collect_*`, `_load_repositories`).
- Must keep integration boundaries — the GitHub REST API and the filesystem — explicit and mockable.
- Must parse authored text only with `living_doc_utilities.authoring` (`feature_header`, `page_object`, `scenario`, `identity`, `status`, `relations`), and Must not add a local parser, normaliser or contract model.

## Testing

- Must use `pytest` with `pytest-mock` (`mocker`), and Must not use `unittest`.
- Must keep tests under `tests/`, mirroring the package layout — `tests/doc_source/`, `tests/ui_tests/`, `tests/utils/`, plus `tests/test_main.py`, `tests/test_action_inputs.py` and `tests/test_contract_checks.py`.
- Must test behaviour — return values, raised exceptions, log messages, exit codes.
- Must mock `INPUT_*` environment variables and the GitHub API in unit tests.
- Must not call external services or the real GitHub API in unit tests.
- Prefer shared fixtures in `tests/conftest.py`.
- Must treat the contracts as owned by `living-doc-utilities` — imported, never vendored: no committed `*-schema.json`, no local contract model.
- Must keep each mode's R12 check 3 test (`tests/<mode>/test_full_sample.py`) green — every contract field has occupancy > 0 over the fully authored fixture, or is in `NOT_PRODUCED` with a reason.
- Must not edit `tests/fixtures/golden/` — it is copied verbatim from `living-doc-utilities` at the pinned tag.

## Tooling and quality gates

- Must run `make qa` before finishing a code change — it runs `format-check` → `lint` → `types` → `no-vendored-schemas` → `retired-names` → `runtime-requirements` → `coverage` and fails on the first failing gate.
- Must use the individual targets while iterating — `make format`, `make format-check`, `make lint`, `make types`, `make runtime-requirements`, `make test`, `make coverage`.
- Must keep `make lint` clean — it runs ruff (`E` / `F` / `I` / `B` over tracked `*.py`, config in `pyproject.toml`) then Pylint, and Pylint must score 9.5 or higher.
- Must keep `make format-check` (Black, line length 120, config in `pyproject.toml`) clean, and Prefer `make format` (ruff autofix + Black) to fix import order and formatting in one step.
- Must keep `make types` (mypy, config in `pyproject.toml`) clean, and Prefer fixing types over adding ignores.
- Must keep `make coverage` (pytest, `--cov-fail-under=80`) passing.
- Must expect `.github/workflows/test.yml` to call the same `make` targets, so local and CI never drift.

## Common pitfalls

- Must verify a new dependency supports Python 3.10 before adding it, and Must keep `requirements.txt` and `action.yml` in step when inputs or dependencies change. Must put a test, lint or type pin in `requirements-dev.txt`, never in `requirements.txt`, which the action installs on every run.
- Must remove unused imports and variables in the same change, and Avoid leaving dead code.
- Avoid changing externally visible strings, the `output-path` key, per-mode output sub-paths, or exit codes unless the task calls for it.
- Must keep new source-mode behaviour behind the `feature_file_discovery` utility rather than re-implementing file walking per mode.

## Learned rules

- Must keep the `"Liv-Doc collector for GitHub - ..."` log strings and exit code `1` stable — `tests/test_main.py` asserts exact strings and `sys.exit(1)`.
- Must not introduce a `2`–`5` exit-code taxonomy; this action reports success as `0` and every failure as `1`.
- Must keep the `tomllib` / `tomli` `sys.version_info` guard in `utils/constants.py` — it is what keeps the 3.10 floor working.
