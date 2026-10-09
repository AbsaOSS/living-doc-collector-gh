# Specification

## Windows runner support

Not built, and carried as debt by decision: the ecosystem runs on Linux runners in CI, and this gap is
written down here rather than left undocumented.

`action.yml` assumes the POSIX virtual-environment layout throughout — it probes `$VENV/bin/python` for
the reuse check and installs with `$VENV/bin/pip`. On a `windows-latest` runner `python -m venv` writes
`Scripts/python.exe` and `Scripts/pip.exe` instead, so the step fails on the `pip` line with a bare
`No such file or directory` and no actionable error. The shell itself is not the problem: `shell: bash`
is Git Bash there, and the `command -v python3` resolution and the version check work as written.

Implementing it needs:

1. A layout probe in the venv step — `bin` on POSIX, `Scripts` on Windows — used by both the reuse check
   and the `pip` invocation, with the resolved interpreter still handed to the run step through
   `steps.venv.outputs.python`.
2. A `windows-latest` job in `integration_test.yml` asserting the same isolation and reuse invariants as
   `Action Venv - Isolation and Reuse`, so the layout cannot regress unnoticed.
3. Dropping the Windows carve-out from the `README.md` prerequisite bullet and deleting this section
   (`.claude/rules/docs-lifecycle.md`).

---

The `doc-source` and `ui-tests` modes this file used to describe are implemented and shipped.
Per [`.claude/rules/docs-lifecycle.md`](.claude/rules/docs-lifecycle.md), that content has
moved to the live docs:

- [`README.md`](README.md) — modes overview, base inputs, outputs.
- [`doc_issues/README.md`](doc_issues/README.md) — `doc-issues` mode (PLANNED after v0.1.0).
- [`doc_source/README.md`](doc_source/README.md) — `doc-source` mode.
- [`ui_tests/README.md`](ui_tests/README.md) — `ui-tests` mode.
- [`DEVELOPER.md`](DEVELOPER.md) — local-dev workflow, quality gate, testing.

When prospective (not-yet-built) behavior needs a written spec again, add it here and delete
each section as its implementing PR lands.
