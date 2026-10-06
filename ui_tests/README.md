# UI Tests Mode

- [Mode De/Activation](#mode-deactivation)
- [Prerequisites](#prerequisites)
- [Usage](#usage)
- [Mode Inputs](#mode-inputs)
- [Feature File Scenario Format](#feature-file-scenario-format)
- [Expected Output](#expected-output)

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
   before invoking this action. This action never clones or fetches repository contents itself.
2. **No output folder to prepare** — the action creates the mode's `ui-tests/` output directory itself and
   replaces it on every run, so any previous content there is removed.

---
## Usage

See the default minimal UI Tests mode action step definition:

```yaml
- name: Living Documentation Collector for GitHub
  id: living_doc_collector_gh
  uses: AbsaOSS/living-doc-collector-gh@v0.1.0
  env:
    GITHUB-TOKEN: ${{ secrets.REPOSITORIES_ACCESS_TOKEN }}
  with:
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

---
## Mode Inputs

| Input Name              | Description                                                            | Required | Default | Usage |
|-------------------------|------------------------------------------------------------------------|----------|---------|-------|
| `ui-tests-repositories` | A JSON string defining the locally checked-out repositories to scan.   | No       | `'[]'`  | Provide a list of repositories with `organization-name`, `repository-name`, and `paths` (absolute directory paths to scan). |

---
## Feature File Scenario Format

Scenarios and their `@AC:<id>[/aspect:<value>]` tags follow the canon in `living-doc`'s
[Living Doc Header Types](https://github.com/AbsaOSS/living-doc/blob/master/docs/guides/living-doc-header-types.md)
and [Living Doc Glossary](https://github.com/AbsaOSS/living-doc/blob/master/docs/guides/living-doc-glossary.md).
This mode parses them with `living-doc-utilities`' `authoring.scenario` parser.

What this mode adds around the parser:

- **`@tutorial`** — a scenario tagged `@tutorial`, or every scenario of a file whose feature-level tags
  include `@tutorial`, is not mined; `.feature` files under a `tutorial*` / `tutorial_<group>`
  directory are skipped at discovery time.
- **`scenario_id`** — `{organization-name}/{repository-name}/{source_ref.native_id}/{title-slug}`, so the
  file's path is the one from its repository root, whichever scan root found it; a slug repeated within one
  file gets `-2`, `-3`, … appended; a title with no ASCII letter or digit gets the slug `scenario`.

---
## Expected Output

The mode writes `output/ui-tests/ui-tests.json`, a
[`ui-tests-v1.0.0`](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/contracts.md)
artifact, through `write_artifact`: the result is validated before the write and written atomically.

| Key | Content |
|---|---|
| `schema_version` | `ui-tests-v1.0.0` |
| `metadata` | the standard envelope — `producer`, `run` (GitHub Actions context), `source`, `generated_at`, `stats` |
| `warnings[]` | every parser warning (e.g. a malformed `@AC:` tag), each with the source file's `path` in its `context` |
| `scenarios[]` | one contract `Scenario` per `Scenario:` / `Scenario Outline:` — `scenario_id`, `title`, `source_ref`, `tags`, `acceptance_criteria` (`{id, aspect}`) |

- **`metadata.source.project_id`** — `unset-project` until the `project-id` input is added.
- **`source_ref`** — `system: GitHub`; `native_id` is the file's path from its repository root;
  `native_type` is `scenario`; `url` is the file on the default branch; `tracker_state` is `committed`.

### Error handling

| Situation | Behaviour |
|---|---|
| A repository entry cannot be loaded (e.g. `organization-name` or `repository-name` is empty, not a string, or contains `/`) | Log error, skip the entry; counted in `sources_configured` and `sources_failed` |
| A path in `paths` does not exist or has no matching files | Log warning, skip path, continue |
| A file cannot be read | Log warning, skip file, continue |
| A malformed `@AC:` tag | `MALFORMED_AC` warning; the scenario is kept without that link |
| A file is outside a git checkout | `source_ref.url` is empty; `NO_SOURCE_URL` warning (only when the file yields a scenario) |
| A `scenario_id` is already collected from another file (e.g. one file reached through two repository entries) | The scenario is skipped; `AUTHORING_ERROR` warning with the file's `path` and the `scenario_id`; the first file read keeps it |
| The result fails contract validation, or the file cannot be written | Log error, no output file, `collect()` returns `False` |

`collect()` returns `True` whenever the artifact was written — an empty repository list or zero
matching files is a successful run with an empty `scenarios` list.
