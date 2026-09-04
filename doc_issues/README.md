# Living Documentation Issues Mode

- [Mode De/Activation](#mode-deactivation)
- [Usage](#usage)
- [Mode Inputs](#mode-inputs)
- [Expected Output](#expected-output)
- [Documentation Ticket Introduction](#documentation-ticket-introduction)
  - [Labels](#labels)
  - [Hosting Documentation Tickets in a Solo Repository](#hosting-documentation-tickets-in-a-solo-repository)
- [Living Documentation Issues Mode Features](#living-documentation-issues-mode-features)
  - [Issues Data Mining from GitHub Repositories](#issues-data-mining-from-github-repositories)
  - [Issues Data Mining from GitHub Projects](#issues-data-mining-from-github-projects)

This mode is designed to data-mine GitHub repositories for [documentation tickets](#documentation-ticket-introduction) containing project documentation.

## Mode De/Activation

- **doc-issues**
  - **Description**: Enables or disables the Living Documentation Issues mode.
  - **Usage**: Set to true to activate.
  - **Example**:
    ```yaml
    with:
      doc-issues: true
    ```
    
## GitHub Repository Structure Requirements

- Is recommended to use only one dedicated repository for documentation tickets (GitHub issues with supported labels).
- User Story **can** point to multiple Features
- Feature **can** point to multiple Functionalities
- Functionality **should** point to one Feature
  - Why one only?
    - To avoid confusion and ensure clarity in the documentation.
    - Functionality implements a specific aspect of a feature, and linking it to multiple features can create ambiguity.

---

## Usage

See the default minimal Living Documentation Issues mode action step definition:

```yaml
- name: Living Documentation Collect for Github
  id: living_doc_collector_gh
  uses: AbsaOSS/living-doc-collector-gh@v0.1.0
  env:
    GITHUB-TOKEN: ${{ secrets.REPOSITORIES_ACCESS_TOKEN }}  
  with:
    doc-issues: true                   # living documentation issues mode de/activation  
    doc-issues-repositories: |
        [
          {
            "organization-name": "fin-services",
            "repository-name": "investment-app"
          }
        ]
```

See the full example of the Living Documentation Issues mode step definition (in the example, non-default values are used):

```yaml
- name: Living Documentation Collector for GitHub
  id: living_doc_collector_gh
  uses: AbsaOSS/living-doc-collector-gh@v0.1.0
  env:
    GITHUB-TOKEN: ${{ secrets.REPOSITORIES_ACCESS_TOKEN }}  
  with:
    doc-issues: true                       # living documentation issues mode de/activation
    verbose-logging: true                  # project verbose (debug) logging feature de/activation

    doc-issues-repositories: |
        [
          {
            "organization-name": "your-organization-name",
            "repository-name": "your-project-living-documentation",
            "projects-title-filter": []
          },
          {
            "organization-name": "your-organization-name",
            "repository-name": "your-another-project-living-documentation",
            "projects-title-filter": ["Management Overview"]
          }
        ]
    doc-issues-project-state-mining: true     # project state mining feature de/activation
```

---
## Mode Inputs

Configure the Living Documentation mode by customizing the following parameters:

| Input Name                        | Description | Required | Default | Usage |
|-----------------------------------|-------------|----------|---------|-------|
| `doc-issues-repositories`         | A JSON string defining the repositories to be included in the documentation generation.                                                                                                    | No       | `'[]'`    | Provide a list of repositories, including the organization name, repository name, and any attached projects you wish to filter in.<br><br> The `projects-title-filter` include parameter is optional. Only issues linked to the specified projects will be fetched. To fetch all issues (all projects), either omit this parameter or leave the list empty. |
| `doc-issues-project-state-mining` | Enables or disables the mining of project state data from [GitHub Projects](https://docs.github.com/en/issues/planning-and-tracking-with-projects/learning-about-projects/about-projects). | No       | `false` ` | Set to true to activate.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |

- **Example**

  ```yaml
  with:
    doc-issues-repositories: |
      [
        {
          "organization-name": "your-organization-name",
          "repository-name": "your-project-living-documentation",
        },
        {
          "organization-name": "your-organization-name",
          "repository-name": "your-another-project-living-documentation",
          "projects-title-filter": ["Management Overview"]
        }
      ]
  
      doc-issues-project-state-mining: true 
  ```

---
## Expected Output

The Living Documentation Collector for GitHub is designed to produce a collection of Consolidated Issues. Where **consolidated** means that the issues' information is merged from both the Repository and Project Issues. 

The mode produces the file `output/doc-issues/doc-issues.json` with the following structure:

### JSON Structure

The output JSON contains three top-level sections:
1. **user_stories**: Array of enriched issue items — despite the name, every collected `FeatureIssue` / `FunctionalityIssue` / `UserStoryIssue` / plain `Issue` ends up here (see [Issue-Level Structure](#issue-level-structure))
2. **metadata**: File-level provenance information
3. **warnings**: Compatibility warnings for downstream consumers (currently always empty; reserved for schema/version compatibility signalling)

### File-Level Metadata

The `metadata` section provides traceability and provenance information:

```json
{
  "user_stories": [ ... ],
  "metadata": {
    "producer": {
      "name": "AbsaOSS/living-doc-collector-gh",
      "version": "0.1.1",
      "build": "12345"
    },
    "run": {
      "run_id": "12345",
      "run_attempt": "1",
      "actor": "github-user",
      "workflow": "Documentation Collector",
      "ref": "refs/heads/main",
      "sha": "abc123"
    },
    "source": {
      "systems": ["GitHub"],
      "repositories": ["owner/repo"],
      "organization": "owner",
      "enterprise": null
    },
    "original_metadata": {
      "generated_at": "2025-01-21T14:30:00.000000+00:00",
      "schema_version": "1.0.0",
      "inputs": {
        "project_state_mining_enabled": true
      }
    }
  },
  "warnings": []
}
```

**Metadata Fields:**
- `producer`: Information about the action that generated the file
  - `name`: Action repository identifier
  - `version`: Package version of the running action
  - `build`: CI/CD build identifier (`GITHUB_RUN_ID`), `null` outside a GitHub Actions run
- `run`: GitHub Actions workflow run information (all fields `null` outside a GitHub Actions run)
  - `run_id` / `run_attempt`: Workflow run identifier / attempt number
  - `actor`: User who triggered the workflow
  - `workflow`: Workflow name
  - `ref`: Git reference (branch/tag)
  - `sha`: Commit SHA
- `source`: Source repository information
  - `systems`: Source systems mined (currently always `["GitHub"]`)
  - `repositories`: List of repositories included in the collection
  - `organization`: Organization of the first configured repository, `null` if none configured
  - `enterprise`: Not currently captured, always `null`
- `original_metadata`: Collector-specific metadata not part of the shared adapter contract
  - `generated_at`: UTC timestamp when the file was generated (ISO-8601 format)
  - `schema_version`: Schema version (`"1.0.0"`) for compatibility checking by downstream consumers
  - `inputs`: Non-sensitive action inputs that affect output
    - `project_state_mining_enabled`: Whether project state mining was enabled

### Output Schema Validation

The collector provides a formal JSON Schema file (`doc_issues/schema/doc-issues-v1.0.0-schema.json`) that describes the complete structure of the output JSON. Downstream consumers (such as the living-doc-toolkit adapter) can use this schema to:
- Validate collector output programmatically
- Understand the complete data contract
- Detect schema version compatibility

The schema is versioned as **v1.0.0** (reflected in both the filename and the `$schema_version` field in the schema itself). The schema defines all required and optional fields, data types, and validation rules for metadata, items (issues), and warnings.

### Schema Sync Obligation

`collector-gh` is both the **schema producer** and the **data producer** for this contract. [`doc_issues/schema/doc-issues-v1.0.0-schema.json`](schema/doc-issues-v1.0.0-schema.json) is generated from the Pydantic models in [`doc_issues/models.py`](models.py) — via [`doc_issues/schema_export.py`](schema_export.py) (`python -m doc_issues.schema_export`) — not hand-authored; those models are this repo's source of truth for the contract. `living-doc-toolkit` is the **schema consumer** and **data consumer**: it vendors a pinned copy of this schema in its `collector_gh` adapter and consumes it independently (no direct code dependency).

**If you change `doc_issues/models.py`, regenerate the schema in the same change (`python -m doc_issues.schema_export`) and open a matching synchronization pull request in `living-doc-toolkit`.** The consumer-side procedure — updating the vendored schema, the adapter's own (consumer-side) Pydantic models, and `CONFIRMED_MIN`/`CONFIRMED_MAX` compatibility bounds — is documented in `living-doc-toolkit`'s [`packages/adapters/collector_gh/SCHEMA_SYNC.md`](https://github.com/AbsaOSS/living-doc-toolkit/blob/master/packages/adapters/collector_gh/SCHEMA_SYNC.md). Follow it whenever this schema changes.

### Issue-Level Structure

Each entry in the `user_stories` array is an enriched issue item. The array carries the
issue key on each item itself (`id`) — there is no dictionary keying by `owner/repo#number`
at the top level:

```json
{
  "id": "owner/repo#123",
  "title": "Feature Title",
  "state": "open",
  "tags": ["DocumentedFeature", "enhancement"],
  "url": "https://github.com/owner/repo/issues/123",
  "timestamps": {
    "created": "2025-01-15T10:00:00",
    "updated": "2025-01-20T15:30:00"
  },
  "description": "Narrative text from the issue's `## Description` section, or null.",
  "business_value": ["Bullet list from `### Business Value`, or null."],
  "preconditions": ["Bullet list from `## Preconditions`, or null."],
  "acceptance_criteria": [
    {
      "id": "AC1",
      "state": "Confirmed",
      "version": "1.0",
      "description": "Row from the `## Acceptance Criteria` table, or null."
    }
  ]
}
```

### Item Fields

- `id`: Issue key in `owner/repo#number` format
- `title`: Issue title
- `state`: Issue state (`open`, `closed`)
- `tags`: Array of label names
- `url`: GitHub web URL for the issue
- `timestamps.created` / `timestamps.updated`: Timestamps when the issue was created / last updated
- `description`: Narrative parsed from the issue body's `## Description` section (`null` if absent)
- `business_value`: Bullet list parsed from `### Business Value` (`null` if absent)
- `preconditions`: Bullet list parsed from `## Preconditions` (`null` if absent)
- `acceptance_criteria`: Table rows parsed from `## Acceptance Criteria` — each row has `id`, `state`, `version`, `description` (`null` if the section is absent)

The parsing rules for these four fields are implemented in `doc_issues/body_parser.py`; see
[Documentation Ticket Introduction](#documentation-ticket-introduction) for how to structure
an issue body so they can be extracted.

> **Note:** the collector also fetches per-issue audit data (creator, closer, comment count,
> timeline events) via `ConsolidatedIssue`, but this data is not currently included in the
> emitted `user_stories` item — only the fields listed above are written to
> `doc-issues.json`.

### Access Requirements

- Fetching issues requires standard repository read access.
- Fetching project status requires GitHub Projects read access, and only applies when `doc-issues-project-state-mining` is enabled.

The `output` folder is the root output directory for the action.

---
## Documentation Ticket Introduction

A **Documentation Ticket** is a small piece of documentation realized as a GitHub Issue dedicated to project documentation. Unlike development-focused tickets, a Documentation Ticket can remain in open state continuously, evolving as updates are needed, and can be reopened or revised indefinitely. They are not directly tied to Pull Requests (PRs) but can be referenced for context.

- **Content Rules**:
  - **Non-technical Focus:** 
    - Keep the documentation body free of technical solution specifics.
    - Technical insights should be accessible through linked PRs or Tickets within the development repository.
  - **Independent Documentation:** 
    - Ensure the content remains independent of implementation details to allow a clear, high-level view of the feature or user story's purpose and functionality.

### Labels

To enhance clarity, the following label groups define and categorize each Documentation Issue:
- **Type**:
  - **DocumentedUserStory:** Describes a user-centric functionality or process, highlighting its purpose and value.
    - Encompasses multiple features, capturing the broader goal from a user perspective.
  - **DocumentedFeature:** Details a specific feature, providing a breakdown of its components and intended outcomes.
    - Built from various requirements and can relate to multiple User Stories, offering an in-depth look at functionality.
  - **DocumentedRequirement:** Outlines individual requirements or enhancements tied to the feature or user story.
- **Issue States**:
  - **Upcoming:** The feature, story, or requirement is planned but not yet implemented.
  - **Implemented:** The feature or requirement has been completed and is in active use.
  - **Deprecated:** The feature or requirement has been phased out or replaced and is no longer supported.

**DocumentedUserStory** and **DocumentedFeature** serve as **Epics**, whereas **DocumentedRequirement** represents specific items similar to feature enhancements or individual requirements.

### Hosting Documentation Tickets in a Solo Repository

Using a dedicated repository solely for documentation tickets provides multiple advantages:
- **Streamlined Management:** This avoids cross-project conflicts, board exclusions and enables specialized templates solely for documentation purposes.- **Focused Access Control:** This allows a small team to manage and edit documentation without interference, maintaining high-quality content.
- **Optimized Data Mining:** Supports easier and more efficient data extraction for feedback and review cycles through Release Notes.
- **Implementation Reflection:** Mirrors elements from the implementation repositories, providing a high-level knowledge source that is valuable for both business and technical teams.
- **Release Notes Integration:** Documentation can evolve based on insights from release notes, serving as a dynamic feedback loop back to the documentation repository.

---

## Living Documentation Issues Mode Features

### Issues Data Mining from GitHub Repositories

This is a built-in feature, that allows you to define which repositories should be included in the living documentation issues mode process. This essential process cannot be deactivated inside of mode scope. By specifying repositories, you can focus on the most relevant projects for your documentation needs.

- **Activation**: This is a built-in feature, so it is always activated.
- **Default Behavior**: By default, the action will include all repositories defined in the repositories input parameter. Each repository is defined with its organization name, and repository name.

### Issues Data Mining from GitHub Projects

This feature allows you to define which projects should be included in the living documentation process. By specifying projects, you can focus on the most relevant projects for your documentation needs.

- **Activation**: To activate this feature, set the `doc-issues-project-state-mining` input to true.
- **Non-Activated Behavior**: By default, when the feature is inactive, the action will include all projects linked to the repositories. This information is provided by the GitHub API.
- **Activated Example**: Use available options to customize which projects are included in the documentation.
  - `doc-issues-project-state-mining: false` deactivates the mining of project state data from GitHub Projects. If set to **false**, project state data will not be included in the generated documentation and project related configuration options will be ignored. 
  - `projects-title-filter: []` filters the repository attached projects by titles, if list is empty all projects are used.
      ```json
        {
          "organization-name": "your-organization-name",
          "repository-name": "your-project-living-documentation",
          "projects-title-filter": ["Community Outreach Initiatives", "Health Data Analysis"]
        }
      ```
