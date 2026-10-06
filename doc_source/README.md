# Documentation Source Mode

- [Mode De/Activation](#mode-deactivation)
- [Prerequisites](#prerequisites)
- [Usage](#usage)
- [Mode Inputs](#mode-inputs)
- [Authoring Formats](#authoring-formats)
- [Expected Output](#expected-output)

This mode mines **User Story**, **Functionality** and **Feature** living documentation from
locally checked-out repositories and writes one `doc-source-v1.0.0` artifact.

- **User Stories** — the living-doc header of each `.feature` file under `us-paths`.
- **Functionalities** — the living-doc header of each `.feature` file under `func-paths`.
- **Features** — the living-doc header comment of each TypeScript PageObject file under `pages-paths`.

## Mode De/Activation

- **doc-source**
  - **Description**: Enables or disables the Documentation Source mode.
  - **Usage**: Set to `true` to activate.
  - **Example**:
    ```yaml
    with:
      doc-source: true
    ```

---
## Prerequisites

1. **Checkout before action** — the caller performs `actions/checkout` for every target repository
   before invoking this action. This action never clones or fetches repository contents itself.
2. **No output folder to prepare** — the action creates the mode's `doc-source/` output directory itself and
   replaces it on every run, so any previous content there is removed.

---
## Usage

```yaml
- name: Living Documentation Collector for GitHub
  id: living_doc_collector_gh
  uses: AbsaOSS/living-doc-collector-gh@v0.1.0
  env:
    GITHUB-TOKEN: ${{ secrets.REPOSITORIES_ACCESS_TOKEN }}
  with:
    doc-source: true
    doc-source-repositories: |
        [
          {
            "organization-name": "absa-group",
            "repository-name": "aul-ui",
            "us-paths":    ["/path/to/checkout/aul-ui/playwright/features/liv_doc_us"],
            "func-paths":  ["/path/to/checkout/aul-ui/playwright/features/liv_doc_func"],
            "pages-paths": ["/path/to/checkout/aul-ui/playwright/pages"]
          }
        ]
```

---
## Mode Inputs

| Input Name                | Description                                                          | Required | Default |
|---------------------------|----------------------------------------------------------------------|----------|---------|
| `doc-source-repositories` | JSON list of repository scan configurations.                         | No       | `'[]'`  |

Each repository entry:

| Field               | Type     | Required | Description |
|---------------------|----------|----------|-------------|
| `organization-name` | string   | yes      | GitHub org name (used in `source_ref.url` and `metadata.source`). |
| `repository-name`   | string   | yes      | GitHub repo name (used in `source_ref.url` and `metadata.source`). |
| `us-paths`          | string[] | yes*     | Absolute directory paths to scan for User Story `.feature` files. Accepts `"paths"` as a backward-compatible alias. |
| `func-paths`        | string[] | no       | Absolute directory paths to scan for Functionality `.feature` files. Omit to skip. |
| `pages-paths`       | string[] | no       | Absolute directory paths to scan for TypeScript PageObject files. Omit to skip. |

*At least one of `us-paths` / `paths` must be present; all other path fields are optional.

---
## Authoring Formats

The `.feature` header and PageObject header formats, their keys and the acceptance-criterion grammar are
defined once, in `living-doc`:

- [Living Doc Header Types](https://github.com/AbsaOSS/living-doc/blob/master/docs/guides/living-doc-header-types.md)
- [Living Doc Glossary](https://github.com/AbsaOSS/living-doc/blob/master/docs/guides/living-doc-glossary.md)

This mode parses them with `living-doc-utilities`' `authoring` parsers (`feature_header`, `page_object`,
`identity`), then settles every entity's state with `derive_statuses` and checks relations with
`check_relations`, once per run over all User Stories, Functionalities and Features together.

What this mode adds around the parsers:

- `.feature` files under a `tutorial*` / `tutorial_<group>` directory are skipped at discovery time.
- A `.ts` file under `pages-paths` that never names `LIVING DOC` in a header comment is code, not
  documentation, and is skipped silently — including a helper that opens with an eslint directive or a
  JSDoc block. A `LIVING DOC` banner placed after another comment is still parsed, and reported.
- A cross-reference PageObject header (`parent-feat:`) adds its page to its Feature's `pages`; one whose
  Feature is not in the run is reported `UNRESOLVED_RELATION` and dropped.

---
## Expected Output

The mode writes `output/doc-source/doc-source.json`, a
[`doc-source-v1.0.0`](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/contracts.md)
artifact, through `write_artifact`: the result is validated before the write and written atomically.

| Key | Content |
|---|---|
| `schema_version` | `doc-source-v1.0.0` |
| `metadata` | the standard envelope — `producer`, `run` (GitHub Actions context), `source`, `generated_at`, `stats` |
| `warnings[]` | every parser, status and relation warning of the run; a warning about one file carries its `path` in its `context`, and a status or relation warning carries the `entity_id` |
| `user_stories[]`, `features[]`, `functionalities[]` | one contract `Entity` per parsed file |

- **`metadata.source.project_id`** — `unset-project` until the `project-id` input is added.
- **`metadata.stats`** — computed by `write_artifact`; `entities_skipped` counts entities not emitted (no
  parseable entity id, an id already collected, or rejected by the contract), `unresolved_refs` counts
  `UNRESOLVED_RELATION` warnings.
- **`source_ref`** — `system: GitHub`; `native_id` is the file's path from its repository root;
  `native_type` is `feature-file` or `page-object`; `url` is the file on the default branch
  (`https://github.com/<org>/<repo>/blob/HEAD/<path>`); `tracker_state` is `committed`.
- **`tags`** and **`timestamps`** — always empty: a source file carries no labels and no
  created/updated/closed time.

### Error handling

| Situation | Behaviour |
|---|---|
| A repository entry cannot be loaded (e.g. `organization-name` or `repository-name` is empty, not a string, or contains `/`) | Log error, skip the entry; counted in `sources_configured` and `sources_failed` |
| A configured path does not exist or has no matching files | Log warning, skip path, continue |
| A file cannot be read | Log warning, skip file, continue |
| A header has no parseable entity id | Not emitted; `MISSING_ENTITY_ID` with path and title; counted in `entities_skipped` |
| An entity id already collected from another file | The first file read keeps it; the later one is not emitted; `AUTHORING_ERROR` with path and `entity_id`; counted in `entities_skipped` |
| An entity the contract rejects (e.g. an AC id of another entity) | Not emitted; `AUTHORING_ERROR` with path, `entity_id` and the reason; counted in `entities_skipped`; statuses and relations are derived without it, so a reference to it is `UNRESOLVED_RELATION`; a rejected Feature takes its cross-reference pages with it |
| A file is outside a git checkout | `source_ref.url` is empty; `NO_SOURCE_URL` warning |
| Malformed header lines or acceptance criteria | Coded warning in `warnings[]`; the rest of the entity is kept |
| The result fails contract validation, or the file cannot be written | Log error, no output file, `collect()` returns `False` |

`collect()` returns `True` whenever the artifact was written — an empty repository list or zero
matching files is a successful run with empty lists.
