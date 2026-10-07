# Documentation Source Mode

- [Mode De/Activation](#mode-deactivation)
- [Prerequisites](#prerequisites)
- [Usage](#usage)
- [Mode Inputs](#mode-inputs)
- [Output](#output)
- [Errors](#errors)
- [Formats](#formats)

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
   before invoking this action. This action never clones or fetches repository contents itself, and needs no
   token.
2. **No output folder to prepare** — the action creates `<output-path>/doc-source/` itself and replaces it on
   every run, so any previous content there is removed. Nothing else under `output-path` is touched.

---
## Usage

```yaml
- name: Living Documentation Collector for GitHub
  id: living_doc_collector_gh
  uses: AbsaOSS/living-doc-collector-gh@v0.1.0
  with:
    project-id: aul
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

The base inputs (`project-id`, `output-path`, `allow-partial`, `github-server-url`) are in the
[root README](../README.md#base-inputs).

---
## Mode Inputs

| Input Name                | Description                                                          | Required | Default |
|---------------------------|----------------------------------------------------------------------|----------|---------|
| `doc-source-repositories` | JSON array of repository scan configurations; each entry is one source. | No       | `'[]'`  |

Each repository entry:

| Field               | Type     | Required | Description |
|---------------------|----------|----------|-------------|
| `organization-name` | string   | yes      | GitHub org name (used in `source_ref.url` and `metadata.source`); non-empty, no `/`. |
| `repository-name`   | string   | yes      | GitHub repo name (used in `source_ref.url` and `metadata.source`); non-empty, no `/`. |
| `us-paths`          | string[] | yes*     | Absolute directory paths to scan for User Story `.feature` files. Accepts `"paths"` as a backward-compatible alias. |
| `func-paths`        | string[] | no       | Absolute directory paths to scan for Functionality `.feature` files. Omit to skip. |
| `pages-paths`       | string[] | no       | Absolute directory paths to scan for TypeScript PageObject files. Omit to skip. |

*At least one of `us-paths` / `paths` must be present; all other path fields are optional.

Every configured path must exist. Within one, discovery is recursive, and:

- `.feature` files under a `tutorial*` / `tutorial_<group>` directory are skipped.
- A `.ts` file under `pages-paths` that never names `LIVING DOC` in a header comment is code, not
  documentation, and is skipped silently — including a helper that opens with an eslint directive or a
  JSDoc block. A `LIVING DOC` banner placed after another comment is still parsed, and reported.

---
## Output

`<output-path>/doc-source/doc-source.json` (by default `output/collector-gh/doc-source/doc-source.json`), a
[`doc-source-v1.0.0`](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/contracts.md)
artifact written through `write_artifact`: validated before the write and written atomically.

What this mode fills in the contract:

- **`metadata.source.project_id`** — the `project-id` input.
- **`metadata.stats.cardinality`** — `sources_configured` and `sources_failed` as in the
  [root README](../README.md#errors); `entities_skipped` counts entities not emitted (no parseable entity id, an
  id already collected, or rejected by the contract); `unresolved_refs` counts `UNRESOLVED_RELATION` warnings.
- **`source_ref`** — `system: GitHub`; `native_id` is the file's path from its repository root;
  `native_type` is `feature-file` or `page-object`; `url` is the file's permalink at its checkout's commit,
  `<github-server-url>/<org>/<repo>/blob/<git rev-parse HEAD>/<native_id>`; `tracker_state` is `committed`.
- **`tags`** and **`timestamps`** — always empty: a source file carries no labels and no
  created/updated/closed time.
- **`pages`** — a cross-reference PageObject header (`parent-feat:`) adds its page to its Feature.

---
## Errors

The run-level codes (`INVALID_CONFIGURATION`, `SOURCE_UNAVAILABLE`, `EMPTY_SOURCE`, `NO_SOURCE_URL`) and
`allow-partial` are in the [root README](../README.md#errors). Within a source:

| Situation | Behaviour |
|---|---|
| A configured path has no matching files | Log warning, continue; a source with no entity header at all is `EMPTY_SOURCE` |
| A file cannot be read | Log warning, skip file, continue |
| A header has no parseable entity id | Not emitted; `MISSING_ENTITY_ID` with path and title; counted in `entities_skipped` |
| An entity id already collected from another file | The first file read keeps it; the later one is not emitted; `AUTHORING_ERROR` with path and `entity_id`; counted in `entities_skipped` |
| An entity the contract rejects (e.g. an AC id of another entity) | Not emitted; `AUTHORING_ERROR` with path, `entity_id` and the reason; counted in `entities_skipped`; statuses and relations are derived without it, so a reference to it is `UNRESOLVED_RELATION`; a rejected Feature takes its cross-reference pages with it |
| A cross-reference page whose Feature is not in the run | Dropped; `UNRESOLVED_RELATION` |
| Malformed header lines or acceptance criteria | Coded warning in `warnings[]`; the rest of the entity is kept |
| The result fails contract validation, or the file cannot be written | Log error; the mode fails, and with it the run, which writes no file |

A warning about one file carries its `path` in its `context`; a status or relation warning carries the
`entity_id`.

---
## Formats

The `.feature` header and PageObject header formats, their keys and the acceptance-criterion grammar are
defined once, in `living-doc`:

- [Living Doc Header Types](https://github.com/AbsaOSS/living-doc/blob/master/docs/guides/living-doc-header-types.md)
- [Living Doc Glossary](https://github.com/AbsaOSS/living-doc/blob/master/docs/guides/living-doc-glossary.md)

This mode parses them with `living-doc-utilities`' `authoring` parsers, then settles every entity's state
with `derive_statuses` and checks relations with `check_relations`, once per run over all sources together.
