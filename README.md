# Living Documentation Collector for GitHub

[![Build and Test](https://github.com/AbsaOSS/living-doc-collector-gh/actions/workflows/test.yml/badge.svg)](https://github.com/AbsaOSS/living-doc-collector-gh/actions/workflows/test.yml)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

## Purpose

A GitHub Action that extracts living documentation from locally checked-out repositories. It is the collect step
of a living-documentation pipeline. It writes JSON, in the contracts `living-doc-utilities` owns, for the downstream
`living-doc-*` tools.

## Contents

- [Overview](#overview)
- [Usage tip](#usage-tip)
- [Inputs and outputs](#inputs-and-outputs)
- [Where next](#where-next)
- [Developer Guide](#developer-guide)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

## Overview

- **Documentation Source** (`doc-source`): User Story, Functionality and Feature headers from `.feature` and PageObject files, as `doc-source-v1.0.0` → [mode](doc_source/README.md)
- **UI Tests** (`ui-tests`): UI test scenarios from `.feature` scenario blocks, as `ui-tests-v1.0.0` → [mode](ui_tests/README.md)
- **Documentation Issues** (`doc-issues`): GitHub Issues as a documentation source; PLANNED, and `true` fails the run at start → [mode](doc_issues/README.md)
- Modular: activate only the modes you need; each writes one artifact, validated before it is written → [Contracts](docs/action.md#contracts)
- Deterministic: the same checkouts always give the same records; collection reads only those checkouts.
- Pipeline-ready: it chains with the other `living-doc-*` actions → [Architecture](https://github.com/AbsaOSS/living-doc/blob/master/docs/introduction/architecture.md)
- GitHub Actions first: a step in a workflow is the supported way to run it; a local run is a development and operator-check aid, not a second deployment target → [Debug run](DEVELOPER.md#debug-run), [Local Integration Run](DEVELOPER.md#local-integration-run)
- AI-free: collect → normalize → generate is deterministic tooling, with no LLM call anywhere in that path → [AI-free Principle](CONTRIBUTING.md#ai-free-principle)
  - The agentic layer in [`living-doc` `agentic/`](https://github.com/AbsaOSS/living-doc/tree/master/agentic) can speed up authoring issues and `.feature` files.
  - It is never a runtime dependency: a human writing the same input by hand is a fully supported, identical path.

## Usage tip

One step that runs both modes over a repository checked out earlier in the job:

```yaml
- name: Living Documentation Collector for GitHub
  id: living_doc_collector_gh
  uses: AbsaOSS/living-doc-collector-gh@v0.2.0
  with:
    project-id: your-project
    doc-source: true
    doc-source-repositories: |
        [ { "organization-name": "your-organization-name", "repository-name": "your-ui-repository",
            "us-paths": ["/path/to/checkout/your-ui-repository/features/liv_doc_us"] } ]
    ui-tests: true
    ui-tests-repositories: |
        [ { "organization-name": "your-organization-name", "repository-name": "your-ui-repository",
            "paths": ["/path/to/checkout/your-ui-repository/features"] } ]
```

What the runner needs: [Prerequisites](docs/action.md#prerequisites). Where the files land: [Output layout](docs/action.md#output-layout).

## Inputs and outputs

Every input at a glance; required flags, defaults and errors are in the [action reference](docs/action.md#inputs).

- `project-id` (required): the project the run documents
- `doc-source`, `doc-source-repositories`: run the Documentation Source mode, and its sources
- `ui-tests`, `ui-tests-repositories`: run the UI Tests mode, and its sources
- `output-path`: the output root, `./output/collector-gh` by default
- `allow-partial`: write without a failed source instead of failing the mode
- `github-server-url`: the GitHub server, for `source_ref.url` permalinks
- `verbose-logging`: verbose (debug) logging
- `github-token`: unused in this version
- `doc-issues`, `doc-issues-repositories`, `doc-issues-project-state-mining`: PLANNED, not available in this version

The one output, `output-path`, is the resolved, absolute output root; each mode writes its artifact under it
([Outputs](docs/action.md#outputs)).

## Where next

| I want to… | Read |
|---|---|
| set every input, read the output, handle an error | [Action reference](docs/action.md) |
| mine user stories, functionalities and features from source files | [Documentation Source mode](doc_source/README.md) |
| mine UI test scenarios | [UI Tests mode](ui_tests/README.md) |
| know what `doc-issues` does in this version | [Documentation Issues mode](doc_issues/README.md) |
| write the headers and scenarios this action reads | [Living Doc Header Types](https://github.com/AbsaOSS/living-doc/blob/master/docs/guides/living-doc-header-types.md) |
| see what is planned but not built yet | [Specification](SPEC.md) |
| set up the repository, run the gates or a local run, release | [Developer guide](DEVELOPER.md) |
| contribute a change | [Contributing](CONTRIBUTING.md) |

## Developer Guide

Setup, the quality gates, local runs, versioning, releasing and the documentation rules: [DEVELOPER.md](DEVELOPER.md).

## Contributing

Bug reports, feature requests, branch and pull request conventions, and the AI-free principle:
[CONTRIBUTING.md](CONTRIBUTING.md). Contributions are welcome: bug fixes, documentation and new features.

## License

Apache License 2.0; see [LICENSE](LICENSE).

## Contact

Questions, bugs and feature requests: the [GitHub Issues page](https://github.com/AbsaOSS/living-doc-collector-gh/issues).
Maintained by [ABSA Group Limited](https://github.com/AbsaOSS).
