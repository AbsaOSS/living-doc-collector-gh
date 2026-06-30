# Specification: `doc-source` and `ui-tests` Modes

## Status
Draft — 2026-06-30

---

## 1. Overview

Two new collector modes are added alongside the existing `doc-issues` mode.

| Mode | Source | Output schema |
|---|---|---|
| `doc-issues` | GitHub Issues via GH API | `doc-issues-v1.0.0-schema.json` (existing) |
| `doc-source` | `.feature` file header blocks on local disk | `doc-issues-v1.0.0-schema.json` (reused) |
| `ui-tests` | `.feature` file scenario blocks on local disk | `ui-tests-v1.0.0-schema.json` (new) |

The modes `tests` and `test-headers` are **removed** — no replacement.

---

## 2. Prerequisites

Both new modes assume:

1. **Checkout before action** — the caller performs `actions/checkout` for every target repository
   before invoking this action. This action never clones or fetches repository contents itself.
2. **Output folder exists** — the output directory is prepared by the caller before this action
   runs. This action writes files into the configured output path but does not create the root
   output directory.

---

## 3. Mode: `doc-source`

### 3.1 Purpose

Mine User Story living documentation from `.feature` file **header blocks** in locally checked-out
repositories and emit JSON in the same schema as `doc-issues`.

### 3.2 `action.yml` inputs

```yaml
doc-source:
  description: 'Enable or disable `Documentation Source` mode.'
  required: true

doc-source-repositories:
  description: >
    JSON string defining the repositories to scan for doc-source mode.
    Each entry must point to a locally checked-out repository.
  required: false
  default: '[]'
```

### 3.3 Environment variables

Set by `action.yml` prepare step:

```
INPUT_DOC_SOURCE=true|false
INPUT_DOC_SOURCE_REPOSITORIES=<JSON string>
```

### 3.4 `doc-source-repositories` JSON schema

```json
[
  {
    "organization-name": "absa-group",
    "repository-name":   "aul-ui",
    "local-path":        "/path/to/checkout/aul-ui",
    "paths":             ["playwright/features/liv_doc_us/**/*.feature"]
  }
]
```

| Field | Type | Required | Description |
|---|---|---|---|
| `organization-name` | string | yes | GitHub org name (used in output `id`) |
| `repository-name` | string | yes | GitHub repo name (used in output `id`) |
| `local-path` | string | yes | Absolute or workspace-relative path to the checked-out repo root |
| `paths` | string[] | yes | Glob patterns relative to `local-path`; resolved with `pathlib.Path.glob()` |

### 3.5 Feature file header format

The header block is a contiguous comment section delimited by `# ===...===` lines at the top
of the file. It must appear before the `@US_ID:` tag and `Feature:` keyword.

```gherkin
# =============================================================================
# LIVING DOC — US-27 · Request Access to Domain
# =============================================================================
# source:         https://github.com/org/repo/issues/3
# status:         active
# business_value:
#   - Enables data consumers to gain access to domains they need.
#   - Provides a governed, auditable access-request workflow.
# preconditions:
#   - The user has logged in.
#   - At least one domain exists that the user does not own.
#
# acceptance_criteria:
#
#   AC:US-27-01 (v1.9.0 - Active)
#     - A user who is not the domain owner can open the Access tab
#       and see a "Request access" button.
#
#   AC:US-27-02 (v1.9.0 - Active)
#     - After submitting an access request, the user receives confirmation.
# =============================================================================

@US_ID:US-27
Feature: Request Access to Domain
As a data consumer, I want to request access to a domain I do not own
so that I can be granted the permissions needed to use its data.
```

### 3.6 Parsing rules

#### 3.6.1 Header block boundaries

- Start: first line matching `^# =+$`
- End: last line matching `^# =+$` before the first `@` or `Feature:` line
- Lines within the block have the leading `# ` prefix stripped before processing

#### 3.6.2 US ID and title

Source line: `LIVING DOC — US-{id} · {title}`

- `id`: integer after `US-`
- `title`: text after ` · ` (trim whitespace)

The `@US_ID:US-{id}` tag on the file must match. If they differ, log a warning and use the
header value.

#### 3.6.3 `source` → `url`

```
source:         https://...
```

Value is the URL string. If the field is absent, `url` is `null`.

#### 3.6.4 `status` → `state`

```
status:         active
```

Value is taken as-is (lowercase string). If absent, `state` is `null`.

#### 3.6.5 `business_value` → `business_value[]`

```
business_value:
  - First bullet.
  - Second bullet.
```

