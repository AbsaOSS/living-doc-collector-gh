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

The output JSON contains two top-level sections:
1. **metadata**: File-level provenance and audit information
2. **issues**: Dictionary of enriched issue objects

### File-Level Metadata

The `metadata` section provides traceability and provenance information:

```json
{
  "metadata": {
    "generated_at": "2025-01-21T14:30:00.000Z",
    "schema_version": "1.0",
    "generator": {
      "name": "AbsaOSS/living-doc-collector-gh",
      "version": "v1.0.0"
    },
    "source": {
      "repositories": ["owner/repo"]
    },
    "run": {
      "workflow": "Documentation Collector",
      "run_id": "12345",
      "run_attempt": "1",
      "actor": "github-user",
      "ref": "refs/heads/main",
      "sha": "abc123"
    },
    "inputs": {
      "project_state_mining_enabled": true
    }
  },
  "issues": { ... }
}
```

**Metadata Fields:**
- `generated_at`: UTC timestamp when the file was generated (ISO-8601 format)
- `schema_version`: Schema version (e.g., "1.0") for compatibility checking by downstream consumers
- `generator`: Information about the action that generated the file
  - `name`: Action repository identifier
  - `version`: Action version, git reference, or commit SHA
- `source`: Source repository information
  - `repositories`: List of repositories included in the collection
- `run`: GitHub Actions workflow run information (when available)
  - `workflow`: Workflow name
  - `run_id`: Unique run identifier
  - `run_attempt`: Run attempt number
  - `actor`: User who triggered the workflow
  - `ref`: Git reference (branch/tag)
  - `sha`: Commit SHA
- `inputs`: Non-sensitive action inputs that affect output
  - `project_state_mining_enabled`: Whether project state mining was enabled

### Output Schema Validation

The collector provides a formal JSON Schema file (`doc_issues/output_schema.json`) that describes the complete structure of the output JSON. Downstream consumers (such as the living-doc-toolkit adapter) can use this schema to:
- Validate collector output programmatically
- Understand the complete data contract
- Detect schema version compatibility

The schema defines all required and optional fields, data types, and validation rules for both metadata and issue structures.

### Issue-Level Structure

Each issue in the `issues` dictionary contains base fields plus audit enrichment:

```json
{
  "owner/repo#123": {
    "type": "FeatureIssue",
    "repository_id": "owner/repo",
    "title": "Feature Title",
    "issue_number": 123,
    "state": "open",
    "created_at": "2025-01-15T10:00:00",
    "updated_at": "2025-01-20T15:30:00",
    "closed_at": null,
    "html_url": "https://github.com/owner/repo/issues/123",
    "body": "Issue description...",
    "labels": ["DocumentedFeature", "enhancement"],
    "linked_to_project": true,
    "project_status": [
      {
        "project_title": "Project Name",
        "status": "In Progress",
        "priority": "High",
        "size": "Medium",
        "moscow": "Must Have"
      }
    ],
    "created_by": "user1",
    "closed_by": null,
    "comments_count": 5,
    "last_commented_at": "2025-01-20T12:00:00",
    "last_commented_by": "user2",
    "audit_events": [
      {
        "action": "labeled",
        "timestamp": "2025-01-15T10:05:00",
        "actor": "user1",
        "label": "enhancement"
      },
      {
        "action": "assigned",
        "timestamp": "2025-01-15T10:10:00",
        "actor": "user1",
        "assignee": "developer1"
      },
      {
        "action": "milestoned",
        "timestamp": "2025-01-16T09:00:00",
        "actor": "user1",
        "milestone": "v1.0"
      }
    ]
  }
}
```

### Base Issue Fields

These fields are always present (if available in GitHub):
- `type`: Issue type (FeatureIssue, UserStoryIssue, FunctionalityIssue, or Issue)
- `repository_id`: Repository identifier (owner/repo)
- `title`: Issue title
- `issue_number`: Issue number
- `state`: Issue state (open, closed)
- `created_at`: Timestamp when issue was created
- `updated_at`: Timestamp when issue was last updated
- `closed_at`: Timestamp when issue was closed (null if open)
- `html_url`: GitHub web URL for the issue
- `body`: Issue description/body
- `labels`: Array of label names
- `linked_to_project`: Whether issue is linked to a GitHub Project
- `project_status`: Array of project status information (when linked to projects)

### Audit Enrichment Fields

These fields provide audit trail and traceability metadata:

#### Always Available (from GitHub Issue API):
- `created_by`: GitHub login of the user who created the issue
- `closed_by`: GitHub login of the user who closed the issue (null if not closed or unavailable)
- `comments_count`: Total number of comments on the issue

#### Available When Comments Exist:
- `last_commented_at`: Timestamp of the most recent comment
- `last_commented_by`: GitHub login of the user who posted the most recent comment

#### Timeline Events (requires timeline API access):
- `audit_events`: Array of audit-relevant timeline events

**Supported Event Types:**
- `labeled` / `unlabeled`: Label additions/removals
  - Includes: `action`, `timestamp`, `actor`, `label`
- `assigned` / `unassigned`: Assignee changes
  - Includes: `action`, `timestamp`, `actor`, `assignee`
- `milestoned` / `demilestoned`: Milestone changes
  - Includes: `action`, `timestamp`, `actor`, `milestone`
- `reopened` / `closed`: State transitions
  - Includes: `action`, `timestamp`, `actor`

### Graceful Degradation

The collector handles API limitations gracefully:
- If timeline events are unavailable (e.g., due to permissions), the `audit_events` field will be omitted or empty
- If comment details cannot be fetched, `last_commented_at` and `last_commented_by` will be omitted
- The collector logs debug/warning messages when data cannot be retrieved, but continues processing
- Base issue fields are always preserved even if audit enrichment fails

### Access Requirements

- **Base fields**: Available with standard repository read access
- **Comments summary**: Requires issue read access (standard)
- **Timeline events**: May require additional permissions depending on repository settings
  - If timeline access is denied, the collector continues without these events

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
