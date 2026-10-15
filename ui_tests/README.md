# UI Tests Mode

## Purpose

Workflow authors who mine UI test scenarios from `.feature` files read this page. It defines the mode's
repository entry, what it discovers and writes, and how it reports problems.

Read before: [Documentation Source mode](../doc_source/README.md) · Next: back to the [Action reference](../docs/action.md)

## Contents

- [Activation](#activation)
- [Usage](#usage)
- [Repository entry](#repository-entry)
- [Discovery](#discovery)
- [Output](#output)
- [Errors](#errors)
- [Formats](#formats)

## Activation

The mode mines scenario blocks from `.feature` files in local checkouts and writes one `ui-tests-v1.0.0` artifact → `ui_tests/collector.py::GHUITestsCollector`

- `ui-tests: true` turns it on; `ui-tests-repositories` lists its sources ([Inputs](../docs/action.md#inputs)) → `action_inputs.py::ActionInputs.is_ui_tests_mode_enabled`
- The checkouts and the output directory need nothing beyond the action's own rules → [Prerequisites](../docs/action.md#prerequisites), [Output layout](../docs/action.md#output-layout)

## Usage

```yaml
- name: Living Documentation Collector for GitHub
  id: living_doc_collector_gh
  uses: AbsaOSS/living-doc-collector-gh@v0.2.0
  with:
    project-id: aul
    ui-tests: true                         # ui-tests mode de/activation
    ui-tests-repositories: |
        [
          {
            "organization-name": "absa-group",
            "repository-name": "aul-ui",
            "paths": ["/path/to/checkout/aul-ui/playwright/features/liv_doc_us"]
          }
        ]
```

## Repository entry

Each entry of `ui-tests-repositories` is one source; a malformed entry fails the run at start → `ui_tests/model/config_repository.py::ConfigRepository.load_from_json`

| Field | Type | Required | Meaning |
|---|---|---|---|
| `organization-name` | string | yes | GitHub organization, used in `scenario_id`, `source_ref.url` and `metadata.source`; non-empty, no `/` |
| `repository-name` | string | yes | GitHub repository name, used in `scenario_id`, `source_ref.url` and `metadata.source`; non-empty, no `/` |
| `paths` | string[] | yes | Absolute directory paths to scan for `.feature` files |

## Discovery

- Every configured path must exist; a missing one fails its whole source → `utils/feature_file_discovery.py::discover_feature_files`
- Within a path, discovery is recursive, and `.feature` files under a `tutorial*` or `tutorial_<group>` directory are skipped → `utils/feature_file_discovery.py::_is_under_tutorial_dir`

## Output

- `<output-path>/ui-tests/ui-tests.json`, by default `output/collector-gh/ui-tests/ui-tests.json` → `ui_tests/collector.py::UI_TESTS_FILE_NAME`
- A [`ui-tests-v1.0.0`](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/contracts.md) artifact, written through `write_artifact`: validated before the write and written atomically → `utils/artifact.py::store_artifact`

What this mode fills in the contract → `ui_tests/collector.py::GHUITestsCollector.build_result`:

- **`metadata.source.project_id`**: the `project-id` input.
- **`metadata.stats.cardinality`**: `sources_configured` and `sources_failed` as in [Errors](../docs/action.md#errors).
- **`scenarios[]`**: one per `Scenario:` or `Scenario Outline:` → `ui_tests/collector.py::_is_tutorial_file`
  - Not mined: a scenario tagged `@tutorial`, and every scenario of a file whose feature-level tags include `@tutorial`.
- **`scenario_id`**: `{organization-name}/{repository-name}/{source_ref.native_id}/{title-slug}`, so the file's path is repository-root-relative inside Git and scan-root-relative outside Git → `ui_tests/collector.py::GHUITestsCollector._collect_file`
  - A slug repeated within one file gets `-2`, `-3`, … appended; a title with no ASCII letter or digit gets the slug `scenario`.
- **`source_ref`**: `system: GitHub`; `native_id` is repository-root-relative inside Git and scan-root-relative outside Git; `native_type` is `scenario`; `url` is the file's permalink at its checkout's commit, `<github-server-url>/<org>/<repo>/blob/<git rev-parse HEAD>/<native_id>`; `tracker_state` is `committed` → `utils/artifact.py::build_source_ref`
  - Outside a Git checkout, `url` is empty and `NO_SOURCE_URL` is emitted.

## Errors

The run-level codes and `allow-partial` are in the action reference → [Errors](../docs/action.md#errors). Within a source:

<!-- over limit: each behaviour cell is one rule with its warning fields; splitting it would scatter the rule -->
| Situation | Behaviour | Where |
|---|---|---|
| A path in `paths` has no matching files | Log warning, continue; a source with no scenario at all is `EMPTY_SOURCE` | `utils/feature_file_discovery.py::discover_feature_files` |
| A file cannot be read | Log warning, skip the file, continue | `ui_tests/collector.py::GHUITestsCollector._collect_file` |
| A malformed `@AC:` tag | `MALFORMED_AC` warning with the file's `path`; the scenario is kept without that link | `ui_tests/collector.py::GHUITestsCollector._collect_file` |
| A file outside a git checkout | `NO_SOURCE_URL`, only when the file yields a scenario | `ui_tests/collector.py::GHUITestsCollector._collect_file` |
| A `scenario_id` already collected from another file (e.g. one file reached through two repository entries) | The scenario is skipped; `AUTHORING_ERROR` warning with the file's `path` and the `scenario_id`; the first file read keeps it | `ui_tests/collector.py::GHUITestsCollector._collect_file` |
| The result fails contract validation, or the file cannot be written | Log error; the mode fails, and with it the run, which writes no file | `utils/artifact.py::collect_artifact` |

## Formats

- Scenarios and their `@AC:<id>[/aspect:<value>]` tags follow the canon in `living-doc` → [Living Doc Header Types](https://github.com/AbsaOSS/living-doc/blob/master/docs/guides/living-doc-header-types.md), [Living Doc Glossary](https://github.com/AbsaOSS/living-doc/blob/master/docs/guides/living-doc-glossary.md)
- This mode parses them with `living-doc-utilities`' `authoring.scenario` parser → utilities
