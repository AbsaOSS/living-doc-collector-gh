# Golden entities

Copied verbatim from `AbsaOSS/living-doc-utilities` `tests/fixtures/golden/` at tag `v0.9.0rc2`
(commit `e8140793452a599a9106b0f3ecdae18c7acb9ed7`). Do not edit here: re-copy from the `utilities`
tag this repository pins.

- `gherkin/liv_doc_*/` and `pageobject/` are the source-code inputs; `tests/doc_source/test_golden_entities.py`
  runs them through the full `doc-source` collector.
- `gherkin/scenario-bodies.feature` and `expected/scenario-bodies.json` are a scenario file and its parsed
  scenarios; `tests/ui_tests/test_golden_scenarios.py` runs the file through the full `ui-tests` collector.
- `gh-issues/` and the other `expected/` files are the issue-body inputs and their hand-written entities, kept for
  the `doc-issues` port (PLANNED after v0.1.0).
