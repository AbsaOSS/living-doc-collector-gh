## Overview

In v0.1.0, `collector-gh` runs only `doc-source` and `ui-tests`. Both read local checkouts, so this PR
removes the last network call. It also makes the collector follow `living-doc-utilities`'
[pipeline rules](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/contracts/pipeline-rules.md)
(§ Project id, § Collector output layout, § R13) and
[error codes](https://github.com/AbsaOSS/living-doc-utilities/blob/master/docs/contracts/errors.md). Task `P35-CGH1c`.

**Output layout**
- New input `output-path`, default `./output/collector-gh`.
- Each mode writes `<output-path>/<mode>/<artifact>.json` and clears only its own `<mode>/` directory.
- The `output-path` action output still reports the resolved absolute root.
- `utilities`' `OUTPUT_PATH` and the unused `DOC_ISSUES_OUTPUT_PATH` are no longer used.

**`project-id`**
- New required input, checked against the imported `PROJECT_ID_PATTERN` before any work.
- It is written to every artifact's `metadata.source.project_id`.
- `DEFAULT_PROJECT_ID = "unset-project"` and its TODO are gone.

**No network**
- The `/octocat` token check is removed, along with `get_ca_bundle` and the `requests` import in active code.
- `github-token` is now optional and unused.
- `action.yml` no longer passes `INPUT_GITHUB_TOKEN`. New inputs go straight into the run step's `env:`.

**GitHub server URL**
- New module `utils/github_urls.py` (`server_url`, `blob_url`) is the only module that holds GitHub addresses.
- New input `github-server-url`.
- Every `source_ref.url` is now a commit permalink: `<server>/<org>/<repo>/blob/<HEAD sha>/<path>`. The sha is
  `git rev-parse HEAD` of the file's checkout, read once per checkout. It uses `--git-dir`, so a broken `.git`
  never borrows an enclosing repository's commit.
- A file outside git still gets `url: ""` and `NO_SOURCE_URL`. So does a checkout whose HEAD git cannot resolve.

**Configuration errors at start**
- These fail the run with `INVALID_CONFIGURATION`, before any work and with no file written:
  - a missing or malformed `project-id`;
  - an invalid `github-server-url`;
  - an enabled mode's `*-repositories` input that is not a JSON array;
  - an entry with a missing key or a bad value. The message names the input, the entry and the key.
- Every error is logged at once.
- A disabled mode's repositories are never read.
- The config models now raise `ValueError` with the reason, instead of logging and returning `False`.

**R13 per source**
- Each `*-repositories` entry is one source, collected on its own by `collect_sources`.
- A missing configured path is `SOURCE_UNAVAILABLE`. It replaces the old warn-and-skip, and is raised before the
  source adds anything.
- By default, every source is tried first; then the mode fails, writes no file, and the run exits `1`.
- With the new input `allow-partial: true`, the mode writes without the failed sources, with one warning each.
  It still fails if every source failed.
- A source that answers with zero entities gives `EMPTY_SOURCE`.
- `sources_configured` is the entry count. `sources_failed` counts only sources that failed while being collected.

**CI and docs**
- `integration_test.yml` uses the new layout and passes a `project-id`, with no token. It also checks that every
  `source_ref.url` is a permalink at the checked-out HEAD.
- `README.md` and the two mode READMEs now cover inputs, output, paths and errors, and link to `living-doc` for
  formats and flows.
- `README.md` has a new Errors section and a GitHub Enterprise Server example. The token how-to is removed.
- In `DEVELOPER.md`, the SSL/CA-bundle section is removed (no HTTPS request is left) and the local-run scripts use
  `INPUT_PROJECT_ID`.
- `workflows/README.md` (a mode "not developed and not in use") is deleted.
- Agent and rule files: only the lines this PR makes false were changed (token, CA bundle, REST check, sub-paths,
  fake-`.git` test pattern).

`doc_issues/` is untouched and stays out of the build.

### Acceptance criteria

- [x] **Default layout; separate `output-path`s don't interfere** — `utils/constants.py:64`, `action_inputs.py:109`,
      `main.py:59`; clearing only `<mode>/`: `utils/artifact.py:337`.
      Tests: `tests/test_main.py:272`, `tests/test_main.py:297`.
- [x] **Bad `project-id` or repository entry fails at start with `INVALID_CONFIGURATION`, no file; `project_id` on
      every output** — `action_inputs.py:93-106` (`re.fullmatch(PROJECT_ID_PATTERN, …)` at `:102`),
      `utils/utils.py:103`, `action_inputs.py:187-212`, run before any mode at `main.py:54-56`; written at
      `utils/artifact.py:275`.
      Tests: `tests/test_main.py:356`, `:375`, `:272`.
- [x] **No token, network blocked** — no `requests` and no token read in active code.
      Test: `tests/test_main.py:400` (patches `socket.socket.connect` / `connect_ex`).
- [x] **Permalinks on `github.com` by default and on `ghe.example`; `NO_SOURCE_URL` outside git; the grep matches
      only `utils/github_urls.py`** — `utils/github_urls.py:27-54`, `utils/artifact.py:95-114`,
      `utils/artifact.py:169`.
      Tests: `tests/doc_source/test_collector.py:269`, `:294`, `:346`; `tests/ui_tests/test_collector.py:175`,
      `:194`, `:211`; `tests/utils/test_artifact.py:78`.
- [x] **Per-source failures** — `utils/feature_file_discovery.py:34`, `utils/artifact.py:208-246`,
      `utils/artifact.py:344`. Tests:
  - missing second source, exit ≠ 0, no file: `tests/test_main.py:456`
  - `allow-partial` writes the first source, one warning, `sources_failed: 1`: `tests/test_main.py:478`
  - all sources missing with `allow-partial` fails: `tests/test_main.py:505`
  - empty source gives `EMPTY_SOURCE`: `tests/test_main.py:536`
- [x] **CI and docs on the new layout; `workflows/README.md` gone; the four inputs exist and are documented** —
      `.github/workflows/integration_test.yml:60,81,91,104`, `action.yml:5-23,107-110`, `README.md:128-132,185`,
      `doc_source/README.md:90-92`, `ui_tests/README.md:78-80`.
- [x] **`make qa` green** — 239 passed, coverage 99.04 %, Pylint 9.99, mypy clean, Black/ruff clean, R12 checks pass.

## Release Notes
- **Breaking:** artifacts move to `<output-path>/<mode>/<artifact>.json`. The default is now
  `./output/collector-gh/doc-source/doc-source.json` and `./output/collector-gh/ui-tests/ui-tests.json`, where it
  used to be `./output/<mode>/…`. A run clears only its own `<output-path>/<mode>/` directory.
- **Breaking:** new required input `project-id`, written to every artifact's `metadata.source.project_id`. A missing
  or malformed value fails the run at start with `INVALID_CONFIGURATION`.
- **Breaking:** a malformed `doc-source-repositories` / `ui-tests-repositories` entry now fails the run at start
  with `INVALID_CONFIGURATION`, naming the entry and key; it used to be skipped.
- **Breaking:** a missing configured path now fails its source with `SOURCE_UNAVAILABLE`, and with it the mode (no
  file, exit `1`); it used to be skipped with a warning.
- New input `allow-partial` (default `false`): writes without the failed sources, with one `SOURCE_UNAVAILABLE`
  warning each. It still fails if every source failed.
- A source with zero entities is reported as an `EMPTY_SOURCE` warning.
- New input `github-server-url` (default `https://github.com`). On GitHub Enterprise Server, pass
  `${{ github.server_url }}`.
- `source_ref.url` is now a commit permalink (`…/blob/<sha>/<path>`, the checkout's `HEAD`) instead of `…/blob/HEAD/…`.
- No token needed: the action calls no GitHub API, and `github-token` is optional and unused. The
  `REQUESTS_CA_BUNDLE` setup is no longer needed.
- The `doc-issues` mode stays PLANNED and disabled; `doc-issues: true` fails the run at start.

## Related
Closes #126

🤖 Generated with [Claude Code](https://claude.com/claude-code)
