# Documentation Source Mode

- [Mode De/Activation](#mode-deactivation)
- [Prerequisites](#prerequisites)
- [Usage](#usage)
- [Mode Inputs](#mode-inputs)
- [Feature File Header Format](#feature-file-header-format)
- [Expected Output](#expected-output)

This mode mines User Story living documentation from `.feature` file **header blocks** in locally
checked-out repositories and emits JSON in the same schema as the [Documentation Issues](../doc_issues/README.md)
mode (`doc-issues-v1.0.0-schema.json`).

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
2. **Output folder exists** — the output directory is prepared by the caller before this action runs.

---
## Usage

See the default minimal Documentation Source mode action step definition:

```yaml
- name: Living Documentation Collector for GitHub
  id: living_doc_collector_gh
  uses: AbsaOSS/living-doc-collector-gh@v0.1.0
  env:
    GITHUB-TOKEN: ${{ secrets.REPOSITORIES_ACCESS_TOKEN }}
  with:
    doc-source: true                       # documentation source mode de/activation
    doc-source-repositories: |
        [
          {
            "organization-name": "absa-group",
            "repository-name": "aul-ui",
            "local-path": "/path/to/checkout/aul-ui",
            "paths": ["playwright/features/liv_doc_us/**/*.feature"]
          }
        ]
```

---
## Mode Inputs

| Input Name                | Description                                                              | Required | Default | Usage |
|---------------------------|--------------------------------------------------------------------------|----------|---------|-------|
| `doc-source-repositories` | A JSON string defining the locally checked-out repositories to scan.     | No       | `'[]'`  | Provide a list of repositories with `organization-name`, `repository-name`, `local-path`, and `paths` (glob patterns relative to `local-path`). |

Each repository entry has the following fields:

| Field               | Type     | Required | Description |
|---------------------|----------|----------|-------------|
| `organization-name` | string   | yes      | GitHub org name (used in the output `id`). |
| `repository-name`   | string   | yes      | GitHub repo name (used in the output `id`). |
| `local-path`        | string   | yes      | Absolute or workspace-relative path to the checked-out repo root. |
| `paths`             | string[] | yes      | Glob patterns relative to `local-path`; resolved with `pathlib.Path.glob()`. |

---
## Feature File Header Format

The header block is a contiguous comment section delimited by `# ===...===` lines at the top of the
file. It must appear before the `@US_ID:` tag and `Feature:` keyword.

```gherkin
# =============================================================================
# LIVING DOC — US-27 · Request Access to Domain
# =============================================================================
# source:         https://github.com/org/repo/issues/3
# status:         active
# business_value:
#   - Enables data consumers to gain access to domains they need.
# preconditions:
#   - The user has logged in.
# acceptance_criteria:
#   AC:US-27-01 (v1.9.0 - Active)
#     - A user who is not the domain owner can open the Access tab.
# =============================================================================

@US_ID:US-27
Feature: Request Access to Domain
As a data consumer, I want to request access to a domain I do not own
so that I can be granted the permissions needed to use its data.
```

---
## Expected Output

The mode produces the file `output/doc-source/doc-source.json` using the
`doc-issues-v1.0.0-schema.json` schema. Each item has the form:

```json
{
  "id":          "absa-group/aul-ui/US-27",
  "title":       "Request Access to Domain",
  "state":       "active",
  "tags":        [],
  "url":         "https://github.com/org/repo/issues/3",
  "timestamps":  null,
  "description": "As a data consumer, I want to request access ...",
  "business_value": ["Enables data consumers to gain access to domains they need."],
  "preconditions":  ["The user has logged in."],
  "acceptance_criteria": [
    {
      "id":          "US-27-01",
      "state":       "Active",
      "version":     "v1.9.0",
      "description": "A user who is not the domain owner can open the Access tab."
    }
  ]
}
```

- **`id` format**: `{organization-name}/{repository-name}/US-{id}`
- **`timestamps`**: always `null` — local files have no GitHub Issue timestamp equivalent.
- **`tags`**: always `[]` — `.feature` file tags do not map to issue labels.
