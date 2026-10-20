<!-- What problem does it solve or what feature does it add? -->
## Overview

`living-doc-utilities` `0.7.0` gives every contract warning an optional `source_url`: the permalink of the file its
line is in, at the collected commit. `authoring` never knows the file, so the collector fills it. Until now, a reader
could link a warning only through its entity's `source_ref.url`. That is the wrong file for a cross-reference page's
warnings, and there is no URL at all for a file that never gets a `source_ref`.

- **Pin.** `requirements.txt` pins `living-doc-utilities==0.7.0`; the runtime-requirements test asserts it. `0.7.0`
  removes no name this repository imports.
- **Golden corpus.** Re-copied from tag `v0.7.0` with no file changes: the blobs equal `utilities`' at that tag. The
  corpus README names the tag and its commit, and the golden test's docstring names the tag.
- **One URL computation.** `utils/artifact.py::file_url` turns `(repository, file)` into the file's blob permalink at
  its checkout's HEAD commit, or `None` outside a checkout or without a resolvable HEAD. `build_source_ref` uses it for
  `source_ref.url`, and every warning that gets a `path` uses it for `source_url`. The URL takes the path from the
  repository root, never the scan-root-relative `path`.
- **Every place that sets `path`** now sets `source_url` too:
  - `with_path` and `with_entity_paths` take the URL;
  - the direct warnings pass `source_url=`;
  - a cross-reference page carries its own URL with it, so its parser warnings and its `UNRESOLVED_RELATION` name
    the page's file, not the Feature's.
  - `NO_SOURCE_URL` keeps none, by definition.
- **Docs.** `doc_source/README.md` and `ui_tests/README.md` state `source_url` beside `path`. `docs/action.md` says a
  `NO_SOURCE_URL` file's warnings carry none. It also no longer says `github-server-url` builds only `source_ref.url`.

The venv step's pip variables, the package version in `pyproject.toml` and the action inputs are unchanged.

<!-- Summarize the key changes for release notes. -->
## Release Notes
- Pins `living-doc-utilities` `0.7.0`.
- Every warning with a `path` carries `source_url`, its file's permalink at the collected commit; none for a file outside a git checkout or without a resolvable commit.

<!-- Add attached issue that this PR solves. -->
## Related
Closes #139

## Framework

Inside the frame ([`living-doc` principles, The frame](https://github.com/AbsaOSS/living-doc/blob/master/docs/introduction/principles.md#the-frame)).
`source_url` is provenance the collector records (F2): which file it read, at which commit. Nothing is interpreted
or computed from the content. The field belongs to the `utilities` model (F5, F7); this repository fills it and
mirrors nothing.

## Acceptance criteria

| # | Criterion | Met by |
|---|---|---|
| 1 | Pin `0.7.0`, asserted by the runtime-requirements test; the corpus README names `v0.7.0` and its commit; the golden test's docstring names `v0.7.0` | `requirements.txt:4`; `tests/test_runtime_requirements.py:54`; `tests/fixtures/golden/README.md:3-4`; `tests/doc_source/test_golden_entities.py:17` |
| 2 | Every warning with a `path` carries its file's `source_url`, at every site, from the same computation as `source_ref.url`; none outside a checkout or without a resolvable HEAD (tested) | `utils/artifact.py:139` (`file_url`), used by `build_source_ref` at `:182` and `:202`; `NO_SOURCE_URL` keeps none (`:194`); `with_path` `:212`; `with_entity_paths` `:226`; `doc_source/collector.py:245`, `:253`, `:272-273`, `:285`, `:328-330`, `:350`; `ui_tests/collector.py:209`, `:228`. Tests: `tests/utils/test_artifact.py:135`, `:149`, `:154`; `tests/doc_source/test_collector.py:446`; `tests/ui_tests/test_collector.py:235`, `:294`, `:316`, `:493` |
| 3 | A cross-reference page's warnings carry the page's URL, not its Feature's; a file without an entity id and a duplicate-id file carry their own URL (tested) | `doc_source/collector.py:88`, `:328-330`, `:340`, `:350`; tests `tests/doc_source/test_collector.py:398`, `:424` |
| 4 | Both mode READMEs name `source_url` beside `path`, once each | `doc_source/README.md:111-112`; `ui_tests/README.md:91-92` |
| 5 | The venv step, the package version and the action inputs are untouched | `git diff master -- action.yml pyproject.toml` is empty |
| 6 | No planning id in the diff or in this body | A grep of the diff's added lines for planning and decision ids finds none; the comment lines this PR rewrites dropped theirs |
| 7 | `make qa` green | 546 passed, 2 skipped; coverage 98.96%; Pylint 9.99; mypy, Black, ruff clean |
| 8 | The body carries `## Framework` | above |

🤖 Generated with [Claude Code](https://claude.com/claude-code)
