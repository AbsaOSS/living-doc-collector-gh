# Documentation Source Mode

- [Mode De/Activation](#mode-deactivation)
- [Prerequisites](#prerequisites)
- [Usage](#usage)
- [Mode Inputs](#mode-inputs)
- [Header Formats](#header-formats)
- [Expected Output](#expected-output)

This mode mines **User Story**, **Functionality**, and **Feature** living documentation from
locally checked-out repositories and emits structured JSON.

- **User Stories** — parsed from `# ===` header blocks in `.feature` files tagged `@US_ID:US-NNN`.
- **Functionalities** — parsed from `# ===` header blocks in `.feature` files tagged `@FUNC_ID:FUNC-NNN`.
- **Features** — parsed from `/* === */` LIVING DOC header blocks in TypeScript page object files.

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
| `organization-name` | string   | yes      | GitHub org name (used in the output `id`). |
| `repository-name`   | string   | yes      | GitHub repo name (used in the output `id`). |
| `us-paths`          | string[] | yes*     | Absolute directory paths to scan for User Story `.feature` files. Accepts `"paths"` as a backward-compatible alias. |
| `func-paths`        | string[] | no       | Absolute directory paths to scan for Functionality `.feature` files. Omit to skip. |
| `pages-paths`       | string[] | no       | Absolute directory paths to scan for TypeScript page object files. Omit to skip. |

*At least one of `us-paths` / `paths` must be present; all other path fields are optional.

---
## Header Formats

### User Story (`.feature` file)

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
```

### Functionality (`.feature` file)

```gherkin
# =============================================================================
# LIVING DOC — FUNC-001 · Authentication Screen — Credential-based Login
# =============================================================================
# status:    active
# parent:    FEAT-001
# func_type: button_action
#
# acceptance_criteria:
#
#   AC:FUNC-001-01 (v1.0.0 - Active)
#     - Submitting valid credentials navigates to the dashboard.
# =============================================================================

@FUNC_ID:FUNC-001
Feature: Authentication Screen — Credential-based Login
```

### Feature (TypeScript page object `.ts` file)

```typescript
/* =============================================================================
 * LIVING DOC — FEAT-001 · Authentication Screen
 * =============================================================================
 * surface_type:          UI
 * route:                 /
 * owners:                Unify Team
 * status:                active
 * purpose:               Authentication screen where users enter credentials.
 * user_stories:          US-1
 * functionalities:       FUNC-001, FUNC-002, FUNC-003
 * external_dependencies: none
 * page-object:           LoginPage.ts
 * ============================================================================= */
```

### Parsed fields (canonical authoring format)

The parsers follow the canonical format defined in the Living Doc guide pages
(`living-doc-header-types.md` §1–§3, `living-doc-glossary.md` "Acceptance Criterion").

**Entity level** (User Story, Functionality, Feature):

| Field | Source | Output |
|---|---|---|
| `not_in_scope` | `# not_in_scope:` bullet section (sibling of `preconditions`; PageObject: `not_in_scope:` `;`-separated list) | `not_in_scope[]` |
| `deprecated_at` | `# deprecated_at:` header key (set when `status: deprecated`) | `deprecated_at` |
| `deprecation_reason` | `# deprecation_reason:` header key | `deprecation_reason` |

**Acceptance criterion level** (each `acceptance_criteria[]` record):

| Field | Source | Output |
|---|---|---|
| `state` | token after ` - ` in `(…)` — kept **verbatim**, including `deprecated`; deprecated/descoped ACs are **not** dropped | `state` |
| `aspect` | `- Aspect: <v1>, <v2>` line under the AC | `aspect[]` |
| `preconditions` | indented `preconditions:` sub-section under the AC — **extends** the entity list | `preconditions[]` |
| `not_in_scope` | indented `not_in_scope:` sub-section under the AC — **extends** the entity list | `not_in_scope[]` |
| `removal_planned` | third `(…)` segment `removal planned v<x>` on a deprecated AC | `removal_planned` |
| `descoped_at` / `descoped_reason` / `future_release` | `- descoped_at:` / `- descoped_reason:` / `- future_release:` bullets under the AC | same keys |

### Intentionally not mined

- **`tutorial*` / `tutorial_<group>` directories** — tutorial walkthroughs are not living
  documentation; `.feature` files under them are skipped at discovery time.
- **`# rationale:` (FUNC header) and `- Rationale:` (AC) lines** — free-text design context, not
  a structured contract field.
- **`superseded_by`, `owner_changed_at`, `owner_change_reason`** — entity-history metadata with no
  downstream consumer yet.
- **PageObject `wizard-steps`, `stub-reason`, cross-reference (`parent-feat`) headers** — surface
  operational detail, not part of the mined Feature contract.
- **Custom `{placeholder-name}:` AC keyword lines** (other than `Aspect:`) — kept inside the AC
  `description` prose rather than split into a field.

---
## Expected Output

The mode produces `output/doc-source/doc-source.json` with three top-level arrays:

```json
{
  "user_stories": [
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
      "not_in_scope":   [],
      "deprecated_at":  null,
      "deprecation_reason": null,
      "acceptance_criteria": [
        {
          "id": "US-27-01", "state": "Active", "version": "v1.9.0", "description": "...",
          "aspect": [], "preconditions": [], "not_in_scope": [],
          "removal_planned": null, "descoped_at": null, "descoped_reason": null, "future_release": null
        }
      ]
    }
  ],
  "functionalities": [
    {
      "id":        "absa-group/aul-ui/FUNC-001",
      "title":     "Authentication Screen — Credential-based Login",
      "state":     "active",
      "parent":    "FEAT-001",
      "func_type": "button_action",
      "acceptance_criteria": [
        { "id": "FUNC-001-01", "state": "Active", "version": "v1.0.0", "description": "..." }
      ]
    }
  ],
  "features": [
    {
      "id":                   "absa-group/aul-ui/FEAT-001",
      "title":                "Authentication Screen",
      "state":                "active",
      "surface_type":         "UI",
      "route":                "/",
      "owners":               "Unify Team",
      "purpose":              "Authentication screen where users enter credentials.",
      "user_stories":         ["US-1"],
      "functionalities":      ["FUNC-001", "FUNC-002", "FUNC-003"],
      "external_dependencies": "none",
      "page_object":          "LoginPage.ts"
    }
  ],
  "metadata": { ... },
  "warnings": []
}
```

- **`id` format**: `{organization-name}/{repository-name}/{US|FUNC|FEAT}-{id}`
- **`timestamps`**: always `null` for user stories — no GitHub Issue timestamp equivalent.
- **`tags`**: always `[]` for user stories — `.feature` tags do not map to issue labels.

---
## Schema

[`doc_source/schema/doc-source-v1.0.0-schema.json`](schema/doc-source-v1.0.0-schema.json) is
**generated** from the Pydantic models in [`doc_source/models.py`](models.py) — via
[`doc_source/schema_export.py`](schema_export.py) (`python -m doc_source.schema_export`) — not
hand-authored. Those models are this repo's source of truth for the `doc-source.json` contract;
the file-level `metadata` / `warnings` block is the shared definition in
[`common/models.py`](../common/models.py), the same one `doc-issues` and `ui-tests` use.

**If you change `doc_source/models.py`, regenerate the schema in the same change
(`python -m doc_source.schema_export`).** A test (`tests/common/test_schema_export.py`) fails if
the committed file drifts from the models.

A downstream consumer is the **schema consumer**: it vendors a pinned copy of this generated
schema for its own validation and consumes it independently (no direct code dependency),
mirroring the [Schema Sync Obligation](../doc_issues/README.md#schema-sync-obligation) documented
for `doc-issues`.