Each `- ` line is one entry. Multi-line continuations (lines without `- ` prefix) are
appended to the previous entry with a single space.

#### 3.6.6 `preconditions` → `preconditions[]`

Same parsing rules as `business_value`.

#### 3.6.7 `acceptance_criteria` → `acceptance_criteria[]`

Each AC block:
```
  AC:US-27-01 (v1.9.0 - Active)
    - Description line one
      continuation of description.
    - Second sentence.
```

- **`id`**: `US-27-01` — the part after `AC:`
- **`version`**: `v1.9.0` — first token inside `(…)`
- **`state`**: `Active` — token after ` - ` inside `(…)`
- **`description`**: all `- ` lines and their continuations, joined with a single space,
  leading `- ` stripped. Multiple `- ` items within one AC are joined with a space
  (they form one prose description, not a sub-list).

If an AC block cannot be parsed, log a warning and skip it.

#### 3.6.8 `description` from `Feature:` narrative

Lines after `Feature: {title}` up to the first blank line or first `Scenario`/`Background`
keyword form the User Story narrative (`As a … I want … so that …`). These are joined with
a single space.

### 3.7 Output item schema

Reuses `doc-issues-v1.0.0-schema.json`.

```json
{
  "id":          "absa-group/aul-ui/US-27",
  "title":       "Request Access to Domain",
  "state":       "active",
  "tags":        [],
  "url":         "https://github.com/org/repo/issues/3",
  "timestamps":  null,
  "description": "As a data consumer, I want to request access to a domain I do not own so that I can be granted the permissions needed to use its data.",
  "business_value": [
    "Enables data consumers to gain access to domains they need.",
    "Provides a governed, auditable access-request workflow."
  ],
  "preconditions": [
    "The user has logged in.",
    "At least one domain exists that the user does not own."
  ],
  "acceptance_criteria": [
    {
      "id":          "US-27-01",
      "state":       "Active",
      "version":     "v1.9.0",
      "description": "A user who is not the domain owner can open the Access tab and see a \"Request access\" button."
    },
    {
      "id":          "US-27-02",
      "state":       "Active",
      "version":     "v1.9.0",
      "description": "After submitting an access request, the user receives confirmation."
    }
  ]
}
```

**`id` format:** `{organization-name}/{repository-name}/US-{id}`

**`timestamps`:** always `null` — local files have no GH Issue timestamp equivalent.

**`tags`:** always `[]` — the `@US_ID:` and domain tags on `.feature` files do not map to
issue labels. No tag extraction for this mode.

### 3.8 Output path

```
{OUTPUT_PATH}/doc-source/doc-source.json
```

### 3.9 Error handling

| Situation | Behaviour |
|---|---|
| `local-path` does not exist on disk | Log error, skip repository, continue |
| No files match a `paths` glob pattern | Log warning, skip pattern, continue |
| Header block missing from file | Log warning, skip file, continue |
| Required header field missing (US ID, title) | Log warning, skip file, continue |
| Optional header field missing | Set output field to `null` / `[]` |
| AC block malformed | Log warning, skip AC, include item without that AC |
| `@US_ID` tag mismatches header ID | Log warning, use header ID |
| Output file write fails | Log error, return `False` from `collect()` |

The collector returns `True` if all repositories were processed without fatal errors.
It returns `False` only if the output file cannot be written.

---

## 4. Mode: `ui-tests`

### 4.1 Purpose

Mine UI test scenarios from `.feature` file **scenario blocks** in locally checked-out
repositories and emit a test catalog JSON.

### 4.2 `action.yml` inputs

```yaml
ui-tests:
  description: 'Enable or disable `UI Tests` mode.'
  required: true

ui-tests-repositories:
  description: >
    JSON string defining the repositories to scan for ui-tests mode.
    Each entry must point to a locally checked-out repository.
  required: false
  default: '[]'
```

### 4.3 Environment variables

```
INPUT_UI_TESTS=true|false
INPUT_UI_TESTS_REPOSITORIES=<JSON string>
```

### 4.4 `ui-tests-repositories` JSON schema

Same shape as `doc-source-repositories`:

```json
[
  {
    "organization-name": "absa-group",
    "repository-name":   "aul-ui",
    "local-path":        "/path/to/checkout/aul-ui",
    "paths":             ["playwright/features/liv_doc_us/**/*.feature"]
  }
]
```

### 4.5 Feature file scenario format

