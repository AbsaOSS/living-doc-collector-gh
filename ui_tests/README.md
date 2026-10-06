# UI Tests Mode

- [Mode De/Activation](#mode-deactivation)
- [Prerequisites](#prerequisites)
- [Usage](#usage)
- [Mode Inputs](#mode-inputs)
- [Output](#output)
- [Errors](#errors)
- [Formats](#formats)

This mode mines UI test scenarios from `.feature` file **scenario blocks** in locally checked-out
repositories and writes one `ui-tests-v1.0.0` artifact.

## Mode De/Activation

- **ui-tests**
  - **Description**: Enables or disables the UI Tests mode.
  - **Usage**: Set to `true` to activate.
  - **Example**:
    ```yaml
    with:
      ui-tests: true
    ```

---
## Prerequisites

1. **Checkout before action** — the caller performs `actions/checkout` for every target repository
   before invoking this action. This action never clones or fetches repository contents itself, and needs no
   token.
2. **No output folder to prepare** — the action creates `<output-path>/ui-tests/` itself and replaces it on
   every run, so any previous content there is removed. Nothing else under `output-path` is touched.

---
## Usage

See the default minimal UI Tests mode action step definition:

```yaml
- name: Living Documentation Collector for GitHub
  id: living_doc_collector_gh
  uses: AbsaOSS/living-doc-collector-gh@v0.1.0
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

The base inputs (`project-id`, `output-path`, `allow-partial`, `github-server-url`) are in the
[root README](../README.md#base-inputs).

---
## Mode Inputs

| Input Name              | Description                                                            | Required | Default |
|-------------------------|------------------------------------------------------------------------|----------|---------|
| `ui-tests-repositories` | JSON array of the locally checked-out repositories to scan; each entry is one source. | No       | `'[]'`  |

Each repository entry:

| Field               | Type     | Required | Description |
|---------------------|----------|----------|-------------|
| `organization-name` | string   | yes      | GitHub org name (used in `scenario_id`, `source_ref.url` and `metadata.source`); non-empty, no `/`. |
| `repository-name`   | string   | yes      | GitHub repo name (used in `scenario_id`, `source_ref.url` and `metadata.source`); non-empty, no `/`. |
| `paths`             | string[] | yes      | Absolute directory paths to scan for `.feature` files. |

Every configured path must exist. Within one, discovery is recursive, and `.feature` files under a
`tutorial*` / `tutorial_<group>` directory are skipped.

---
## Output

`<output-path>/ui-tests/ui-tests.json` (by default `output/collector-gh/ui-tests/ui-tests.json`), a
[`ui-tests-v1.0.0`](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/contracts.md)
artifact written through `write_artifact`: validated before the write and written atomically.

What this mode fills in the contract:

- **`metadata.source.project_id`** — the `project-id` input.
- **`metadata.stats.cardinality`** — `sources_configured` and `sources_failed` as in the
  [root README](../README.md#errors).
- **`scenarios[]`** — one per `Scenario:` / `Scenario Outline:`, except a scenario tagged `@tutorial` and every
  scenario of a file whose feature-level tags include `@tutorial`.
- **`scenario_id`** — `{organization-name}/{repository-name}/{source_ref.native_id}/{title-slug}`, so the
  file's path is the one from its repository root, whichever scan root found it; a slug repeated within one
  file gets `-2`, `-3`, … appended; a title with no ASCII letter or digit gets the slug `scenario`.
- **`source_ref`** — `system: GitHub`; `native_id` is the file's path from its repository root;
  `native_type` is `scenario`; `url` is the file's permalink at its checkout's commit,
  `<github-server-url>/<org>/<repo>/blob/<git rev-parse HEAD>/<native_id>`; `tracker_state` is `committed`.

---
## Errors

The run-level codes (`INVALID_CONFIGURATION`, `SOURCE_UNAVAILABLE`, `EMPTY_SOURCE`, `NO_SOURCE_URL`) and
`allow-partial` are in the [root README](../README.md#errors). Within a source:

| Situation | Behaviour |
|---|---|
| A path in `paths` has no matching files | Log warning, continue; a source with no scenario at all is `EMPTY_SOURCE` |
| A file cannot be read | Log warning, skip file, continue |
| A malformed `@AC:` tag | `MALFORMED_AC` warning with the file's `path`; the scenario is kept without that link |
| A file outside a git checkout | `NO_SOURCE_URL`, only when the file yields a scenario |
| A `scenario_id` is already collected from another file (e.g. one file reached through two repository entries) | The scenario is skipped; `AUTHORING_ERROR` warning with the file's `path` and the `scenario_id`; the first file read keeps it |
| The result fails contract validation, or the file cannot be written | Log error, no output file, the mode fails |

---
## Formats

Scenarios and their `@AC:<id>[/aspect:<value>]` tags follow the canon in `living-doc`'s
[Living Doc Header Types](https://github.com/AbsaOSS/living-doc/blob/master/docs/guides/living-doc-header-types.md)
and [Living Doc Glossary](https://github.com/AbsaOSS/living-doc/blob/master/docs/guides/living-doc-glossary.md).
This mode parses them with `living-doc-utilities`' `authoring.scenario` parser.
