# Living Documentation Collector for GitHub

[![Build and Test](https://github.com/AbsaOSS/living-doc-collector-gh/actions/workflows/test.yml/badge.svg)](https://github.com/AbsaOSS/living-doc-collector-gh/actions/workflows/test.yml)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

A GitHub Action that extracts living-documentation content from GitHub Projects, Issues, and locally checked-out repositories and emits machine-readable JSON for the downstream `living-doc-*` documentation generators.

## Overview

> **Expected usage: GitHub Actions first.** The supported way to run this action is as a step in a GitHub Actions workflow, chained with the other `living-doc-*` actions. Running it locally — the `run_script.sh` / `python3 main.py` pattern documented in `DEVELOPER.md` — is a development and debugging affordance only, not a second supported deployment target.

> **The Living Documentation pipeline runs AI-free.** Every step — collect → normalize → generate — is deterministic tooling (Python, JSON Schema validation, Jinja2/Markdown templates) with no LLM call anywhere in that path. [`AbsaOSS/agentic-toolkit`](https://github.com/AbsaOSS/agentic-toolkit) can accelerate the upstream *authoring* of GitHub Issues and `.feature` files, but it is never a runtime dependency of this pipeline: a human writing the same input by hand is a fully supported, identical path.

Addresses the need for continuously updated documentation accessible to all team members and stakeholders. Achieves this by extracting information directly from GitHub and providing it in a JSON format, which can be easily transformed into various documentation formats. This approach ensures that the documentation is always up-to-date and relevant, reducing the burden of manual updates and improving overall project transparency.

The Collector supports multiple mining modes, each with its own functionality. Activate only the modes you need; read more about each at its linked mode documentation.

| Mode | Purpose | Typical output |
|------|---------|----------------|
| **[Documentation Issues](doc_issues/README.md)** ![Status](https://img.shields.io/badge/status-in%20development-orange) | Data-mines GitHub repositories and Projects for documentation tickets that carry project documentation. | Issue / project living-documentation JSON |
| **[Documentation Source](doc_source/README.md)** ![Status](https://img.shields.io/badge/status-in%20development-orange) | Mines **User Story**, **Functionality**, and **Feature** blocks from locally checked-out repositories. | `doc-source` structured JSON |
| **[UI Tests](ui_tests/README.md)** ![Status](https://img.shields.io/badge/status-in%20development-orange) | Mines UI test scenarios from `.feature` scenario blocks in locally checked-out repositories. | UI test catalog JSON |

**Key features**
- 🔎 Multi-source: GitHub Projects and Issues plus locally checked-out repositories
- 🧩 Modular: activate only the mining modes you need (`doc-issues`, `doc-source`, `ui-tests`)
- 📄 Structured output: schema-versioned JSON ready for the downstream generators
- ⚡ Deterministic: the same inputs always produce the same JSON
- 🔁 Pipeline-ready: chains with the other `living-doc-*` actions

---
## Usage

### Prerequisites

Before we begin, ensure you have fulfilled the following prerequisites:
- GitHub Token with permission to fetch repository data such as Issues and Pull Requests.
- Python version 3.10 or higher.

### Adding the Action to Your Workflow

See the default action step definition:

```yaml
- name: Living Documentation Collector for GitHub
  id: living_doc_collector_gh
  uses: AbsaOSS/living-doc-collector-gh@v0.1.0
  env:
    GITHUB-TOKEN: ${{ secrets.REPOSITORIES_ACCESS_TOKEN }}  
  with:
    # modes de/activation
    doc-issues: false
    doc-source: false
    ui-tests: false
```

See the default action step definitions for each mode:

- [Documentation Issues mode default step definition](doc_issues/README.md#usage)
- [Documentation Source mode default step definition](doc_source/README.md#usage)
- [UI Tests mode default step definition](ui_tests/README.md#usage)

#### Full Example of Action Step Definition

See the full example of action step definition (in the example, non-default values are used):

```yaml
- name: Living Documentation Collector for GitHub
  id: living_doc_collector_gh
  uses: AbsaOSS/living-doc-collector-gh@v0.1.0
  env:
    GITHUB-TOKEN: ${{ secrets.REPOSITORIES_ACCESS_TOKEN }}  
  with:
    doc-issues: true                       # Documentation Issues mode de/activation
    verbose-logging: true                  # Optional: project verbose (debug) logging feature de/activation
    
    # 'Documentation Issues' mode required configuration
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
      
    # 'Documentation Issues' mode optional configuration
    doc-issues-project-state-mining: true     # project state mining feature de/activation
```

---
## Action Configuration

This section outlines the essential parameters that are common to all modes a user can define. Configure the action by customizing the following parameters based on your needs:

### Environment Variables

| Variable Name                | Description                                                                                                | Required | Usage                                                                                                                              |
|------------------------------|------------------------------------------------------------------------------------------------------------|----------|------------------------------------------------------------------------------------------------------------------------------------|
| `REPOSITORIES_ACCESS_TOKEN`  | GitHub access token for authentication, that has permission to access all defined repositories / projects. | Yes      | Store it in the GitHub repository secrets and reference it in the workflow file using  `${{ secrets.REPOSITORIES_ACCESS_TOKEN }}`. |
| `REQUESTS_CA_BUNDLE`         | Path to a custom CA bundle file for HTTPS certificate verification (e.g., corporate/proxy CA certificates). | No       | Set this when running in an environment with SSL interception. See [DEVELOPER.md](DEVELOPER.md#ssl--tls-certificate-verification) for details. |
- **Example**:
  ```yaml
  env:
    GITHUB-TOKEN: ${{ secrets.REPOSITORIES_ACCESS_TOKEN }}
  ```

The way how to generate and store a token into the GitHub repository secrets is described in the [support chapter](#how-to-create-a-token-with-required-scope).

### Inputs

#### Base Inputs

These inputs are common to all modes.

| Input Name        | Description                                        | Required | Default | Usage                     | 
|-------------------|----------------------------------------------------|----------|---------|---------------------------|
| `doc-issues`      | Enables or disables `Documentation Issues` mode. | No       | `false` | Set to true to activate.  |
| `doc-source`      | Enables or disables `Documentation Source` mode. | No       | `false` | Set to true to activate.  |
| `ui-tests`        | Enables or disables `UI Tests` mode.             | No       | `false` | Set to true to activate.  |
| `verbose-logging` | Enables or disables verbose (debug) logging.       | No       | `false` | Set to true to activate.  |


##### Example
```yaml
with:
  doc-issues: true          # Activation of Documentation Issues mode
  doc-source: true          # Activation of Documentation Source mode
  ui-tests: true            # Activation of UI Tests mode
  
  verbose-logging: true     # Activation of verbose (debug) logging
```

#### Mode Inputs

Mode-specific inputs and outputs are detailed in the respective mode's documentation:

- [Documentation Issues mode specific inputs](doc_issues/README.md#mode-inputs)
- [Documentation Source mode specific inputs](doc_source/README.md#mode-inputs)
- [UI Tests mode specific inputs](ui_tests/README.md#mode-inputs)
    
---
## Action Outputs

The action provides a main output path that allows users to locate and access the generated json files easily. 
This output can be utilized in various ways within your CI/CD pipeline to ensure the documentation is effectively distributed and accessible.

- `output-path`
  - **Description**: The root output path to the directory where all generated living documentation files are stored.
  - **Usage**: 
   ``` yaml
    - name: Living Documentation Collector for GitHub
      id: living_doc_collector_gh
      ... rest of the action definition ...
      
    - name: Output Documentation Path
      run: echo "GitHub Collector root output path: ${{ steps.living_doc_collector_gh.outputs.output-path }}"            
    ```

> Each mode generates its output files, which is stored in the `output-path` directory with clear naming conventions.

---

## Developer Guide

For local setup, the Makefile quality gate, testing, coverage, running the action locally, versioning, and releasing, see [DEVELOPER.md](DEVELOPER.md).

---
## How-to

This section aims to help the user walk through different processes, such as:
- [Generating and storing a token as a secret](#how-to-create-a-token-with-required-scope)

### How to Create a Token with Required Scope

1. Go to your GitHub account settings.
2. Click on the `Developer settings` tab in the left sidebar.
3. In the left sidebar, click on `Personal access tokens` and choose `Tokens (classic)`.
4. Click on the `Generate new token` button and choose `Generate new token (classic)`.
5. Optional - Add a note detailing what the token is for and choose the token expiration date.
6. Select ONLY bold scope options below:
   - **workflow**
   - write:packages
     - **read:packages**
   - admin:org
     - **read:org**
     - **manage_runners:org**
   - admin:public_key
     - **read:public_key**
   - admin:repo_hook
     - **read:repo_hook**
   - admin:enterprise
     - **manage_runners:enterprise**
     - **read:enterprise**
   - audit_log
     - **read:audit_log**
   - project
     - **read:project**
7. Copy the token value somewhere safe, because you won't be able to view it again.
8. Authorize the new token for the organization you want to fetch from.

### How to Store Token as a Secret

1. Go to the GitHub repository, from which you want to run the GitHub Action.
2. Click on the `Settings` tab in the top bar.
3. In the left sidebar, click on `Secrets and variables` > `Actions`.
4. Click on the `New repository secret` button.
5. Name the token `REPOSITORIES_ACCESS_TOKEN` and paste the token value.

---
## Contribution Guidelines

We welcome contributions to the Living Documentation Collector — bug fixes, documentation improvements, and new features. See [CONTRIBUTING.md](CONTRIBUTING.md) for the bug-report, feature-request, branch-naming, and PR conventions.

### License Information

This project is licensed under the Apache License 2.0. It is a liberal license that allows you great freedom in using, modifying, and distributing this software, while also providing an express grant of patent rights from contributors to users.

For more details, see the [LICENSE](LICENSE) file in the repository.

### Contact or Support Information

If you need help with using or contributing to the Living Documentation Collector Action, or if you have any questions or feedback, don't hesitate to reach out:

- **Issue Tracker**: For technical issues, questions, or feature requests, use the [GitHub Issues page](https://github.com/AbsaOSS/living-doc-collector-gh/issues).

Maintained by [ABSA Group Limited](https://github.com/AbsaOSS).