```gherkin
@US_ID:US-26
@domain_create
Feature: Create Domain
    As a user, I want to create domain
    so that I can make it available for data consumers.

    # AC:US-26-01 (v1.4.2 - Active) — description comment (ignored)
    @AC:US-26-01
    @Regression
    Scenario: User can complete the Create Domain wizard and create a new domain
        Given the user "1" is logged in
        And the user is on the Create Domain wizard About screen
        When the user fills in the domain name "<unique>"
        Then the user is on the Create Domain wizard Owner screen
```

### 4.6 Parsing rules

#### 4.6.1 File-level tags

Tags on lines immediately before `Feature:` — these are **file-level tags**:
- `@US_ID:US-{id}` → `us_id` for all scenarios in this file
- Any other `@tag` → ignored at file level (not propagated to scenarios)

A file without `@US_ID:` is processed but each scenario's `us_id` is `null`.

#### 4.6.2 Scenario block extraction

A scenario block starts on a `Scenario:` or `Scenario Outline:` line and ends at the next
`Scenario:`, `Scenario Outline:`, `@` tag block (before next scenario), `Rule:`, or EOF.

`Background:` blocks are **not** extracted as scenarios.

Comment lines (`# …`) within a scenario block are **ignored**.

#### 4.6.3 Scenario tags

Tag lines (`@…`) immediately before a `Scenario:` / `Scenario Outline:` line belong to that
scenario.

- `@AC:US-26-01` → extracted into `ac_ids[]` (the `AC:` prefix is stripped: value is `US-26-01`)
- `@Regression`, `@Smoke`, or any other `@tag` → extracted into `tags[]`
- `@US_ID:` on a scenario-level tag block is invalid — log a warning and ignore it

A scenario may have **zero or more** `@AC:` tags → `ac_ids` is always an array.

#### 4.6.4 Scenario type

- `Scenario:` → `"scenario_type": "Scenario"`
- `Scenario Outline:` → `"scenario_type": "Scenario Outline"`

#### 4.6.5 Step extraction

Lines starting with `Given`, `When`, `Then`, `And`, `But` (case-sensitive, followed by a space)
are steps.

Each step:
- `keyword`: the leading word (`Given`, `When`, `Then`, `And`, `But`)
- `text`: remainder of the line, trimmed

Docstring (`"""`) and DataTable (`|`) blocks attached to a step are **not** extracted in v1.

#### 4.6.6 Scenario ID

```
{organization-name}/{repository-name}/{relative-file-path}/{scenario-name-slug}
```

`scenario-name-slug` rules:
- Lowercase
- Spaces → hyphens
- Remove characters not in `[a-z0-9\-]`
- Truncate to 80 characters
- **Collision guard within the same file**: if a slug is already used, append `-2`, `-3`, etc.

Example:
```
absa-group/aul-ui/playwright/features/liv_doc_us/domain_create.feature/user-can-complete-the-create-domain-wizard-and-create-a-new-domain
```

`relative-file-path` is the path from `local-path` to the file, using `/` separators.

### 4.7 Output item schema (new: `ui-tests-v1.0.0`)

```json
{
  "items": [
    {
      "id":            "absa-group/aul-ui/playwright/features/liv_doc_us/domain_create.feature/user-can-complete-the-create-domain-wizard-and-create-a-new-domain",
      "us_id":         "US-26",
      "ac_ids":        ["US-26-01"],
      "scenario_name": "User can complete the Create Domain wizard and create a new domain",
      "scenario_type": "Scenario",
      "tags":          ["Regression"],
      "steps": [
        { "keyword": "Given", "text": "the user \"1\" is logged in" },
        { "keyword": "And",   "text": "the user is on the Create Domain wizard About screen" },
        { "keyword": "When",  "text": "the user fills in the domain name \"<unique>\"" },
        { "keyword": "Then",  "text": "the user is on the Create Domain wizard Owner screen" }
      ],
      "source": {
        "org":  "absa-group",
        "repo": "aul-ui",
        "file": "playwright/features/liv_doc_us/domain_create.feature"
      }
    }
  ]
}
```

### 4.8 Output path

```
{OUTPUT_PATH}/ui-tests/ui-tests.json
```

### 4.9 Error handling

| Situation | Behaviour |
|---|---|
| `local-path` does not exist | Log error, skip repository, continue |
| No files match glob | Log warning, skip pattern, continue |
| File has no `@US_ID:` tag | Log warning, set `us_id: null` for all its scenarios |
| Scenario has no `@AC:` tag | `ac_ids: []` — valid, no warning |
| Step keyword unrecognised | Skip line silently |
| Scenario slug collision | Append `-2`, `-3`, log debug |
| Output file write fails | Log error, return `False` from `collect()` |

