# Documentation Source Mode

## Purpose

This page defines the mode that mines user stories, functionalities and features from source files: its
repository entry, what it discovers and writes, and how it reports problems.

Read before: [Action reference](../docs/action.md) · Next: [UI Tests mode](../ui_tests/README.md)

## Contents

- [Activation](#activation)
- [Usage](#usage)
- [Repository entry](#repository-entry)
- [Discovery](#discovery)
- [Output](#output)
- [Errors](#errors)
- [Formats](#formats)

## Activation

The mode mines living documentation from local checkouts and writes one `doc-source-v1.0.0` artifact.

- `doc-source: true` turns it on; `doc-source-repositories` lists its sources ([Inputs](../docs/action.md#inputs))
- **User Stories**: the living-doc header of each `.feature` file under `us-paths`
- **Functionalities**: the living-doc header of each `.feature` file under `func-paths`
- **Features**: the living-doc header comment of each TypeScript PageObject file under `pages-paths`
- The checkouts and the output directory need nothing beyond the action's own rules → [Prerequisites](../docs/action.md#prerequisites), [Output layout](../docs/action.md#output-layout)

## Usage

```yaml
- name: Living Documentation Collector for GitHub
  id: living_doc_collector_gh
  uses: AbsaOSS/living-doc-collector-gh@v0.2.0
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

## Repository entry

Each entry of `doc-source-repositories` is one source; a malformed entry fails the run at start.

| Field | Type | Required | Meaning |
|---|---|---|---|
| `organization-name` | string | yes | GitHub organization, used in `source_ref.url` and `metadata.source`; non-empty, no `/` |
| `repository-name` | string | yes | GitHub repository name, used in `source_ref.url` and `metadata.source`; non-empty, no `/` |
| `us-paths` | string[] | yes* | Absolute directory paths to scan for User Story `.feature` files; `paths` is accepted as a backward-compatible alias |
| `func-paths` | string[] | no | Absolute directory paths to scan for Functionality `.feature` files; omit to skip |
| `pages-paths` | string[] | no | Absolute directory paths to scan for TypeScript PageObject files; omit to skip |

- *At least one of `us-paths` or `paths` must be present; all other path fields are optional
- The two names are checked by one function for both modes

## Discovery

- Every configured path must exist; a missing one fails its whole source
- Within a path, discovery is recursive
- `.feature` files under a `tutorial*` or `tutorial_<group>` directory are skipped
- Every other `.feature` file found is parsed; one with no living-doc header is not emitted: `MISSING_ENTITY_ID`, counted in `entities_skipped`
- A `.ts` file under `pages-paths` with no `LIVING DOC` text anywhere is code, not documentation: skipped silently
  - The marker check scans the whole file, not just the header comment.
  - A body-string occurrence can enter parsing and produce a warning.
  - That includes a helper that opens with an eslint directive or a JSDoc block.
- A `LIVING DOC` banner placed after another `/* … */` comment is not read: the first block comment is taken as the header, so the Feature is not emitted (`MISSING_ENTITY_ID`, counted in `entities_skipped`)
  - Put the banner first; `//` line comments above it are fine.

## Output

- `<output-path>/doc-source/doc-source.json`, by default `output/collector-gh/doc-source/doc-source.json`
- A [`doc-source-v1.0.0`](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/contracts.md) artifact, written through `write_artifact`: validated before the write and written atomically

What this mode fills in the contract:

- **`metadata.source.project_id`**: the `project-id` input.
- **`metadata.stats.cardinality`**: `sources_configured` and `sources_failed` as in [Errors](../docs/action.md#errors); `entities_skipped` counts entities not emitted (no parseable entity id, an id already collected, or rejected by the contract); `unresolved_refs` counts `UNRESOLVED_RELATION` warnings.
- **`source_ref`**: `system: GitHub`; `native_id` is repository-root-relative inside Git and scan-root-relative outside Git; `native_type` is `feature-file` or `page-object`; `url` is the file's permalink at its checkout's commit, `<github-server-url>/<org>/<repo>/blob/<git rev-parse HEAD>/<native_id>`; `tracker_state` is `committed`
  - Outside a Git checkout, `url` is empty and `NO_SOURCE_URL` is emitted.
- **`tags`** and **`timestamps`**: always empty; a source file carries no labels and no created, updated or closed time.
- **`pages`**: a cross-reference PageObject header (`parent-feat:`) adds its page to its Feature

## Errors

The run-level codes and `allow-partial` are in the action reference → [Errors](../docs/action.md#errors). Within a source:

<!-- over limit: each behaviour cell is one rule with its count and its warning fields; splitting it would scatter the rule -->
| Situation | Behaviour |
|---|---|
| A configured path has no matching files | Log warning, continue |
| Nothing in the source is read as a header: no readable `.feature` file, and no `.ts` file with a header comment naming `LIVING DOC` | `EMPTY_SOURCE`; a header-less `.feature` file is a skipped entity, not an empty source |
| A file cannot be read | Log warning, skip the file, continue |
| A `.feature` file has no living-doc header, or a header has no parseable entity id | Not emitted; `MISSING_ENTITY_ID` with path and title; counted in `entities_skipped` |
| An entity id already collected from another file | The first file read keeps it; the later one is not emitted; `AUTHORING_ERROR` with path and `entity_id`; counted in `entities_skipped` |
| An entity the contract rejects (e.g. an AC id of another entity) | Not emitted; `AUTHORING_ERROR` with path, `entity_id` and the reason; counted in `entities_skipped`; statuses and relations are derived without it, so a reference to it is `UNRESOLVED_RELATION`; a rejected Feature takes its cross-reference pages with it |
| A cross-reference page whose Feature is not in the run | Dropped; `UNRESOLVED_RELATION` |
| Malformed header lines or acceptance criteria | A coded warning from the `authoring` parsers in `warnings[]` ([codes](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/contracts/errors.md)); the rest of the entity is kept |
| The result fails contract validation, or the file cannot be written | Log error; the mode fails, and with it the run, which writes no file |

- A warning about one file carries that file in its `path` field
- A warning with a `path` also carries that file's permalink in `source_url`, built as `source_ref.url` is
  - Unset wherever the file's `source_ref.url` would be empty.
- A status or relation warning of `derive_statuses` or `check_relations` carries the `entity_id` → utilities
  - `MISSING_STATUS` and `STATUS_AC_MISMATCH` also carry the entity's file in `path`.
- A dropped cross-reference page's `UNRESOLVED_RELATION` has no `entity_id`: it carries `path`, and its target in `context`

## Formats

- The `.feature` header and PageObject header formats, their keys and the acceptance-criterion grammar are defined once, in `living-doc` → [Authoring formats](https://github.com/AbsaOSS/living-doc/blob/master/docs/reference/authoring-formats.md), [Acceptance Criterion](https://github.com/AbsaOSS/living-doc/blob/master/docs/reference/glossary.md#acceptance-criterion-ac)
- This mode parses them with `living-doc-utilities`' `authoring` parsers → utilities
- It settles every entity's state with `derive_statuses` and checks relations with `check_relations`, once per run over all sources together
