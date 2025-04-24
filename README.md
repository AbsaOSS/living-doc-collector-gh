# Living Documentation Collector for GitHub

- [Motivation](#motivation)
- [Mining Modes](#mining-modes)
- [Usage](#usage)
    - [Prerequisites](#prerequisites)
    - [Adding the Action to Your Workflow](#adding-the-action-to-your-workflow)
- [Action Configuration](#action-configuration)
    - [Environment Variables](#environment-variables)
    - [Inputs](#inputs)
      - [Base Inputs](#base-inputs)
      - [Mode Inputs](#mode-inputs)
- [Action Outputs](#action-outputs)
- [How-to](#how-to)
  - [How to Create a Token with Required Scope](#how-to-create-a-token-with-required-scope)
  - [How to Store Token as a Secret](#how-to-store-token-as-a-secret)
- [Contribution Guidelines](#contribution-guidelines)
  - [License Information](#license-information)
  - [Contact or Support Information](#contact-or-support-information)

## Motivation

Addresses the need for continuously updated documentation accessible to all team members and stakeholders. Achieves this by extracting information directly from GitHub and providing it in a json format, which can be easily transformed into various documentation formats. This approach ensures that the documentation is always up-to-date and relevant, reducing the burden of manual updates and improving overall project transparency.

---
## Mining Modes

This Collector  supports multiple mining modes, each with its own unique functionality. Read more about the modes at their respective links:
- [Documentation Issues](doc_issues/README.md) ![Status](https://img.shields.io/badge/status-in%20development-orange)
- [Tests](tests/README.md) ![Status](https://img.shields.io/badge/status-todo-lightgrey)
- [Test Headers](test_headers/README.md) ![Status](https://img.shields.io/badge/status-todo-lightgrey)
- [Code Tags](code_tags/README.md) ![Status](https://img.shields.io/badge/status-todo-lightgrey)
- [Release Notes](release_notes/README.md) ![Status](https://img.shields.io/badge/status-todo-lightgrey)
- [Workflows](workflows/README.md) ![Status](https://img.shields.io/badge/status-todo-lightgrey)
- [User Guide](user_guide/README.md) ![Status](https://img.shields.io/badge/status-todo-lightgrey)

---
## Usage

### Prerequisites

Before we begin, ensure you have a following prerequisites:
- GitHub Token with permission to fetch repository data such as Issues and Pull Requests,
- Python version 3.12 or higher.

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
    tests: false
    test-headers: false
    code-tags: false
    release-notes: false
    workflows: false
    user-guide: false
```

See the default action step definitions for each mode:

- [Documentation Issues mode default step definition](doc_issues/README.md#adding-doc-issues-mode-to-the-workflow)
- [Tests mode default step definition](tests/README.md#adding-tests-mode-to-the-workflow)
- [Test Headers mode default step definition](test_headers/README.md#adding-test-headers-mode-to-the-workflow)
- [Code Tags mode default step definition](code_tags/README.md#adding-code-tags-mode-to-the-workflow)
- [Release Notes mode default step definition](release_notes/README.md#adding-release-notes-mode-to-the-workflow)
- [Workflows mode default step definition](workflows/README.md#adding-workflows-mode-to-the-workflow)
- [User Guide mode default step definition](user_guide/README.md#adding-user-guide-mode-to-the-workflow)

#### Full Example of Action Step Definition

See the full example of action step definition (in example are used non-default values):

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
| `tests`           | Enables or disables `Tests` mode.                | No       | `false` | Set to true to activate.  |
| `test-headers`    | Enables or disables `Test headers` mode.         | No       | `false` | Set to true to activate.  |
| `code-tags`       | Enables or disables `Code tags` mode.            | No       | `false` | Set to true to activate.  |
| `release-notes`   | Enables or disables `Release Notes` mode.        | No       | `false` | Set to true to activate.  |
| `workflows`       | Enables or disables `Workflows` mode.            | No       | `false` | Set to true to activate.  |
| `user-guide`      | Enables or disables `User guide` mode.           | No       | `false` | Set to true to activate.  |
| `verbose-logging` | Enables or disables verbose (debug) logging.       | No       | `false` | Set to true to activate.  |


##### Example
```yaml
with:
  doc-issues: true          # Activation of Documentation Issues mode
  test-headers: true        # Activation of Test Headers mode
  
  verbose-logging: true     # Activation of verbose (debug) logging
```

#### Mode Inputs

Mode-specific inputs and outputs are detailed in the respective mode's documentation:

- [Documentation Issues mode specific inputs](doc_issues/README.md#mode-configuration)
- [Tests mode specific inputs](tests/README.md#mode-configuration)
- [Test Headers mode specific inputs](test_headers/README.md#mode-configuration)
- [Code Tags mode specific inputs](code_tags/README.md#mode-configuration)
- [Release Notes mode specific inputs](release_notes/README.md#mode-configuration)
- [Workflows mode specific inputs](workflows/README.md#mode-configuration)
- [User Guide mode specific inputs](user_guide/README.md#mode-configuration)
    
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

> Each mode generates its own output files, which are stored in the `output-path` directory with clear naming conventions.

---

## Developer Guide

See this [Developer Guide](DEVELOPER.md) for more technical a development related information.

---
## How-to

This section aims to help the user walk through different processes, such as:
- [Generating and storing a token as a secret](#how-to-create-a-token-with-required-scope)

### How to Create a Token with Required Scope

1. Go to your GitHub account settings.
2. Click on the `Developer settings` tab in the left sidebar.
3. In the left sidebar, click on `Personal access tokens` and choose `Tokens (classic)`.
4. Click on the `Generate new token` button and choose `Generate new token (classic)`.
5. Optional - Add a note, what is token for and choose token expiration.
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
7. Copy the token value somewhere, because you won't be able to see it again.
8. Authorize new token to organization you want to fetch from.

### How to Store Token as a Secret

1. Go to the GitHub repository, from which you want to run the GitHub Action.
2. Click on the `Settings` tab in the top bar.
3. In the left sidebar, click on `Secrets and variables` > `Actions`.
4. Click on the `New repository secret` button.
5. Name the token `REPOSITORIES_ACCESS_TOKEN` and paste the token value.

---
## Contribution Guidelines

We welcome contributions to the Living Documentation Generator! Whether you're fixing bugs, improving documentation, or proposing new features, your help is appreciated.

#### How to Contribute

Before contributing, please review our [contribution guidelines](https://github.com/AbsaOSS/living-doc-collector-gh/blob/master/CONTRIBUTING.md) for more detailed information.

### License Information

This project is licensed under the Apache License 2.0. It is a liberal license that allows you great freedom in using, modifying, and distributing this software, while also providing an express grant of patent rights from contributors to users.

For more details, see the [LICENSE](https://github.com/AbsaOSS/living-doc-collector-gh/blob/master/LICENSE) file in the repository.

### Contact or Support Information

If you need help with using or contributing to Living Documentation Generator Action, or if you have any questions or feedback, don't hesitate to reach out:

- **Issue Tracker**: For technical issues or feature requests, use the [GitHub Issues page](https://github.com/AbsaOSS/living-doc-collector-gh/issues).
- **Discussion Forum**: For general questions and discussions, join our [GitHub Discussions forum](https://github.com/AbsaOSS/living-doc-collector-gh/discussions).
