# doc_issues

Parent: [../CONTEXT.md](../CONTEXT.md)

## Purpose

The PLANNED `doc-issues` mode's code, kept aside unchanged for its port onto the `living-doc-utilities` contracts.
Its page is [README.md](README.md); this file maps that page to the code.

Not responsible for: any run of this version. `main.py` fails the run when the mode is requested, and nothing here
is imported, tested, linted or type-checked (the root `CONTEXT.md`, Invariants and gotchas).

## Code map

What realises each fact of [README.md](README.md), the mode's page:

- The mode is not available in this version → `main.py::DOC_ISSUES_PLANNED_MESSAGE`
- Its code is kept aside for the port → `doc_issues/collector.py::GHDocIssuesCollector`
- Every gate leaves it out → `Makefile::KEPT_ASIDE`
- `doc-issues: true` fails the run at start, exit `1` → `main.py::run`
- The former description matches the kept-aside code → `doc_issues/models.py::AdapterResult`