---

## 5. Shared infrastructure

### 5.1 File discovery utility

New module: `utils/feature_file_discovery.py`

```python
def discover_feature_files(local_path: str, patterns: list[str]) -> list[Path]:
    """
    Resolve glob patterns under local_path and return matching .feature file paths.
    Returns empty list if local_path does not exist (caller logs the error).
    """
```

Used by both `doc_source` and `ui_tests` collectors.

### 5.2 `ConfigRepository` for source modes

Both `doc_source` and `ui_tests` define their own `ConfigRepository` model under their
respective `model/` packages. They do **not** share the `doc_issues` version because the
field set differs (`local-path`, `paths` instead of `projects-title-filter`).

Fields loaded from JSON:

| JSON key | Property |
|---|---|
| `organization-name` | `organization_name` |
| `repository-name` | `repository_name` |
| `local-path` | `local_path` |
| `paths` | `paths` |

---

## 6. Code structure

```
doc_source/
    __init__.py
    collector.py          # GHDocSourceCollector(output_path).collect() -> bool
    header_parser.py      # parse_header(lines: list[str]) -> dict  (pure function)
    model/
        __init__.py
        config_repository.py   # org, repo, local_path, paths

ui_tests/
    __init__.py
    collector.py          # GHUITestsCollector(output_path).collect() -> bool
    scenario_parser.py    # parse_scenarios(lines: list[str], org, repo, rel_path) -> list[dict]
    model/
        __init__.py
        config_repository.py   # org, repo, local_path, paths
    schema/
        ui-tests-v1.0.0-schema.json

utils/
    feature_file_discovery.py   # discover_feature_files() — new
    ... (existing files unchanged)
```

Both `header_parser.py` and `scenario_parser.py` are **pure functions** — they take raw
lines as input and return structured dicts. No file I/O, no logging setup, no env access.
This keeps them unit-testable without mocks.

---

## 7. `utils/constants.py` changes

```python
# Collector regimes
class Mode(Enum):
    DOC_ISSUES = "DOC_ISSUES"
    DOC_SOURCE = "DOC_SOURCE"    # new
    UI_TESTS   = "UI_TESTS"     # new

# Source mode Action inputs
DOC_SOURCE_REPOSITORIES = "DOC_SOURCE_REPOSITORIES"
UI_TESTS_REPOSITORIES   = "UI_TESTS_REPOSITORIES"

# Regime output sub-paths (new)
DOC_SOURCE_OUTPUT_PATH = "doc-source"
UI_TESTS_OUTPUT_PATH   = "ui-tests"
```

Modes `TESTS` and `TEST_HEADERS` are **removed** from the enum.

---

## 8. `action_inputs.py` additions

```python
@staticmethod
def is_doc_source_mode_enabled() -> bool:
    return get_action_input(Mode.DOC_SOURCE.value, "false").lower() == "true"

@staticmethod
def get_doc_source_repositories() -> list[dict]:
    return json.loads(get_action_input(DOC_SOURCE_REPOSITORIES, "[]"))

@staticmethod
def is_ui_tests_mode_enabled() -> bool:
    return get_action_input(Mode.UI_TESTS.value, "false").lower() == "true"

@staticmethod
def get_ui_tests_repositories() -> list[dict]:
    return json.loads(get_action_input(UI_TESTS_REPOSITORIES, "[]"))
```

Validation in `validate_user_configuration()`:
- If `doc-source=true` and `doc-source-repositories` is empty → log warning (not fatal; zero repos → zero output items)
- If `ui-tests=true` and `ui-tests-repositories` is empty → log warning (same)

---

## 9. `action.yml` changes

### 9.1 New inputs

```yaml
  doc-source:
    description: 'Enable or disable `Documentation Source` mode.'
    required: true

  doc-source-repositories:
    description: 'JSON string defining the repositories for doc-source mode.'
    required: false
    default: '[]'

  ui-tests:
    description: 'Enable or disable `UI Tests` mode.'
    required: true

  ui-tests-repositories:
    description: 'JSON string defining the repositories for ui-tests mode.'
    required: false
    default: '[]'
```

### 9.2 Prepare step additions

