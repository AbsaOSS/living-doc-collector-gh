# Living Documentation Collector for GitHub

[![Build and Test](https://github.com/AbsaOSS/living-doc-collector-gh/actions/workflows/test.yml/badge.svg)](https://github.com/AbsaOSS/living-doc-collector-gh/actions/workflows/test.yml)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

A GitHub Action that extracts living-documentation content from locally checked-out repositories and emits machine-readable JSON, in the contracts `living-doc-utilities` owns, for the downstream `living-doc-*` tools.

## Overview

> **Expected usage: GitHub Actions first.** The supported way to run this action is as a step in a GitHub Actions workflow, chained with the other `living-doc-*` actions. Running it locally — the `run_script.sh` / `python3 main.py` pattern documented in `DEVELOPER.md` — is a development and debugging affordance only, not a second supported deployment target.

> **The Living Documentation pipeline runs AI-free.** Every step — collect → normalize → generate — is deterministic tooling (Python, JSON Schema validation, Jinja2/Markdown templates) with no LLM call anywhere in that path. [`AbsaOSS/agentic-toolkit`](https://github.com/AbsaOSS/agentic-toolkit) can accelerate the upstream *authoring* of GitHub Issues and `.feature` files, but it is never a runtime dependency of this pipeline: a human writing the same input by hand is a fully supported, identical path.

Addresses the need for continuously updated documentation accessible to all team members and stakeholders. Achieves this by extracting information directly from GitHub and providing it in a JSON format, which can be easily transformed into various documentation formats. This approach ensures that the documentation is always up-to-date and relevant, reducing the burden of manual updates and improving overall project transparency.

The Collector supports multiple mining modes, each with its own functionality. Activate only the modes you need; read more about each at its linked mode documentation.

| Mode | Purpose | Typical output |
|------|---------|----------------|
| **[Documentation Source](doc_source/README.md)** ![Status](https://img.shields.io/badge/status-in%20development-orange) | Mines **User Story**, **Functionality**, and **Feature** blocks from locally checked-out repositories. | `doc-source-v1.0.0` |
| **[UI Tests](ui_tests/README.md)** ![Status](https://img.shields.io/badge/status-in%20development-orange) | Mines UI test scenarios from `.feature` scenario blocks in locally checked-out repositories. | `ui-tests-v1.0.0` |
| **[Documentation Issues](doc_issues/README.md)** | GitHub Issues as a documentation source. | ![Status](https://img.shields.io/badge/status-planned-blue) — after v0.1.0; `doc-issues: true` fails the run at start |

**Key features**
- 🔎 Source-code mining: living-doc headers and Gherkin scenarios from locally checked-out repositories
- 🧩 Modular: activate only the mining modes you need (`doc-source`, `ui-tests`)
- 📄 Structured output: [contract](#contracts) artifacts, validated before they are written
- ⚡ Deterministic: the same inputs always produce the same JSON
- 🔁 Pipeline-ready: chains with the other `living-doc-*` actions

---
## Usage

### Prerequisites

Before we begin, ensure you have fulfilled the following prerequisites:
- Every repository a mode reads is checked out (`actions/checkout`) earlier in the job. The `doc-source` and
  `ui-tests` modes read those local checkouts only: they call no GitHub API and need no token.
- Requires Python ≥ 3.10 on `PATH`, found as `python3` (or `python`, if there is no `python3`). The action
  brings its own virtual environment: it creates one under `$RUNNER_TEMP`, installs its requirements there
  and runs with that interpreter, so the caller needs no `actions/setup-python` and the job's own
  interpreter, `PATH` and installed packages are left untouched. A `PATH` whose `python3` is older than
  3.10 fails the step with a one-line error, even if some other name on `PATH` would satisfy the floor.
- Runs on Linux and macOS runners. Every GitHub-hosted Linux and macOS runner already ships a suitable
  `python3`; on a self-hosted one without it, add `actions/setup-python` before this step. Windows runners
  are not supported: the step resolves the venv with POSIX layout (`bin/`, not `Scripts/`).

### Adding the Action to Your Workflow

See the default action step definition:

```yaml
- name: Living Documentation Collector for GitHub
  id: living_doc_collector_gh
  uses: AbsaOSS/living-doc-collector-gh@v0.1.0
  with:
    project-id: your-project               # Required: written to every artifact's metadata.source.project_id

    # modes de/activation
    doc-source: false
    ui-tests: false
```

See the default action step definitions for each mode:

- [Documentation Source mode default step definition](doc_source/README.md#usage)
- [UI Tests mode default step definition](ui_tests/README.md#usage)

#### Full Example of Action Step Definition

See the full example of action step definition (in the example, non-default values are used):

```yaml
- name: Living Documentation Collector for GitHub
  id: living_doc_collector_gh
  uses: AbsaOSS/living-doc-collector-gh@v0.1.0
  with:
    project-id: your-project               # Required: written to every artifact's metadata.source.project_id
    output-path: ./output/collector-gh     # Optional: the default
    allow-partial: true                    # Optional: write without a failed source instead of failing the mode
    doc-source: true                       # Documentation Source mode de/activation
    ui-tests: true                         # UI Tests mode de/activation
    verbose-logging: true                  # Optional: project verbose (debug) logging feature de/activation

    doc-source-repositories: |
        [
          {
            "organization-name": "your-organization-name",
            "repository-name": "your-ui-repository",
            "us-paths":    ["/path/to/checkout/your-ui-repository/features/liv_doc_us"],
            "func-paths":  ["/path/to/checkout/your-ui-repository/features/liv_doc_func"],
            "pages-paths": ["/path/to/checkout/your-ui-repository/pages"]
          }
        ]
    ui-tests-repositories: |
        [
          {
            "organization-name": "your-organization-name",
            "repository-name": "your-ui-repository",
            "paths": ["/path/to/checkout/your-ui-repository/features"]
          }
        ]
```

#### GitHub Enterprise Server

`source_ref.url` permalinks point at `https://github.com` by default. For repositories on GitHub Enterprise
Server, pass the workflow's own server URL:

```yaml
- name: Living Documentation Collector for GitHub
  uses: AbsaOSS/living-doc-collector-gh@v0.1.0
  with:
    project-id: your-project
    github-server-url: ${{ github.server_url }}
    doc-source: true
    doc-source-repositories: |
        [ { "organization-name": "your-organization-name", "repository-name": "your-ui-repository",
            "us-paths": ["/path/to/checkout/your-ui-repository/features/liv_doc_us"] } ]
```

---
## Action Configuration

This section outlines the essential parameters that are common to all modes a user can define. Configure the action by customizing the following parameters based on your needs:

### Inputs

#### Base Inputs

These inputs are common to all modes.

| Input Name          | Description | Required | Default |
|---------------------|-------------|----------|---------|
| `project-id`        | The project the run documents, written to every artifact's `metadata.source.project_id`. Format: [`PROJECT_ID_PATTERN`](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/contracts/pipeline-rules.md) (§ Project id). | Yes | — |
| `output-path`       | Output root. Each mode writes `<output-path>/<mode>/<artifact>.json` and clears only its own `<output-path>/<mode>/` directory, so two collectors (or two runs with different `output-path`) in one tree never touch each other's files. | No | `./output/collector-gh` |
| `allow-partial`     | `false`: any failed source fails its mode, and with it the run. `true`: the mode writes without a failed source and records one `SOURCE_UNAVAILABLE` warning for it; it still fails if every source failed. | No | `false` |
| `github-server-url` | GitHub server the configured repositories live on, used only to build `source_ref.url` permalinks. | No | `https://github.com` |
| `github-token`      | Optional and unused: the `doc-source` and `ui-tests` modes read local checkouts and make no GitHub API call. | No | `''` |
| `doc-issues`        | PLANNED — `Documentation Issues` mode is not available in this version; `true` fails the run at start (`INVALID_CONFIGURATION`). | No | `false` |
| `doc-source`        | Enables or disables `Documentation Source` mode. | No | `false` |
| `ui-tests`          | Enables or disables `UI Tests` mode. | No | `false` |
| `verbose-logging`   | Enables or disables verbose (debug) logging. | No | `false` |

##### Example
```yaml
with:
  project-id: your-project  # Required project id
  doc-source: true          # Activation of Documentation Source mode
  ui-tests: true            # Activation of UI Tests mode
  
  verbose-logging: true     # Activation of verbose (debug) logging
```

#### Mode Inputs

Mode-specific inputs and outputs are detailed in the respective mode's documentation:

- [Documentation Source mode specific inputs](doc_source/README.md#mode-inputs)
- [UI Tests mode specific inputs](ui_tests/README.md#mode-inputs)
    
---
## Action Outputs

The action provides a main output path that allows users to locate and access the generated json files easily. 
This output can be utilized in various ways within your CI/CD pipeline to ensure the documentation is effectively distributed and accessible.

- `output-path`
  - **Description**: The resolved, absolute output root — the `output-path` input made absolute.
  - **Usage**: 
   ``` yaml
    - name: Living Documentation Collector for GitHub
      id: living_doc_collector_gh
      ... rest of the action definition ...
      
    - name: Output Documentation Path
      run: echo "GitHub Collector root output path: ${{ steps.living_doc_collector_gh.outputs.output-path }}"            
    ```

Each enabled mode writes one artifact under the root; with the default `output-path`:

| Mode | Artifact |
|---|---|
| `doc-source` | `output/collector-gh/doc-source/doc-source.json` |
| `ui-tests` | `output/collector-gh/ui-tests/ui-tests.json` |

The layout rule is `living-doc-utilities`'
[pipeline rules](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/contracts/pipeline-rules.md)
(§ Collector output layout).

---
## Errors

Each configured repository entry is one **source**, collected on its own. Codes are defined in
`living-doc-utilities`' [errors](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/contracts/errors.md);
the failure rules are [R13](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/contracts/pipeline-rules.md).

| Situation | Code | Effect |
|---|---|---|
| `project-id` missing or malformed; `github-server-url` not an http(s) URL; an enabled mode's `*-repositories` input not a JSON array, or an entry with a missing key or an invalid value | `INVALID_CONFIGURATION` (error) | The run fails at start, before any work: the log names the input, the entry and the reason; no file is written; exit `1` |
| A configured path of a source does not exist | `SOURCE_UNAVAILABLE` (error) | Default: every source is still tried, then the mode fails — the log names each failed source; the run writes no file; exit `1`. With `allow-partial: true`: one warning per failed source, and the mode writes without it; it still fails if every source failed |
| A source answers with zero entities | `EMPTY_SOURCE` (warning) | Reported in `warnings[]`; the run succeeds |
| A source file is outside a git checkout, or its checkout has no resolvable commit | `NO_SOURCE_URL` (warning) | `source_ref.url` is `""` |

A failed mode fails the whole run: a mode that already wrote its artifact has it removed again, so a run that
exits `1` leaves no output file, not even the other mode's.

`metadata.stats.cardinality.sources_configured` counts the entries of the mode's `*-repositories` input, and
`sources_failed` the sources that failed while being collected — non-zero only with `allow-partial: true`.
`metadata.source.repositories` lists only the repositories the artifact documents: a repository whose every
entry failed is not listed, and stays visible through its `SOURCE_UNAVAILABLE` warning.
Mode-specific warnings are listed in the [Documentation Source](doc_source/README.md#errors) and
[UI Tests](ui_tests/README.md#errors) mode docs.

---
## Contracts

The artifacts this action writes — `doc-source-v1.0.0` and `ui-tests-v1.0.0` — are contracts owned by
[`living-doc-utilities`](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/contracts.md).
This repository imports their models and parsers from the pinned `living-doc-utilities` release; it does not
vendor them: no schema file and no local copy of a contract model is committed here. Every artifact is written
through `write_artifact`, which fills `metadata.stats` and validates the result before anything is written.

> Until `living-doc-toolkit` moves onto `living-doc-utilities` `0.5.0`, `toolkit` on `master` cannot read
> this output.

The authoring formats this action reads and the pipeline it feeds are documented in `living-doc`:
[Living Doc Header Types](https://github.com/AbsaOSS/living-doc/blob/master/docs/guides/living-doc-header-types.md),
[Collecting from GitHub](https://github.com/AbsaOSS/living-doc/blob/master/docs/guides/github-collection.md) and
[Architecture](https://github.com/AbsaOSS/living-doc/blob/master/docs/introduction/architecture.md).

---

## Developer Guide

For local setup, the Makefile quality gate, testing, coverage, running the action locally, versioning, and releasing, see [DEVELOPER.md](DEVELOPER.md).

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
