# doc_check

Parent: [../CONTEXT.md](../CONTEXT.md)

## Purpose

The `doc-check` mode: `GHDocChecker`, which runs `living-doc-utilities`' authored-input check over the files the
`doc-source` mode reads. Its behaviour is [README.md](README.md); this file maps that page to the code.

Not responsible for: reading the files (`doc_source/collector.py::read_source_files`, shared with `doc-source`); the
check, its codes, fix hints, report text and policy model (`living_doc_utilities.check`, `living_doc_utilities.policy`).

## Conventions

- The report goes to stdout with `sys.stdout.write`, not through `logging`: a workflow command (`::error`,
  `::stop-commands::`) must start its line, and the log format prefixes every record. Everything else is logged.
- The mode reads no file of its own: the corpus comes from `read_source_files`, so `doc-source` and `doc-check` can
  never read different files. A new skip or path list goes there.
- The runner variables `GITHUB_ACTIONS` and `GITHUB_STEP_SUMMARY` are read through `ActionInputs`, like the inputs.

## Code map

What realises each fact of [README.md](README.md), the mode's page:

- The mode runs the check over the files `doc-source` reads → `doc_check/checker.py::GHDocChecker`
- `doc-check: true` turns it on → `action_inputs.py::ActionInputs.is_doc_check_mode_enabled`
- Its files come from `doc-source-repositories` → `doc_check/checker.py::_corpus`
- It runs alone; with another mode the run fails at start → `action_inputs.py::ActionInputs._check_doc_check_runs_alone`
- It writes nothing under `output-path` and sets no output → `main.py::run`
- The files, their entity types and the same skips as `doc-source` → `doc_source/collector.py::read_source_files`
- Each file is named by its path from its repository root → `utils/artifact.py::repository_path`
- A file outside a git checkout is named from its scan root → `utils/artifact.py::relative_path`
- Two repositories with a file at the same path fail the step → `doc_check/checker.py::_corpus`
- The changed paths, one per line, blank lines ignored → `action_inputs.py::ActionInputs.get_doc_check_changed_paths`
- A changed path outside the corpus is skipped; with none in it, nothing is reported → `doc_check/checker.py::GHDocChecker._check`
- The changed files' findings and every relation finding of the corpus → utilities
- The policy file at each repository's root; the default policy without one → `doc_check/checker.py::_policy`
- A finding fails or warns under its own repository's policy → `doc_check/checker.py::_by_repository`
- Each policy file is read whenever a changed path is in the corpus → `doc_check/checker.py::GHDocChecker._check`
- Inside GitHub Actions: the GitHub report and the job summary; outside: the plain lines → `doc_check/checker.py::_report`
- Inside GitHub Actions means `GITHUB_ACTIONS` is `true` → `action_inputs.py::ActionInputs.is_github_actions`
- Exit `1` exactly when a finding fails under its policy → `main.py::_run_doc_check`
- `SOURCE_UNAVAILABLE` for a missing configured path → `utils/feature_file_discovery.py::discover_feature_files`
- `INVALID_CONFIGURATION` for an unreadable or rejected policy file → `doc_check/checker.py::_policy`
- An unreadable file is logged and skipped → `doc_source/collector.py::_read`
- A job summary that can't be written is logged → `doc_check/checker.py::_report`
- The report's lines, annotations and table → utilities