```bash
echo "INPUT_DOC_SOURCE=${{ inputs.doc-source }}" >> $GITHUB_ENV
echo "INPUT_UI_TESTS=${{ inputs.ui-tests }}" >> $GITHUB_ENV

if [[ "${{ inputs.doc-source }}" == "true" ]]; then
  echo "INPUT_DOC_SOURCE_REPOSITORIES=$(echo '${{ inputs.doc-source-repositories }}' | jq -c .)" >> $GITHUB_ENV
fi

if [[ "${{ inputs.ui-tests }}" == "true" ]]; then
  echo "INPUT_UI_TESTS_REPOSITORIES=$(echo '${{ inputs.ui-tests-repositories }}' | jq -c .)" >> $GITHUB_ENV
fi
```

### 9.3 Run step additions

```yaml
INPUT_DOC_SOURCE:               ${{ env.INPUT_DOC_SOURCE }}
INPUT_UI_TESTS:                 ${{ env.INPUT_UI_TESTS }}
INPUT_DOC_SOURCE_REPOSITORIES:  ${{ env.INPUT_DOC_SOURCE_REPOSITORIES }}
INPUT_UI_TESTS_REPOSITORIES:    ${{ env.INPUT_UI_TESTS_REPOSITORIES }}
```

---

## 10. `main.py` additions

```python
from doc_source.collector import GHDocSourceCollector
from ui_tests.collector import GHUITestsCollector

# inside run():
if ActionInputs.is_doc_source_mode_enabled():
    logger.info("Liv-Doc collector for GitHub - Starting the `doc-source` mode.")
    if GHDocSourceCollector(output_path).collect():
        logger.info("Liv-Doc collector for GitHub - `doc-source` mode completed successfully.")
    else:
        logger.info("Liv-Doc collector for GitHub - `doc-source` mode failed.")
        all_modes_success = False
else:
    logger.info("Liv-Doc collector for GitHub - `doc-source` mode disabled.")

if ActionInputs.is_ui_tests_mode_enabled():
    logger.info("Liv-Doc collector for GitHub - Starting the `ui-tests` mode.")
    if GHUITestsCollector(output_path).collect():
        logger.info("Liv-Doc collector for GitHub - `ui-tests` mode completed successfully.")
    else:
        logger.info("Liv-Doc collector for GitHub - `ui-tests` mode failed.")
        all_modes_success = False
else:
    logger.info("Liv-Doc collector for GitHub - `ui-tests` mode disabled.")
```

---

## 11. Testing requirements

### 11.1 `doc_source`

| Test | Covers |
|---|---|
| `test_header_parser.py::test_full_header` | All fields present and correctly parsed |
| `test_header_parser.py::test_missing_optional_fields` | `url`, `status`, `business_value`, `preconditions` absent → `null`/`[]` |
| `test_header_parser.py::test_missing_required_fields` | No US ID / no title → returns `None` |
| `test_header_parser.py::test_multi_line_ac_description` | AC description spanning multiple `-` lines |
| `test_header_parser.py::test_malformed_ac_block` | Malformed AC → skipped, rest of ACs returned |
| `test_collector.py::test_collect_single_repo` | One repo, two files → two output items |
| `test_collector.py::test_collect_local_path_missing` | Repo skipped, collector returns `True` |
| `test_collector.py::test_collect_no_matching_files` | Zero files → empty items array, returns `True` |
| `test_config_repository.py` | Load valid / invalid JSON |

### 11.2 `ui_tests`

| Test | Covers |
|---|---|
| `test_scenario_parser.py::test_single_scenario` | One scenario, all fields extracted |
| `test_scenario_parser.py::test_multiple_ac_tags` | `ac_ids` with two `@AC:` tags |
| `test_scenario_parser.py::test_scenario_outline` | `scenario_type` is `"Scenario Outline"` |
| `test_scenario_parser.py::test_no_us_id` | `us_id` is `null` |
| `test_scenario_parser.py::test_no_ac_tags` | `ac_ids` is `[]` |
| `test_scenario_parser.py::test_slug_collision` | Duplicate scenario names → `-2` suffix |
| `test_scenario_parser.py::test_background_ignored` | `Background:` block not in output |
| `test_collector.py::test_collect_single_repo` | One file, two scenarios → two output items |
| `test_collector.py::test_collect_local_path_missing` | Repo skipped, returns `True` |
| `test_config_repository.py` | Load valid / invalid JSON |

### 11.3 `utils/feature_file_discovery.py`

| Test | Covers |
|---|---|
| `test_discovery.py::test_matching_glob` | Returns expected file list |
| `test_discovery.py::test_no_match` | Returns `[]` |
| `test_discovery.py::test_missing_local_path` | Returns `[]` |

### 11.4 Coverage gate
All new modules must meet the project-wide 80% coverage threshold.
