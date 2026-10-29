# tests

Parent: [../CONTEXT.md](../CONTEXT.md)

## Purpose

The pytest suite: unit tests per module, the R12 contract checks over the full-sample fixtures, the golden-entity
checks and the documentation checks (`tests/docs/`).

Not responsible for: a run over a real checkout (`local-integration.sh`).

## Conventions

- `pytest` with `pytest-mock` (`mocker`), never `unittest`.
- The layout mirrors the package: `tests/doc_source/`, `tests/ui_tests/`, `tests/utils/`, plus `tests/test_main.py`,
  `tests/test_action_inputs.py` and `tests/test_contract_checks.py`. Shared fixtures live in `tests/conftest.py`.
- Mock `INPUT_*` variables and the GitHub API; never make a real network call.
- Test behaviour: return values, raised exceptions, log messages, exit codes.
- Read an artifact only with `living_doc_utilities.contracts.io.read_artifact` and assert on the typed model it
  returns (`DocSourceResult`, `UITestsResult`), never `json.load` and dict checks.

## Mock and fixture surface

| What you fake | Pattern | Copy it from |
|---|---|---|
| `INPUT_*` action inputs | `monkeypatch.setenv("INPUT_...", ...)` or `mocker.patch("<module>.ActionInputs.get_*", return_value=...)` | `tests/test_action_inputs.py` |
| Repository scan configuration | `mocker.patch("doc_source.collector.ActionInputs.get_doc_source_repositories", return_value=[...])` pointing at `tmp_path` dirs | `tests/doc_source/test_collector.py::_configure` |
| `GITHUB_OUTPUT` file | the autouse `_set_github_output_env` fixture points it at `tmp_path` | `tests/conftest.py` |
| `GITHUB_*` run context in `metadata.run` | `monkeypatch.setenv("GITHUB_RUN_ID", ...)` and the like | `tests/doc_source/test_full_sample.py::_artifact` |
| A git checkout, for `source_ref.url` | the `git_checkout` fixture: a real `git init` with one commit, returning its HEAD sha (a bare `.git` directory resolves no commit, so it gives `NO_SOURCE_URL`); or patch `utils.artifact.find_repo_root` to `None` | `tests/conftest.py` |
| An unreadable source file | patch `pathlib.Path.read_text` with `autospec=True` and raise only for `.feature` / `.ts` suffixes | `tests/doc_source/test_collector.py::test_unreadable_file_is_skipped` |
| A contract validation failure | patch the collector's `build_metadata` to return a `model_construct`-ed invalid `Source`, so `write_artifact`'s own validation fails | `tests/doc_source/test_collector.py::test_collect_validation_failure_leaves_no_output_file` |
| Logging assertions | `mocker.patch("<module>.logger")` and assert on `.info` / `.warning` / `.error` | `tests/doc_source/test_collector.py` |
| `main.run()` exit code and logs | `mocker.patch("sys.exit")` and `mock_log_info.assert_has_calls([...])`; or `pytest.raises(SystemExit)` when the run must stop | `tests/test_main.py` |

## Invariants and gotchas

- No tests for `doc_issues/`: the mode is PLANNED and kept aside; `tests/doc_issues/` is outside pytest (`addopts`
  in `pyproject.toml`) and coverage.
- R12 check 3: each mode's `test_full_sample.py` runs the collector over `tests/fixtures/full_sample/<mode>/` and
  requires every `metadata.stats.field_occupancy` path to be above 0, or listed in `NOT_PRODUCED` with a reason. To
  change what a mode emits, add the authored input to that fixture and let the test fail while the field stays empty.
- `tests/fixtures/golden/` is copied verbatim from `living-doc-utilities` at the pinned tag; never edit it.
- `make coverage` requires 80 % (`COV_MIN` in the `Makefile`).
- `tests/docs/` checks every tracked Markdown page: a new page goes into `APPROVED_PAGES` in `tests/docs/pages.py`.
  Agent files and `CONTEXT.md` files are not pages (`NOT_PAGES`, `tracked_markdown()`).
- `tests/docs/test_option_lists.py` collects upper-case names from every tracked or untracked, non-ignored file outside
  `tests/` that isn't Markdown, and expects `NOT_PRODUCED` among none of them: a stray local file naming it fails
  the test.

## Read more

- [DEVELOPER.md](../DEVELOPER.md#checks): what the documentation checks enforce.
