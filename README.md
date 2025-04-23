# Living Documentation Collector for GitHub

- [Motivation](#motivation)
- [Mining Regimes](#mining-regimes)
- [Usage](#usage)
    - [Prerequisites](#prerequisites)
    - [Adding the Action to Your Workflow](#adding-the-action-to-your-workflow)
- [Action Configuration](#action-configuration)
    - [Environment Variables](#environment-variables)
    - [Inputs](#inputs)
      - [Base Inputs](#base-inputs)
      - [Regime Inputs](#regime-inputs)
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
## Mining Regimes

This Collector  supports multiple mining regimes, each with its own unique functionality. Read more about the regimes at their respective links:
- [Documentation Issues](doc_issues/README.md)
- [Tests](tests/README.md)
- [Test Headers](test_headers/README.md)
- [Code Tags](code_tags/README.md)
- [Release Notes](release_notes/README.md)
- [Workflows](workflows/README.md)
- [User Guide](user_guide/README.md)

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
    # regimes de/activation
    doc-issues: false
    tests: false
    test-headers: false
    code-tags: false
    release-notes: false
    workflows: false
    user-guide: false
```

See the default action step definitions for each regime:

- [Documentation Issues regime default step definition](doc_issues/README.md#adding-doc-issues-regime-to-the-workflow)
- [Tests regime default step definition](tests/README.md#adding-tests-regime-to-the-workflow)
- [Test Headers regime default step definition](test_headers/README.md#adding-test-headers-regime-to-the-workflow)
- [Code Tags regime default step definition](code_tags/README.md#adding-code-tags-regime-to-the-workflow)
- [Release Notes regime default step definition](release_notes/README.md#adding-release-notes-regime-to-the-workflow)
- [Workflows regime default step definition](workflows/README.md#adding-workflows-regime-to-the-workflow)
- [User Guide regime default step definition](user_guide/README.md#adding-user-guide-regime-to-the-workflow)

#### Full Example of Action Step Definition

See the full example of action step definition (in example are used non-default values):

```yaml
- name: Living Documentation Collector for GitHub
  id: living_doc_collector_gh
  uses: AbsaOSS/living-doc-collector-gh@v0.1.0
  env:
    GITHUB-TOKEN: ${{ secrets.REPOSITORIES_ACCESS_TOKEN }}  
  with:
    doc-issues: true                       # Documentation Issues regime de/activation
    verbose-logging: true                  # Optional: project verbose (debug) logging feature de/activation
    
    # 'Documentation Issues' regime required configuration
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
      
    # 'Documentation Issues' regime optional configuration
    doc-issues-project-state-mining: true     # project state mining feature de/activation
```

---
## Action Configuration

This section outlines the essential parameters that are common to all regimes a user can define. Configure the action by customizing the following parameters based on your needs:

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

These inputs are common to all regimes.

| Input Name        | Description                                        | Required | Default | Usage                     | 
|-------------------|----------------------------------------------------|----------|---------|---------------------------|
| `doc-issues`      | Enables or disables `Documentation Issues` regime. | No       | `false` | Set to true to activate.  |
| `tests`           | Enables or disables `Tests` regime.                | No       | `false` | Set to true to activate.  |
| `test-headers`    | Enables or disables `Test headers` regime.         | No       | `false` | Set to true to activate.  |
| `code-tags`       | Enables or disables `Code tags` regime.            | No       | `false` | Set to true to activate.  |
| `release-notes`   | Enables or disables `Release Notes` regime.        | No       | `false` | Set to true to activate.  |
| `workflows`       | Enables or disables `Workflows` regime.            | No       | `false` | Set to true to activate.  |
| `user-guide`      | Enables or disables `User guide` regime.           | No       | `false` | Set to true to activate.  |
| `verbose-logging` | Enables or disables verbose (debug) logging.       | No       | `false` | Set to true to activate.  |


##### Example
```yaml
with:
  doc-issues: true          # Activation of Documentation Issues regime
  test-headers: true        # Activation of Test Headers regime
  
  verbose-logging: true     # Activation of verbose (debug) logging
```

#### Regime Inputs

Regime-specific inputs and outputs are detailed in the respective regime's documentation:

- [Documentation Issues regime specific inputs](doc_issues/README.md#regime-configuration)
- [Tests regime specific inputs](tests/README.md#regime-configuration)
- [Test Headers regime specific inputs](test_headers/README.md#regime-configuration)
- [Code Tags regime specific inputs](code_tags/README.md#regime-configuration)
- [Release Notes regime specific inputs](release_notes/README.md#regime-configuration)
- [Workflows regime specific inputs](workflows/README.md#regime-configuration)
- [User Guide regime specific inputs](user_guide/README.md#regime-configuration)
    
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

> Each regime generates its own output files, which are stored in the `output-path` directory with clear naming conventions.

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
