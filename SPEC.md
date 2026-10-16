# Specification

## Purpose

Anyone who plans work on this repository reads this page. It holds only behaviour that is not built yet; a section
leaves, into the live docs, in the change that builds it ([docs lifecycle](.claude/rules/docs-lifecycle.md)).

Read before: [README](README.md), which routes to everything that is built.

## Contents

- [Windows runner support](#windows-runner-support)

## Windows runner support

Not built, and carried as debt by decision: the ecosystem runs on Linux runners in CI, and this gap is
written down here rather than left undocumented.

`action.yml` assumes the POSIX virtual-environment layout throughout — it probes `$VENV/bin/python` for the reuse
check and installs with `$VENV/bin/pip`. On a `windows-latest` runner `python -m venv` writes `Scripts/python.exe`
and `Scripts/pip.exe` instead, so the step fails on the `pip` line with a bare `No such file or directory` and no
actionable error.

The shell itself is not the problem: `shell: bash` is Git Bash there, and the `command -v python3` resolution and
the version check work as written.

Implementing it needs:

1. A layout probe in the venv step — `bin` on POSIX, `Scripts` on Windows — used by both the reuse check
   and the `pip` invocation, with the resolved interpreter still handed to the run step through
   `steps.venv.outputs.python`.
2. A `windows-latest` job in `integration_test.yml` asserting the same isolation and reuse invariants as
   `Action Venv - Isolation and Reuse`, so the layout cannot regress unnoticed.
3. Dropping the Windows carve-out from the action reference's [Prerequisites](docs/action.md#prerequisites)
   and deleting this section (`.claude/rules/docs-lifecycle.md`).
