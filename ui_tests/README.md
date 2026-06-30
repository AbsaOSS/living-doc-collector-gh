# UI Tests Mode

- [Mode De/Activation](#mode-deactivation)
- [Prerequisites](#prerequisites)
- [Usage](#usage)
- [Mode Inputs](#mode-inputs)
- [Feature File Scenario Format](#feature-file-scenario-format)
- [Expected Output](#expected-output)

This mode mines UI test scenarios from `.feature` file **scenario blocks** in locally checked-out
repositories and emits a test catalog JSON (`ui-tests-v1.0.0-schema.json`).

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
2. **Output folder exists** — the output directory is prepared by the caller before this action runs.

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
            "local-path": "/path/to/checkout/aul-ui",
            "paths": ["playwright/features/liv_doc_us/**/*.feature"]
          }
        ]
```

---
## Mode Inputs

| Input Name              | Description                                                            | Required | Default | Usage |
|-------------------------|------------------------------------------------------------------------|----------|---------|-------|
| `ui-tests-repositories` | A JSON string defining the locally checked-out repositories to scan.   | No       | `'[]'`  | Provide a list of repositories with `organization-name`, `repository-name`, `local-path`, and `paths` (glob patterns relative to `local-path`). |

Each repository entry uses the same shape as the [Documentation Source](../doc_source/README.md#mode-inputs) mode.

---
## Feature File Scenario Format

```gherkin
@US_ID:US-26
@domain_create
Feature: Create Domain
    As a user, I want to create domain.

    @AC:US-26-01
    @Regression
    Scenario: User can complete the Create Domain wizard and create a new domain
        Given the user "1" is logged in
        And the user is on the Create Domain wizard About screen
        When the user fills in the domain name "<unique>"
        Then the user is on the Create Domain wizard Owner screen
```

- File-level `@US_ID:US-{id}` applies `us_id` to all scenarios in the file.
- Scenario-level `@AC:US-26-01` tags populate `ac_ids` (the `AC:` prefix is stripped).
- Any other scenario-level `@tag` populates `tags`.
- `Background:` blocks are not extracted.

---
## Expected Output

The mode produces the file `output/ui-tests/ui-tests.json` using the
`ui-tests-v1.0.0-schema.json` schema. Each item has the form:

```json
{
  "id":            "absa-group/aul-ui/playwright/features/.../domain_create.feature/user-can-...",
  "us_id":         "US-26",
  "ac_ids":        ["US-26-01"],
  "scenario_name": "User can complete the Create Domain wizard and create a new domain",
  "scenario_type": "Scenario",
  "tags":          ["Regression"],
  "steps": [
    { "keyword": "Given", "text": "the user \"1\" is logged in" },
    { "keyword": "And",   "text": "the user is on the Create Domain wizard About screen" }
  ],
  "source": {
    "org":  "absa-group",
    "repo": "aul-ui",
    "file": "playwright/features/liv_doc_us/domain_create.feature"
  }
}
```

- **`id` format**: `{organization-name}/{repository-name}/{relative-file-path}/{scenario-name-slug}`
- **`us_id`**: `null` when the file has no `@US_ID:` tag.
- **`ac_ids`**: always an array; empty when the scenario has no `@AC:` tags.
