# Documentation Check Mode

## Purpose

This page defines the mode that checks a pull request's authored living-doc files before the merge: the files it
checks, the changed paths, the policy file, its report and how it fails.

Read before: [Documentation Source mode](../doc_source/README.md) · Next: back to the [Action reference](../docs/action.md)

## Contents

- [Activation](#activation)
- [Usage](#usage)
- [Corpus](#corpus)
- [Changed paths](#changed-paths)
- [Policy](#policy)
- [Report](#report)
- [Errors](#errors)
- [Formats](#formats)

## Activation

The mode runs `living-doc-utilities`' authored-input check over the files the Documentation Source mode reads,
for the paths a pull request changed, and fails the step on the policy's codes.

- `doc-check: true` turns it on; `doc-check-changed-paths` lists the changed paths ([Inputs](../docs/action.md#inputs))
- Its files come from `doc-source-repositories`, the same entries a `doc-source` step takes ([repository entry](../doc_source/README.md#repository-entry))
- It runs alone: with `doc-source` or `ui-tests` also `true`, the run fails at start
- It writes nothing under `output-path` and sets no output
- A collector that fails a pull request on its findings bends the frame's F2; the frame records it as exception E2 → [Principles](https://github.com/AbsaOSS/living-doc/blob/master/docs/introduction/principles.md)

## Usage

A pull-request job that checks out the repository with its history, lists the changed paths and checks them:

```yaml
- uses: actions/checkout@v4
  with:
    fetch-depth: 0                         # the base commit, for the diff
- name: List the changed paths
  id: changed
  env:
    BASE: ${{ github.event.pull_request.base.sha }}
  run: |
    { echo 'paths<<EOF'; git diff --name-only "$BASE...HEAD"; echo 'EOF'; } >> "$GITHUB_OUTPUT"
- name: Check the changed living-doc files
  uses: AbsaOSS/living-doc-collector-gh@v0.2.0
  with:
    project-id: aul
    doc-check: true
    doc-source-repositories: |
        [ { "organization-name": "absa-group", "repository-name": "aul-ui",
            "us-paths": ["${{ github.workspace }}/playwright/features/liv_doc_us"] } ]
    doc-check-changed-paths: ${{ steps.changed.outputs.paths }}
```

## Corpus

The corpus is every file the Documentation Source mode reads → [Discovery](../doc_source/README.md#discovery)

- The files under the `us-paths`, `func-paths` and `pages-paths` of each entry, read by the same reader as `doc-source`
- The path list gives each file its entity type: User Story, Functionality, or Feature for a PageObject file
- The same skips: `.feature` files under a `tutorial*` directory, and `.ts` files with no living-doc header
- Each file is named by its path from its repository root, as `git diff --name-only` prints it
  - Why: GitHub puts an annotation on a line only for a path from the repository root.
- A file outside a git checkout is named by its path from its scan root
- Two configured repositories holding a file at the same path fail the step

## Changed paths

- `doc-check-changed-paths` takes one path per line, as `git diff --name-only <base>...<head>` prints them; blank lines are ignored
- A path outside the corpus is skipped: a file of no configured path list, or a deleted file
- With no changed path in the corpus, the mode reports nothing and passes
- The changed files' own findings are reported, and every relation finding of the whole corpus → [What it reports](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/check.md#what-it-reports)
  - So a changed file that breaks a relation another file holds is reported too.

## Policy

- The mode reads `living-doc-policy.yaml` at the root of each repository's checkout, the directory that holds `.git`
- A finding fails or warns under the policy of the repository its file is in
- Without the file, or outside a git checkout, the default policy applies: every code of the default list fails
- `check.warn` names the codes that only warn → [Policy file](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/check.md#policy-file)
- Each policy file is read whenever a changed path is in the corpus, so an invalid one fails the step even with no finding

A policy that keeps a criterion's legacy state a warning:

```yaml
check:
  warn:
    - LEGACY_AC_STATE
```

## Report

- Inside GitHub Actions, where the runner sets `GITHUB_ACTIONS` to `true`, the step's log shows the check's GitHub report:
  - one line per finding, `<path>:<line>: <CODE> <message> Fix: <hint>`;
  - a summary annotation, then an `::error` or `::warning` annotation per finding, on its line, while GitHub's per-step limit lasts.
- The job summary, the file `GITHUB_STEP_SUMMARY` names, gets a table of every finding
- With findings in more than one repository, each repository gets its own report and table, under its own policy
- Outside GitHub Actions, only the plain finding lines are printed
- The step exits `1` exactly when a finding's code fails under its policy, and `0` otherwise, warnings included
- The report's lines, annotations and table are `living-doc-utilities`' → [Report](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/check.md#report)

## Errors

The run-level codes are in the action reference → [Errors](../docs/action.md#errors). Within the mode:

| Situation | Behaviour |
|---|---|
| A configured path does not exist | `SOURCE_UNAVAILABLE`: the step fails; `allow-partial` does not apply; exit `1` |
| Two configured repositories hold a file at the same path | `INVALID_CONFIGURATION`, naming the path; exit `1` |
| A policy file can't be read, is not YAML, or the policy model rejects it | `INVALID_CONFIGURATION`, naming the file; exit `1` |
| A file can't be read | Log warning, skip the file |
| The job summary can't be written | Log warning; the exit code still follows the findings |

## Formats

- The files follow the authoring formats in `living-doc` → [Authoring formats](https://github.com/AbsaOSS/living-doc/blob/master/docs/reference/authoring-formats.md)
- The codes, the default fail list, the fix hints and the policy model come from `living-doc-utilities`' check → [Check](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/check.md)
