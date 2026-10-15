# Documentation Issues Mode

![Status](https://img.shields.io/badge/status-planned-blue)

## Purpose

Anyone who asks about GitHub Issues as a documentation source reads this page. The mode is planned: the page says
what enabling it does in this version, and where its former description is kept for the port.

Read before: [Action reference](../docs/action.md)

## Contents

- [State](#state)
- [Enabling it](#enabling-it)
- [Former description](#former-description)

## State

- PLANNED: GitHub Issues as a documentation source is not available in this version → `main.py::DOC_ISSUES_PLANNED_MESSAGE`
- The code in `doc_issues/` is kept aside unchanged for its port onto the `living-doc-utilities` contracts → `doc_issues/collector.py::GHDocIssuesCollector`
- Every gate leaves that code, the modules only it uses and their tests out; each exclusion is one commented line → `Makefile::KEPT_ASIDE`

## Enabling it

- `doc-issues: true` fails the run at start with ``[INVALID_CONFIGURATION] `doc-issues` mode is planned and not available in this version``; exit `1` → `main.py::run`
- No `doc-issues-*` input is read: `doc-issues-repositories` and `doc-issues-project-state-mining` are PLANNED → [Inputs](../docs/action.md#inputs)

## Former description

- The page as it stood before this rebuild describes the mode as it ran, for the port → [`doc_issues/README.md` at `1e968ce`](https://github.com/AbsaOSS/living-doc-collector-gh/blob/1e968ce551e03d0554d31461e993f9250b6eebfb/doc_issues/README.md)
  - It covers documentation tickets, their labels, the inputs, the output and its schema.
- It matches the code kept aside in `doc_issues/`, not a mode this version runs → `doc_issues/models.py::AdapterResult`
