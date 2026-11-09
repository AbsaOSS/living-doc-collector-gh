# living-doc-collector-gh

## Purpose

A composite GitHub Action, the collect step of the living-documentation pipeline: it reads locally checked-out
repositories and writes JSON artifacts, in the contracts `living-doc-utilities` owns, for the downstream
`living-doc-*` tools.

Not responsible for: the artifact contracts, their models and the authoring parsers (all in `living-doc-utilities`);
normalizing or generating documentation (later pipeline steps).

## How it fits

- Entry point: `main.py::run()`, which `action.yml` runs in the venv it builds under `$RUNNER_TEMP` from
  `requirements.txt`.
- Modes: `doc-source` and `ui-tests` are active. `doc-issues` is PLANNED: requesting it fails the run at start.
- Depends on: `living-doc-utilities`, pinned in `requirements.txt`, for input reading (`BaseActionInputs`,
  `get_action_input`), logging setup, the authoring parsers, the contract models and `write_artifact`.
- Contracts: `doc-source-v1.0.0` and `ui-tests-v1.0.0`, imported from `living_doc_utilities.contracts`, never vendored.

| Path | Holds |
|---|---|
| `main.py` | `run()`: the step order, the `output-path` Action output and the exit code |
| `action_inputs.py` | `ActionInputs(BaseActionInputs)`: every `INPUT_*` read, its default and its validation (`_validate()`, `validate_user_configuration()`) |
| `doc_source/`, `ui_tests/` | one mode each: `collector.py` (`GHDocSourceCollector`, `GHUITestsCollector`) and `model/config_repository.py` → [doc_source/CONTEXT.md](doc_source/CONTEXT.md), [ui_tests/CONTEXT.md](ui_tests/CONTEXT.md) |
| `utils/artifact.py` | the metadata envelope, `source_ref`, warning location, collecting each source on its own (R13), and running a mode: `collect_artifact` → `store_artifact` → `write_artifact` |
| `utils/constants.py` | the `Mode` enum, input key names, per-mode output sub-paths |
| `utils/` (other) | `feature_file_discovery.py` (file discovery for both modes), `github_urls.py` (permalinks), `exceptions.py`, `utils.py` |
| `tools/` | `check_runtime_requirements.py` (the `make runtime-requirements` gate), `local_integration.py` (validates and reports a `local-integration.sh` run) |
| `doc_issues/`, `utils/github_project_queries.py` | the PLANNED `doc-issues` mode, kept aside unchanged for its port → [doc_issues/CONTEXT.md](doc_issues/CONTEXT.md) |
| `tests/` | the pytest suite → [tests/CONTEXT.md](tests/CONTEXT.md) |

`run()` order: set up logging → exit `1` with `INVALID_CONFIGURATION` when `doc-issues` is requested →
`ActionInputs().validate_user_configuration()` → per mode, `doc-source` then `ui-tests`: skip when disabled, else
`collector_class(output_path).collect()` → when a mode failed, clear what the other modes wrote (R13) →
`set_action_output("output-path", output_path)` → `sys.exit(1)` when a mode failed.

## Conventions

- Read action inputs only through `ActionInputs`: no `get_action_input` or `os.getenv("INPUT_...")` in any other
  module, and no environment reads in collectors or parsers. Read no `doc-issues-*` input; only the mode switch, to
  fail the run.
- Parse authored text only with `living_doc_utilities.authoring` (`feature_header`, `page_object`, `scenario`,
  `status`, `relations` and the rest). Add no local parser, normaliser or contract model.
- Write an artifact only through `utils.artifact.store_artifact` (→ `write_artifact`); read one only with
  `living_doc_utilities.contracts.io.read_artifact`.
- Walk source files only through `utils/feature_file_discovery.py`, not per mode.
- Leaf modules raise the typed exceptions in `utils/exceptions.py`; only `main.run()` turns a failure into an exit code.
- Internal collector behaviour lives in private helpers (`_name`).
- Python 3.10 is the floor; CI runs 3.10 to 3.14. Guard 3.11+ standard-library use with a `sys.version_info`
  fallback, as the `tomllib` / `tomli` import in `utils/constants.py` does.
- Imports at module top. Type hints on new public functions and classes.
- `logging`, never `print`. Lazy `%` formatting in log calls (`logger.info("msg %s", value)`), no f-strings.
- Module docstring: a short summary of what the module contains. Function docstring: a one-line summary, with
  `@param` / `@return` / `@raise` lines where they add information.
- No inline linter disable or `# type: ignore` without a recorded reason.

## Key decisions

