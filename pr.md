#129: the action in its own venv, on utilities 0.6.0

## Overview

The action used to `pip install -r requirements.txt` straight into whatever interpreter the caller's job had
on `PATH`, export a `PYTHONPATH` entry pointing at a directory that does not exist, and route six of its ten
inputs through `$GITHUB_ENV` before reading them back. All three leaked into the caller's job. This change
gives the action its own virtual environment and leaves the caller's environment alone:

- **`action.yml`** resolves `python3`/`python` from `PATH`, fails with one actionable error below 3.10, and
  creates a venv at `$RUNNER_TEMP/living-doc-collector-gh-venv`, reused when it already exists, so two steps
  of the action in one job install once. `requirements.txt` is installed into that venv and `main.py` runs
  with its interpreter. The `PYTHONPATH` step and the `$GITHUB_ENV` block are gone; all ten inputs are now
  passed in the run step's own `env:`, each from `${{ inputs.* }}`.
- The two `*-repositories` JSON strings are passed **verbatim**, with no `jq -c .` compaction:
  `action_inputs._get_repositories` reads them with `json.loads`
  ([action_inputs.py:61](action_inputs.py#L61)), which tolerates any whitespace, and a step `env:` value
  carries newlines as they are — unlike a `$GITHUB_ENV` line, which is why the compaction existed.
- **`requirements.txt` is now runtime-only** — `living-doc-utilities==0.6.0` (the `[github]` extra dropped:
  no active module imports anything needing it), `pydantic`, and `tomli` below Python 3.11.
  `typing_extensions` is gone too: `git grep` finds no direct import, only the pin.
  Everything else moved to the new **`requirements-dev.txt`**, which starts with `-r requirements.txt`.
  `make qa` now fails when a test, lint or type tool reappears in the runtime file
  ([tools/check_runtime_requirements.py](tools/check_runtime_requirements.py)).
- **`utilities` 0.6.0.** The golden corpus is re-copied from tag `v0.6.0`, and the warning file moves from
  free text to the typed `path` field (`DEC-77`). 0.6.0 also closes the AC variant grammar to **one**
  declaration per criterion (`DEC-71`), which the repo's own `full_sample` fixtures violated — each had an
  `Aspect:` bullet *and* a placeholder bullet on the same criterion. They are split, and the keyword form is
  now covered by tests in both modes.
- **`release_draft.yml`** passes `release-notes-title: '## [Rr]elease [Nn]otes'`. The action's default,
  `[Rr]elease [Nn]otes:`, needs a colon no PR heading in this repository has, so the draft was taking no
  line from any PR body.

`doc_issues/` is untouched: PLANNED after v0.1.0 (`DEC-50`, `D28`). Only its dev-only dependencies
(`PyGithub`, `requests`, `types-requests`) changed file.

## Release Notes

- **Breaking:** `requirements.txt` is now runtime-only — `living-doc-utilities`, `pydantic` and `tomli` (below Python 3.11). Anyone installing this action's `requirements.txt` to get its lint or test tools must use the new `requirements-dev.txt`.
- **Breaking:** the action is pinned to `living-doc-utilities` `0.6.0`, which allows one AC variant declaration per criterion: a criterion carrying both an `Aspect:` bullet and a keyword bullet is now dropped with a `MALFORMED_AC` warning.
- The action brings its own virtual environment under `$RUNNER_TEMP` and runs with its interpreter, so it installs nothing into the caller's Python and leaves the job's `PATH`, `PYTHONPATH` and packages untouched; no `actions/setup-python` is needed, only Python ≥ 3.10 on `PATH`.
- The action no longer writes any of its inputs to `$GITHUB_ENV`; all ten are passed in its own run step.
- A `PATH` whose Python is older than 3.10 now fails the action with one actionable error instead of an obscure install or import failure.
- Every warning about one source file now carries that file in the typed `path` field, with `entity_id`, `ac_id` and `line_no` wherever the emitter knows them, instead of a `path=...` prefix inside the free-text `context`. A cross-entity warning (`UNRESOLVED_RELATION`, `FEATURE_WITHOUT_FUNCTIONALITY`, …) is not about one file and names its entity only.
- `requirements.txt` is now rejected by `make qa` when it names a development tool **or** carries a line that is not a plain pin — an `-r` include, a VCS/URL reference or a local wheel — since those hide what is really installed.
- An acceptance criterion may declare its variants with a keyword (`- rule: minimum-length, ...` under a description naming `{rule}`) as well as with `Aspect:`; a `@AC:<id>/<keyword>:<value>` scenario tag links one declared value and a bare `@AC:<id>` links the whole criterion.
- `make qa` gained `make runtime-requirements`, which fails when `requirements.txt` names a test, lint or type tool.
- Release-note lines are now collected from each PR's `## Release Notes` section; drafts generated before this change took none.

## Related

Closes #<issue>

---

## Acceptance criteria

| # | Criterion | Where it is satisfied |
|---|---|---|
| 1 | `action.yml` uses Python from `PATH`, creates a venv under `$RUNNER_TEMP`, installs `requirements.txt` into it, runs `main.py` with its interpreter; no bare `pip install`, nothing to `$GITHUB_ENV`/`$GITHUB_PATH`, no `PYTHONPATH` step | [action.yml:81-88](action.yml#L81-L88) (resolve, check, create, install), [action.yml:108](action.yml#L108) (`main.py` via `steps.venv.outputs.python`), [action.yml:93-106](action.yml#L93-L106) (all ten inputs in the run step's `env:`). `grep -n 'GITHUB_ENV\|GITHUB_PATH\|PYTHONPATH' action.yml` matches only the comment on [action.yml:75](action.yml#L75) |
| 2 | A workflow runs the action twice in one job beside a conflicting `pydantic`; both succeed, the venv is reused, a later step reports unchanged `python --version` / `which python`. A Python 3.9 job fails with the one-line error | `Action Venv - Isolation and Reuse` (`integration_test.yml`): `pip install 'pydantic<2'`, two `uses: ./` steps, then one assertion step that checks (a) both artifacts exist, (b) **neither step wrote the mode it disabled** — the assertion that catches an input leaking through `$GITHUB_ENV`, which comparing interpreters cannot see, (c) `pyvenv.cfg`'s **mtime is unchanged**, which is what actually distinguishes a reused venv from a rebuilt one (a marker file inside the venv does not: `python -m venv` without `--clear` leaves pre-existing files alone), and (d) a `diff` of `which python` / `python --version` / the runner's `pydantic.VERSION` before and after. `Action Venv - Python 3.9 Is Rejected`: asserts `PATH`'s Python really is 3.9, the step's `outcome == 'failure'`, and that no venv directory was created. The error **text** is pinned separately in [tests/test_action_yml.py](tests/test_action_yml.py), because a composite action's step log is not readable from a later workflow step. **Run links: not yet available — the branch is not pushed (`no commit`); add both links here after the first CI run.** |
| 3 | `requirements.txt` lists only `living-doc-utilities==0.6.0` (no `[github]`), `pydantic`, `tomli` for < 3.11; a deny-list check in `make qa`; `requirements-dev.txt` exists; `Makefile`, `test.yml`, `integration_test.yml` use it; `dependabot.yml` covers both | [requirements.txt](requirements.txt) (3 pins), [tools/check_runtime_requirements.py:82-94](tools/check_runtime_requirements.py#L82-L94) wired at [Makefile:27](Makefile#L27) and [Makefile:56-58](Makefile#L56-L58), [requirements-dev.txt](requirements-dev.txt) (`-r requirements.txt` first), [Makefile:24](Makefile#L24), [test.yml:99](.github/workflows/test.yml#L99) + [test.yml:123](.github/workflows/test.yml#L123) + [test.yml:153](.github/workflows/test.yml#L153) (all `make install`), [integration_test.yml:55](.github/workflows/integration_test.yml#L55), triggers at [integration_test.yml:31-32](.github/workflows/integration_test.yml#L31-L32) and [test.yml:62](.github/workflows/test.yml#L62). `dependabot.yml`: one `pip` entry with `directory: "/"` already covers both files — the `pip` ecosystem scans the configured directory for every requirements file in it, so **no second entry was added**; the reason is now a comment at [dependabot.yml:22-23](.github/dependabot.yml#L22-L23). Pinned by [tests/test_runtime_requirements.py](tests/test_runtime_requirements.py) (17 tests) |
| 4 | The golden corpus is re-copied from `utilities` `v0.6.0`, its README names that tag and commit, and the golden `doc-source` run still matches the canonical parsers | `tests/fixtures/golden/README.md` lines 3-5 ([file](tests/fixtures/golden/README.md)) (`v0.6.0`, `80378738a52f57452374f5645912d254ea1f5b09`). `diff -r` against a `git archive v0.6.0` extract reports only the local `README.md`. [test_golden_entities.py:85-99](tests/doc_source/test_golden_entities.py#L85-L99) recomputes the expectation from the fixtures through the canonical parsers and passes unchanged |
| 5 | New tests: a keyword AC carries `aspect` equal to its declared values; a keyword tag → `AcLink(aspect=<value>)`; a bare tag on an AC with variants → `AcLink(aspect=None)`; `Aspect:` + a keyword → absent with `MALFORMED_AC` | [test_full_sample.py:197-220](tests/doc_source/test_full_sample.py#L197-L220) (`aspect == ["admin","viewer","auditor"]` for `US-901-06`, `["Save","Submit"]` for `FUNC-901-01`, each with `placeholder_values` keyed by the folded keyword name), [tests/ui_tests/test_full_sample.py:136-147](tests/ui_tests/test_full_sample.py#L136-L147) (`("US-901-06","admin")` from `@AC:US-901-06/user-role:admin`; `("US-901-06",None)` from the bare tag), [test_collector.py:548-567](tests/doc_source/test_collector.py#L548-L567) (`DEC-71`: criterion absent, `MALFORMED_AC` reported). Fixtures: [us-901-full-story.feature](tests/fixtures/full_sample/doc_source/us/us-901-full-story.feature), [func-901-full-functionality.feature](tests/fixtures/full_sample/doc_source/func/func-901-full-functionality.feature), [full-scenarios.feature](tests/fixtures/full_sample/ui_tests/full-scenarios.feature) — none in the golden corpus |
| 6 | Every warning about one file carries the typed `path` in `doc-source` and `ui-tests` alike, with `entity_id`, `ac_id`, `line_no` wherever known; tested on a `MALFORMED_AC` from a `.feature` header, a `MISSING_ENTITY_ID` and a duplicate-id `AUTHORING_ERROR` | [utils/artifact.py:193](utils/artifact.py#L193) (`with_path` sets the field, `context` untouched), [utils/artifact.py:167](utils/artifact.py#L167) (`NO_SOURCE_URL`), [doc_source/collector.py:237](doc_source/collector.py#L237), [:270](doc_source/collector.py#L270), [:331](doc_source/collector.py#L331), [ui_tests/collector.py:226](ui_tests/collector.py#L226). `git grep 'context=.*path='` over `doc_source ui_tests utils main.py action_inputs.py` returns nothing. Tests: [test_collector.py:563-565](tests/doc_source/test_collector.py#L563-L565) (`MALFORMED_AC`: `path`, `entity_id`, `ac_id`, `line_no`), [test_collector.py:286](tests/doc_source/test_collector.py#L286) (`MISSING_ENTITY_ID`: `path`, `line_no`), [test_collector.py:604](tests/doc_source/test_collector.py#L604) (duplicate-id `AUTHORING_ERROR`: `path`, `entity_id`), [test_artifact.py:212-226](tests/utils/test_artifact.py#L212-L226), [tests/ui_tests/test_collector.py:283-285](tests/ui_tests/test_collector.py#L283-L285). [test_golden_entities.py:111-122](tests/doc_source/test_golden_entities.py#L111-L122) now pins the two canon warnings on `entity_id='FEAT-003'` in the typed field, not only in the text |
| 7 | README states "Requires Python ≥ 3.10 on `PATH`"; `release_draft.yml` passes `release-notes-title: '## [Rr]elease [Nn]otes'`; `DEVELOPER.md` describes both requirements files and where the release notes come from | [README.md](README.md) lines 39-44, [release_draft.yml:71](.github/workflows/release_draft.yml#L71), [DEVELOPER.md](DEVELOPER.md) lines 35-47 (the two files, with who installs each, plus the Dependabot note at line 46), [DEVELOPER.md](DEVELOPER.md) lines 421-428 (the notes are the bullet lines directly under each PR's `## Release Notes`, one line each) |
| 8 | `make qa` green; the test count and coverage in the PR body | **Green.** Black clean, ruff clean, **Pylint 9.99/10**, mypy `Success: no issues found in 19 source files`, `no-vendored-schemas` + `retired-names` + `runtime-requirements` clean, **286 tests passed**, **coverage 98.97 %** (gate 80 %). Link-check is its own workflow, not a `make qa` target; `lychee --include-fragments --offline './**/*.md'` run separately: 63 OK, 0 errors |

### `make qa` output (tail)

```
Your code has been rated at 9.99/10 (previous run: 9.99/10, +0.00)
mypy .
Success: no issues found in 19 source files
python3 -m living_doc_utilities.contracts.check_no_vendored_schemas --allow doc_issues
python3 tools/check_runtime_requirements.py
...
Name                                    Stmts   Miss  Cover
-----------------------------------------------------------
action_inputs.py                           98      0   100%
doc_source/collector.py                   155      0   100%
main.py                                    49      1    98%
tools/check_runtime_requirements.py        38      1    97%
ui_tests/collector.py                      97      1    99%
utils/artifact.py                         125      0   100%
utils/constants.py                         41      3    93%
utils/feature_file_discovery.py            44      2    95%
utils/utils.py                             67      0   100%
-----------------------------------------------------------
TOTAL                                     780      8    99%
Required test coverage of 80% reached. Total coverage: 98.97%
============================= 286 passed in 6.09s ==============================
```

### Notes for the reviewer

- **The `full_sample` fixture change is not cosmetic.** `utilities` 0.6.0 reads a `- <name>: <values>` bullet
  as the criterion's *keyword* — the other spelling of `Aspect:` — only when the description names
  `{<name>}`, and allows one variant declaration per criterion. Both `full_sample` criteria carried
  `Aspect:` *and* a placeholder bullet, so on 0.6.0 the bullet became an `UNPARSED_AC_LINE` and
  `placeholder_values` emptied, failing R12 check 3. `US-901-01` now keeps `Aspect:` alone, a new
  `US-901-06` carries the keyword, and `FUNC-901-01` switched to the keyword form — so both spellings stay
  covered and `placeholder_values` is occupied under both record roots.
- `tools/` is a new directory with the deny-list check and an `__init__.py`, so the check is importable
  from a test rather than only runnable as a script.
- `.github/copilot-instructions.md` and `.github/agents/devops-engineer.agent.md` both described the old
  single-file, install-into-the-runner shape; both are updated in this change.
- **Black's `force-exclude` was an unanchored `test`**, so it matched `ui_tests/` and the whole `tests/` tree
  as substrings: `make format-check` was silently skipping 27 of the 41 files it passes in — all `ui_tests/`
  production code included — and 6 tracked files were in fact unformatted. `pyproject.toml` now anchors the
  pattern to mirror the Makefile's `KEPT_ASIDE`, and those 6 files are reformatted here.
- **`runtime-requirements` is now wired into CI.** It was in `make qa` but no workflow invoked it, so the
  parity invariant `Makefile` and `DEVELOPER.md` both assert ("`test.yml` runs the same targets") was false.
- **The run step uses `-E`.** A venv isolates site-packages, not the environment: a caller's `PYTHONPATH`
  still precedes it on `sys.path`, so a package vendored there would shadow the pinned one. The venv step
  also unsets `PIP_TARGET`/`PIP_PREFIX`/`PIP_USER`, which would redirect the install out of the venv.
- **`MISSING_STATUS`/`STATUS_AC_MISMATCH` now carry `path`.** They are facts about one entity's own header,
  so the file belongs in the typed field; the genuinely cross-entity warnings keep it unset (`DEC-77`).
  `NO_SOURCE_URL` now carries its `entity_id`, and its `path` is scan-root-relative like every other
  emitter's rather than repo-root-relative.
