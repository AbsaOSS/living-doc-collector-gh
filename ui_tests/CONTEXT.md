# ui_tests

Parent: [../CONTEXT.md](../CONTEXT.md)

## Purpose

The `ui-tests` mode: `GHUITestsCollector` and its repository entry. Its behaviour is [README.md](README.md); this
file maps that page to the code.

Not responsible for: file discovery, the metadata envelope and writing the artifact (`utils/`, the root
`CONTEXT.md`); parsing scenarios and their `@AC:` tags (`living_doc_utilities.authoring.scenario`).

## Code map

What realises each fact of [README.md](README.md), the mode's page:

- The mode mines scenario blocks into one `ui-tests-v1.0.0` artifact → `ui_tests/collector.py::GHUITestsCollector`
- `ui-tests: true` turns it on → `action_inputs.py::ActionInputs.is_ui_tests_mode_enabled`
- Each entry is one source; a malformed entry fails the run at start → `ui_tests/model/config_repository.py::ConfigRepository.load_from_json`
- A missing configured path fails its whole source → `utils/feature_file_discovery.py::discover_feature_files`
- Discovery is recursive; `tutorial*` directories are skipped → `utils/feature_file_discovery.py::_is_under_tutorial_dir`
- The output file name → `ui_tests/collector.py::UI_TESTS_FILE_NAME`
- Written through `write_artifact`: validated, then written atomically → `utils/artifact.py::store_artifact`
- What the mode fills in the contract → `ui_tests/collector.py::GHUITestsCollector.build_result`
- One scenario per `Scenario:` or `Scenario Outline:` → `ui_tests/collector.py::GHUITestsCollector._collect_file`
- A file whose feature-level tags include `@tutorial` is not mined → `ui_tests/collector.py::_is_tutorial_file`
- A scenario tagged `@tutorial` is not mined → `ui_tests/collector.py::_without_tutorial_scenarios`
- `scenario_id` is `<org>/<repo>/<native_id>/<title slug>` → `ui_tests/collector.py::GHUITestsCollector._collect_file`
- The slug, `-2`, `-3` for a repeat within a file, `scenario` for a title with no ASCII letter or digit → `ui_tests/collector.py::_slugify`
- `source_ref`, its permalink and `NO_SOURCE_URL` → `utils/artifact.py::build_source_ref`
- A path with no matching files logs a warning → `utils/feature_file_discovery.py::discover_feature_files`
- An unreadable file is logged and skipped → `ui_tests/collector.py::GHUITestsCollector._collect_file`
- A malformed `@AC:` tag: `MALFORMED_AC`, the scenario kept → `ui_tests/collector.py::GHUITestsCollector._collect_file`
- `NO_SOURCE_URL` only when the file yields a scenario → `ui_tests/collector.py::GHUITestsCollector._collect_file`
- A `scenario_id` already collected: `AUTHORING_ERROR`, the first file keeps it → `ui_tests/collector.py::GHUITestsCollector._collect_file`
- A result that fails validation or cannot be written fails the mode → `utils/artifact.py::collect_artifact`
- A warning with a `path` carries the file's `source_url` → `utils/artifact.py::file_url`