- The pipeline is AI-free: deterministic Python, no LLM call in the collect path →
  [CONTRIBUTING.md](CONTRIBUTING.md#ai-free-principle).
- Exit codes are `0` for success and `1` for any failure, with no `2`–`5` taxonomy (reason unknown).
- A failed mode fails the run, and `run()` then removes what the other modes wrote, so exit `1` after the modes ran
  leaves no output file (R13). A failure at start (`doc-issues` requested, invalid configuration) exits before any
  mode clears its directory, so a previous run's output stays; a directory that can't be removed is logged as an
  error → [docs/action.md](docs/action.md#errors).
- The contracts belong to `living-doc-utilities`: a field's shape changes there and arrives by re-pinning. No
  `*-schema.json` of an active contract is committed here (`make no-vendored-schemas`, which skips `tests/` and the
  kept-aside `doc_issues/`).
- `requirements.txt` is runtime-only, because `action.yml` installs it on every caller's run. Test, lint and type tools
  go in `requirements-dev.txt` (`make runtime-requirements`).
- The supported path is the Action on a GitHub-hosted runner. `local-integration.sh` and a hand-run `python3 main.py`
  are development and operator checks; no workflow calls them.

## Invariants and gotchas

- Contract-sensitive, stable unless the task changes the contract: the Action output key `output-path`, the per-mode
  sub-paths `DOC_SOURCE_OUTPUT_PATH` / `UI_TESTS_OUTPUT_PATH`, the exit codes, and the
  `"Liv-Doc collector for GitHub - ..."` log strings, which `tests/test_main.py` asserts exactly.
- `doc_issues/` and the modules only it uses are outside pytest, coverage, mypy, Pylint and the formatting checks
  (`pyproject.toml`, `Makefile::KEPT_ASIDE`).
- `requirements.txt` and `action.yml` change together when inputs or dependencies change.
- A hand-run `main.py` needs `GITHUB_OUTPUT` set, or its last step fails with a `KeyError`.

## Code map

What realises each fact of [`docs/action.md`](docs/action.md), the action's reference:

- Every repository is checked out earlier in the job; the action never clones or fetches → `utils/feature_file_discovery.py::discover_feature_files`
- The modes call no GitHub API and need no token → `action_inputs.py::ActionInputs`
- Python 3.10 or later on `PATH`, `python3` first, then `python` → `action.yml::sys.version_info`
- A `python3` below 3.10 fails the step with one line → `tests/test_action_yml.py::test_an_unsupported_python_fails_with_the_documented_one_line_error`
- The action's own venv under `$RUNNER_TEMP`; the caller's interpreter stays untouched → `tests/test_action_yml.py::test_the_action_installs_into_its_own_venv_and_never_the_runners_interpreter`
- The venv step installs the pinned requirements with `pip` → `action.yml::requirements.txt`
- Linux runners, the only platform CI covers → `.github/workflows/integration_test.yml::ubuntu-latest`
- macOS runners share the POSIX venv layout → `action.yml::POSIX`
- The input table equals `action.yml` → `tests/docs/test_option_lists.py::test_the_input_table_equals_action_yml`
- A switch is on only when it is `true`, in any case → `action_inputs.py::ActionInputs.is_allow_partial_enabled`
- `project-id`, `github-server-url` and an enabled mode's repositories are checked before any work → `action_inputs.py::ActionInputs._validate`
- A disabled mode's repositories are never read → `action_inputs.py::ActionInputs._validate`
- An enabled mode with no repositories warns and writes an artifact with no records → `action_inputs.py::_check_repositories`
- The output table equals `action.yml` → `tests/docs/test_option_lists.py::test_the_output_table_equals_action_yml`
- The `output-path` output is the input made absolute → `utils/utils.py::make_absolute_path`
- Each enabled mode writes one artifact under the root → `main.py::run`
- The mode directories → `utils/constants.py::DOC_SOURCE_OUTPUT_PATH`
- A mode replaces its directory on every run → `utils/artifact.py::clear_output_dir`
- A mode clears only its own `<output-path>/<mode>/` → `utils/artifact.py::collect_artifact`
- Each repository entry is one source, collected on its own → `utils/artifact.py::collect_sources`
- `INVALID_CONFIGURATION` for a bad input, before any work → `action_inputs.py::ActionInputs._validate`
- `INVALID_CONFIGURATION` for `doc-issues: true` → `main.py::DOC_ISSUES_PLANNED_MESSAGE`
- `SOURCE_UNAVAILABLE`, with and without `allow-partial` → `utils/artifact.py::collect_sources`
- `EMPTY_SOURCE` → `utils/artifact.py::collect_sources`
- `NO_SOURCE_URL`, and an empty `source_ref.url` → `utils/artifact.py::build_source_ref`
- A failed mode fails the run and removes what the other modes wrote → `main.py::run`
- Exit code `0` on success, `1` on any failure → `main.py::run`
- `sources_configured` counts the `*-repositories` entries → `doc_source/collector.py::GHDocSourceCollector.build_result`
- `sources_failed` counts the sources that failed → `utils/artifact.py::collect_sources`
- `metadata.source.repositories` lists only the repositories the artifact documents → `utils/artifact.py::build_metadata`
- The contract models and parsers come from the pinned `living-doc-utilities` → `requirements.txt::living-doc-utilities`
- No schema file or model copy of the two contracts is committed → `Makefile::no-vendored-schemas`
- Every artifact is written through `write_artifact` → `utils/artifact.py::store_artifact`
- `source_ref.url` permalinks default to `https://github.com` → `utils/github_urls.py::DEFAULT_SERVER_URL`
- `github-server-url` sets the permalinks' server → `utils/github_urls.py::server_url`

## Read more

- [docs/action.md](docs/action.md): inputs, outputs, output layout, run-level errors and contracts.
- [doc_source/README.md](doc_source/README.md), [ui_tests/README.md](ui_tests/README.md): each mode's activation,
  discovery, output and errors.
- [DEVELOPER.md](DEVELOPER.md): setup, the gates, the debug run, the local integration run, release, and the rules for
  writing documentation.
- [SPEC.md](SPEC.md): what isn't built yet; [docs-lifecycle](.claude/rules/docs-lifecycle.md) moves a shipped section
  into the live docs.
