# Golden entities

Copied verbatim from `AbsaOSS/living-doc-utilities` `tests/fixtures/golden/` at tag `v0.9.0`
(commit `7a6fb9f36dd24f8593224c14bef1058dd09c7ea6`). Do not edit here: re-copy from the `utilities`
tag this repository pins.

- `gherkin/liv_doc_*/` and `pageobject/` are the source-code inputs; `tests/doc_source/test_golden_entities.py`
  runs them through the full `doc-source` collector.
- `gherkin/scenario-bodies.feature` and `expected/scenario-bodies.json` are a scenario file and its parsed
  scenarios; `tests/ui_tests/test_golden_scenarios.py` runs the file through the full `ui-tests` collector.
- `gh-issues/` and the other `expected/` files are the issue-body inputs and their hand-written entities, kept for
  the `doc-issues` port (PLANNED after v0.1.0).
