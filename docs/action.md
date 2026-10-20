# Action reference

## Purpose

Workflow authors who configure the collector step read this page. It defines every input, the output and its
layout, the run-level errors, and the contracts the action writes.

Read before: [README](../README.md) · Next: [Documentation Source mode](../doc_source/README.md), [UI Tests mode](../ui_tests/README.md)

## Contents

- [Prerequisites](#prerequisites)
- [Inputs](#inputs)
- [Outputs](#outputs)
- [Output layout](#output-layout)
- [Errors](#errors)
- [Contracts](#contracts)
- [GitHub Enterprise Server](#github-enterprise-server)

## Prerequisites

- Every repository a mode reads is checked out (`actions/checkout`) earlier in the job; the action never clones or fetches → `utils/feature_file_discovery.py::discover_feature_files`
- The `doc-source` and `ui-tests` modes read those checkouts only: they call no GitHub API and need no token → `action_inputs.py::ActionInputs`
- Python 3.10 or later is on `PATH` as `python3`, or as `python` when there is no `python3` → `action.yml::sys.version_info`
- A `python3` older than 3.10 fails the step with a one-line error, even if another name on `PATH` would do → `tests/test_action_yml.py::test_an_unsupported_python_fails_with_the_documented_one_line_error`
- The action brings its own venv: it creates one under `$RUNNER_TEMP`, installs its requirements there, and runs with that interpreter → `tests/test_action_yml.py::test_the_action_installs_into_its_own_venv_and_never_the_runners_interpreter`
  - So the caller needs no `actions/setup-python`; the job's interpreter, `PATH` and packages stay untouched.
- The runner reaches a package index: on its first run in a job, the venv step installs the pinned requirements with `pip` → `action.yml::requirements.txt`
  - PyPI by default, or the mirror the runner's `pip.conf` or `PIP_INDEX_URL` sets.
- It runs on Linux runners (`ubuntu-*`), the only platform CI covers; every GitHub-hosted one ships a suitable `python3` → `.github/workflows/integration_test.yml::ubuntu-latest`
  - On a self-hosted runner without `python3`, add `actions/setup-python` before this step.
- Windows runners are not supported: the venv step assumes the POSIX `bin/` layout, not `Scripts/`, so it fails there → [Windows runner support](../SPEC.md#windows-runner-support)
- macOS runners use the same POSIX layout and are expected to work, but no job runs on them → `action.yml::POSIX`

## Inputs

Every input `action.yml` declares, in its order; a test keeps this table equal to it → `tests/docs/test_option_lists.py::test_the_input_table_equals_action_yml`

<!-- over limit: one row per input; the meanings are the one-line option-list entries the page rules ask for -->
| Input | Required | Default | Meaning |
|---|---|---|---|
| `project-id` | yes | — | The project the run documents, written to every artifact's `metadata.source.project_id`; format `PROJECT_ID_PATTERN` ([pipeline rules](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/contracts/pipeline-rules.md), § Project id) |
| `output-path` | no | `./output/collector-gh` | The output root; each mode writes and clears only `<output-path>/<mode>/` ([Output layout](#output-layout)) |
| `allow-partial` | no | `false` | `false`: any failed source fails its mode, and with it the run. `true`: the mode writes without a failed source and records one `SOURCE_UNAVAILABLE` warning for it; it still fails if every source failed |
| `github-server-url` | no | `https://github.com` | The GitHub server the configured repositories live on, used only to build the `source_ref.url` and warning `source_url` permalinks ([GitHub Enterprise Server](#github-enterprise-server)) |
| `github-token` | no | `''` | Unused: the `doc-source` and `ui-tests` modes read local checkouts and make no GitHub API call |
| `doc-issues` | no | `false` | PLANNED: the Documentation Issues mode is not available in this version; `true` fails the run at start ([Documentation Issues](../doc_issues/README.md)) |
| `verbose-logging` | no | `false` | `true` turns on verbose (debug) logging |
| `doc-issues-repositories` | no | `[]` | PLANNED: not read in this version |
| `doc-issues-project-state-mining` | no | `false` | PLANNED: not read in this version |
| `doc-source` | no | `false` | `true` runs the Documentation Source mode |
| `doc-source-repositories` | no | `[]` | The Documentation Source mode's sources, a JSON array ([repository entry](../doc_source/README.md#repository-entry)) |
| `ui-tests` | no | `false` | `true` runs the UI Tests mode |
| `ui-tests-repositories` | no | `[]` | The UI Tests mode's sources, a JSON array ([repository entry](../ui_tests/README.md#repository-entry)) |

- A switch is on only when it is `true`, in any case; any other value, an empty one included, leaves it off and is not reported → `action_inputs.py::ActionInputs.is_allow_partial_enabled`
  - The switches: `doc-source`, `ui-tests`, `doc-issues`, `allow-partial`, `verbose-logging`.
- `project-id`, `github-server-url` and an enabled mode's `*-repositories` are checked before any work; a bad one is `INVALID_CONFIGURATION` ([Errors](#errors)) → `action_inputs.py::ActionInputs._validate`
- A disabled mode's repositories are never read, so a malformed one cannot fail the run → `action_inputs.py::ActionInputs._validate`
- An enabled mode with an empty repository list logs a warning and writes an artifact with no records → `action_inputs.py::_check_repositories`

A step with every base input set; the mode switches take their sources from the mode pages:

```yaml
- name: Living Documentation Collector for GitHub
  id: living_doc_collector_gh
  uses: AbsaOSS/living-doc-collector-gh@v0.2.0
  with:
    project-id: your-project               # required: written to every artifact's metadata.source.project_id
    output-path: ./output/collector-gh     # the default
    allow-partial: true                    # write without a failed source instead of failing the mode
    github-server-url: https://github.com  # the default
    verbose-logging: true                  # debug logging
    doc-source: true                       # sources: doc-source-repositories, see the mode page
    ui-tests: true                         # sources: ui-tests-repositories, see the mode page
```

## Outputs

Every output `action.yml` declares; a test keeps this table equal to it → `tests/docs/test_option_lists.py::test_the_output_table_equals_action_yml`

| Output | Meaning |
|---|---|
| `output-path` | The resolved, absolute output root: the `output-path` input made absolute |

- The input is made absolute against the working directory of the step → `utils/utils.py::make_absolute_path`

```yaml
- name: Show where the collector wrote
  run: echo "Collector output root is ${{ steps.living_doc_collector_gh.outputs.output-path }}"
```

## Output layout

Each enabled mode writes one artifact under the root → `main.py::run`

| Mode | Artifact, with the default `output-path` |
|---|---|
| `doc-source` | `output/collector-gh/doc-source/doc-source.json` |
| `ui-tests` | `output/collector-gh/ui-tests/ui-tests.json` |

- The mode directories are `doc-source` and `ui-tests` → `utils/constants.py::DOC_SOURCE_OUTPUT_PATH`
- A mode creates its directory and replaces it on every run, so any previous content there is removed → `utils/artifact.py::clear_output_dir`
- A mode clears only its own `<output-path>/<mode>/`; nothing else under `output-path` is touched → `utils/artifact.py::collect_artifact`
  - Why: two collectors, or two runs with different `output-path`, in one tree never touch each other's files.
- The layout rule is defined in `living-doc-utilities`, § Collector output layout → [pipeline rules](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/contracts/pipeline-rules.md)

## Errors

Each configured repository entry is one **source**, collected on its own → `utils/artifact.py::collect_sources`

- Codes are defined in `living-doc-utilities` → [errors](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/contracts/errors.md)
- The failure rules are R13 → [pipeline rules](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/contracts/pipeline-rules.md)

<!-- over limit: the effect column states the full failure rule of each code; splitting it would scatter one rule -->
| Situation | Code | Effect | Where |
|---|---|---|---|
| `project-id` missing or malformed; `github-server-url` not an http(s) URL; an enabled mode's `*-repositories` input not a JSON array, or an entry with a missing key or an invalid value | `INVALID_CONFIGURATION` (error) | The run fails at start, before any work: the log names the input, the entry and the reason; no file is written; exit `1` | `action_inputs.py::ActionInputs._validate` |
| `doc-issues: true` | `INVALID_CONFIGURATION` (error) | The run fails at start ([Documentation Issues](../doc_issues/README.md)); exit `1` | `main.py::DOC_ISSUES_PLANNED_MESSAGE` |
| A configured path of a source does not exist | `SOURCE_UNAVAILABLE` (error) | Default: every source is still tried, then the mode fails; the log names each failed source; the run writes no file; exit `1`. With `allow-partial: true`: one warning per failed source, and the mode writes without it; it still fails if every source failed | `utils/artifact.py::collect_sources` |
| A source yields nothing: no entity header (`doc-source`) or scenario (`ui-tests`) is read from it, kept or skipped | `EMPTY_SOURCE` (warning) | Reported in `warnings[]`; the run succeeds | `utils/artifact.py::collect_sources` |
| A source file is outside a git checkout, or its checkout has no resolvable commit | `NO_SOURCE_URL` (warning) | `source_ref.url` is `""`, and the file's warnings carry no `source_url` | `utils/artifact.py::build_source_ref` |

- A failed mode fails the whole run → `main.py::run`
  - A mode that already wrote has its artifact removed: exit `1` leaves no output file, not even the other mode's.
- The exit code is `0` on success and `1` on any failure → `main.py::run`
- `metadata.stats.cardinality.sources_configured` counts the entries of the mode's `*-repositories` input → `doc_source/collector.py::GHDocSourceCollector.build_result`
- `sources_failed` counts the sources that failed while being collected; it is non-zero only with `allow-partial: true` → `utils/artifact.py::collect_sources`
- `metadata.source.repositories` lists only the repositories the artifact documents → `utils/artifact.py::build_metadata`
  - A repository whose every entry failed is not listed, and stays visible through its `SOURCE_UNAVAILABLE` warning.
- Mode-specific warnings → [Documentation Source](../doc_source/README.md#errors), [UI Tests](../ui_tests/README.md#errors)

## Contracts

- The artifacts, `doc-source-v1.0.0` and `ui-tests-v1.0.0`, are contracts owned by `living-doc-utilities` → [documentation contracts](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/contracts.md)
- This repository imports their models and parsers from the pinned `living-doc-utilities` release → `requirements.txt::living-doc-utilities`
- It vendors none of them: no schema file and no local copy of a contract model is committed → `Makefile::no-vendored-schemas`
- Every artifact is written through `write_artifact`, which fills `metadata.stats` and validates the result before anything is written → `utils/artifact.py::store_artifact`
- Until `living-doc-toolkit` moves onto the `living-doc-utilities` release this action pins, `toolkit` on `master` cannot read this output → toolkit
- The authoring formats this action reads and the pipeline it feeds are documented in `living-doc` → [Living Doc Header Types](https://github.com/AbsaOSS/living-doc/blob/master/docs/guides/living-doc-header-types.md), [Collecting from GitHub](https://github.com/AbsaOSS/living-doc/blob/master/docs/guides/github-collection.md), [Architecture](https://github.com/AbsaOSS/living-doc/blob/master/docs/introduction/architecture.md)

## GitHub Enterprise Server

- `source_ref.url` permalinks point at `https://github.com` by default → `utils/github_urls.py::DEFAULT_SERVER_URL`
- For repositories on GitHub Enterprise Server, pass the workflow's own server URL → `utils/github_urls.py::server_url`

```yaml
- name: Living Documentation Collector for GitHub
  uses: AbsaOSS/living-doc-collector-gh@v0.2.0
  with:
    project-id: your-project
    github-server-url: ${{ github.server_url }}
    doc-source: true
    doc-source-repositories: |
        [ { "organization-name": "your-organization-name", "repository-name": "your-ui-repository",
            "us-paths": ["/path/to/checkout/your-ui-repository/features/liv_doc_us"] } ]
```
