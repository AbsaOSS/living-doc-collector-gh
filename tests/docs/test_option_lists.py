#
# Copyright 2026 ABSA Group Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""Option lists are complete against the code: the inputs and outputs equal `action.yml`, every code is registered."""

import re
import subprocess
from typing import Any

import pytest
from living_doc_utilities.contracts.codes import ALL_CODES

from tests.docs.pages import (
    ANCHOR_RE,
    APPROVED_PAGES,
    REPO_ROOT,
    action_yml,
    read_page,
    section,
    table_rows,
    unfenced_lines,
)

ACTION_PAGE = "docs/action.md"
_TICKED_RE = re.compile(r"`([^`\s]+)`")
_CONSTANT_WORD_RE = re.compile(r"(?<![\w$])[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+\b")
_LINK_TARGET_RE = re.compile(r"\]\([^)\s]*\)")
_NAME_RE = re.compile(r"^[a-z]+(?:-[a-z]+)*$")
_HYPHENATED_NAME_RE = re.compile(r"^[a-z]+(?:-[a-z]+)+$")
_SUBJECT_RE = re.compile(r"^- ((?:`[^`\s]+`(?:,\s*)?)+)")
_NO_DEFAULT = "—"
_PLANNED = "PLANNED"
# Upper-case names a page may tick that belong to another tool, not to this repository's code: pip's settings.
EXTERNAL_NAMES = {"PIP_INDEX_URL", "PIP_FIND_LINKS"}
DOCUMENTED_TEST_NAMES = {"NOT_PRODUCED"}


def _cell(cell: str) -> str:
    """A table cell without its code ticks; an empty-string default is written `''`."""
    text = cell.strip()
    return "" if text == "`''`" else text.strip("`")


def documented_options(lines: list[str]) -> list[tuple[str, str, str]]:
    """`(name, required, default)` per row of the first table in `lines`."""
    return [(_cell(row[0]), row[1], _cell(row[2])) for row in table_rows(lines)]


def _action_value(value: Any) -> str:
    """An `action.yml` default as the runner passes it to the step: a YAML boolean as `true` / `false`, no value as
    an empty string."""
    if isinstance(value, bool):
        return "true" if value else "false"
    return "" if value is None else str(value)


def declared_inputs(inputs: dict[str, dict[str, Any]] | None = None) -> list[tuple[str, str, str]]:
    """`(name, required, default)` per input of `action.yml` (or of `inputs`), in its order."""
    inputs = action_yml()["inputs"] if inputs is None else inputs
    return [
        (
            name,
            "yes" if spec.get("required") is True else "no",
            _action_value(spec["default"]) if "default" in spec else _NO_DEFAULT,
        )
        for name, spec in inputs.items()
    ]


def planned_problems(page: str, rows: list[list[str]], inputs: dict[str, dict[str, Any]]) -> list[str]:
    """Each input whose meaning on the page is not marked `PLANNED` exactly when its `action.yml` description is."""
    meanings = {_cell(row[0]): row[3] for row in rows if len(row) > 3}
    problems = []
    for name, spec in inputs.items():
        planned = str(spec.get("description", "")).startswith(_PLANNED)
        if name in meanings and meanings[name].startswith(_PLANNED) != planned:
            state = "PLANNED" if planned else "not PLANNED"
            problems.append(f"{page} § Inputs: `{name}` is {state} in `action.yml`; its meaning must say so first")
    return problems


def table_problems(page: str, chapter: str, documented: list, declared: list) -> list[str]:
    """Each row the page's table lacks or holds beyond `action.yml`, and each row that disagrees with it."""
    documented_names = [row[0] for row in documented]
    declared_names = [row[0] for row in declared]
    problems = [f"{page} § {chapter}: `{name}` is missing" for name in declared_names if name not in documented_names]
    problems += [
        f"{page} § {chapter}: `{name}` is not in `action.yml`"
        for name in documented_names
        if name not in declared_names
    ]
    by_name = {row[0]: row for row in documented}
    problems += [
        f"{page} § {chapter}: `{row[0]}` is documented as {by_name[row[0]]!r}, `action.yml` says {row!r}"
        for row in declared
        if row[0] in by_name and by_name[row[0]] != row
    ]
    if not problems and documented_names != declared_names:
        problems.append(f"{page} § {chapter}: the rows are not in `action.yml` order")
    return problems


def test_the_input_table_equals_action_yml():
    """`docs/action.md` § Inputs lists every input `action.yml` declares, in its order, with its required flag and
    default, and nothing else."""
    documented = documented_options(section(read_page(ACTION_PAGE), "Inputs"))
    assert table_problems(ACTION_PAGE, "Inputs", documented, declared_inputs()) == []


def test_the_output_table_equals_action_yml():
    """`docs/action.md` § Outputs lists every output `action.yml` declares, and nothing else."""
    documented = [(_cell(row[0]),) for row in table_rows(section(read_page(ACTION_PAGE), "Outputs"))]
    declared = [(name,) for name in action_yml()["outputs"]]
    assert table_problems(ACTION_PAGE, "Outputs", documented, declared) == []


def test_the_planned_inputs_are_marked_planned():
    """`docs/action.md` § Inputs starts the meaning of every PLANNED input, and only those, with `PLANNED`."""
    rows = table_rows(section(read_page(ACTION_PAGE), "Inputs"))
    assert planned_problems(ACTION_PAGE, rows, action_yml()["inputs"]) == []


def test_planted_unmarked_planned_input_is_reported():
    """A PLANNED input whose meaning drops the mark fails, as does an available input marked PLANNED."""
    inputs = {"doc-issues-repositories": {"description": "PLANNED - not read."}, "doc-source": {"description": "On."}}
    rows = [
        ["`doc-issues-repositories`", "no", "`[]`", "The Documentation Issues mode's sources, a JSON array"],
        ["`doc-source`", "no", "`false`", "PLANNED: runs the mode"],
    ]
    assert planned_problems("docs/x.md", rows, inputs) == [
        "docs/x.md § Inputs: `doc-issues-repositories` is PLANNED in `action.yml`; its meaning must say so first",
        "docs/x.md § Inputs: `doc-source` is not PLANNED in `action.yml`; its meaning must say so first",
    ]


def test_an_action_yml_default_is_read_as_the_runner_passes_it():
    """An unquoted YAML boolean default is the string `true` / `false`, an empty one is `''`, and only a YAML `true`
    makes an input required."""
    inputs = {"a": {"default": False}, "b": {"default": None}, "c": {"required": "false", "default": "x"}}
    assert declared_inputs(inputs) == [("a", "no", "false"), ("b", "no", ""), ("c", "no", "x")]


def readme_overview_problems(lines: list[str], inputs: list[str], outputs: list[str]) -> list[str]:
    """Each input missing from the list items, each output not named after the list, and each undeclared name."""
    in_items = {token for line in lines if line.startswith("- ") for token in _TICKED_RE.findall(line)}
    elsewhere = {token for line in lines if not line.startswith("- ") for token in _TICKED_RE.findall(line)}
    problems = [
        f"README § Inputs and outputs: input `{name}` is in no list item" for name in inputs if name not in in_items
    ]
    problems += [
        f"README § Inputs and outputs: output `{name}` is not named outside the input list"
        for name in outputs
        if name not in elsewhere
    ]
    # A hyphenated name is an input wherever it is ticked; a one-word one only as an item's subject - the ticked names
    # it opens with - since a meaning may tick a value such as `true`, even before its `:`.
    subjects = {
        token
        for line in lines
        if (subject_m := _SUBJECT_RE.match(line))
        for token in _TICKED_RE.findall(subject_m.group(1))
    }
    named = {name for name in in_items | elsewhere if _HYPHENATED_NAME_RE.match(name)}
    named |= {name for name in subjects if _NAME_RE.match(name)}
    undeclared = named - set(inputs) - set(outputs)
    problems += [f"README § Inputs and outputs: `{name}` is not in `action.yml`" for name in sorted(undeclared)]
    return problems


def test_a_value_ticked_in_a_meaning_is_no_input_name():
    """`true`, `false` or `json` in an item's meaning are values, not undeclared inputs."""
    lines = [
        "- `allow-partial`: `true` writes without a failed source; `false` fails; the sources are `json`",
        "- `verbose-logging` (default `false`): debug logging",
        "- `doc-source` - `true` runs the mode",
    ]
    assert readme_overview_problems(lines, ["allow-partial", "verbose-logging", "doc-source"], []) == []
    assert readme_overview_problems(["- `verbose` - an alias"], [], []) == [
        "README § Inputs and outputs: `verbose` is not in `action.yml`"
    ]


def test_the_readme_overview_names_every_input_and_output():
    """README § Inputs and outputs gives every input a list item, names the output after the list, and names
    nothing `action.yml` does not declare."""
    lines = section(read_page("README.md"), "Inputs and outputs")
    assert readme_overview_problems(lines, list(action_yml()["inputs"]), list(action_yml()["outputs"])) == []


def test_planted_readme_overview_gaps_are_reported():
    """A dropped output paragraph, an undeclared one-word name, and inputs named only in a sentence each fail."""
    lines = [
        "Every input at a glance:",
        "- `project-id` (required): the project",
        "- `verbose`: an alias",
        "Not covered here: `allow-partial`.",
    ]
    assert readme_overview_problems(lines, ["project-id", "allow-partial"], ["output-path"]) == [
        "README § Inputs and outputs: input `allow-partial` is in no list item",
        "README § Inputs and outputs: output `output-path` is not named outside the input list",
        "README § Inputs and outputs: `verbose` is not in `action.yml`",
    ]


def test_planted_missing_or_wrong_input_row_is_reported():
    """A table that drops an input, adds one, or gives a wrong default fails, naming the input."""
    declared = [("project-id", "yes", _NO_DEFAULT), ("output-path", "no", "./output/collector-gh")]
    documented = [("project-id", "yes", _NO_DEFAULT), ("output-dir", "no", "./output/collector-gh")]
    assert table_problems("docs/x.md", "Inputs", documented, declared) == [
        "docs/x.md § Inputs: `output-path` is missing",
        "docs/x.md § Inputs: `output-dir` is not in `action.yml`",
    ]
    wrong_default = [("project-id", "yes", _NO_DEFAULT), ("output-path", "no", "./output")]
    assert table_problems("docs/x.md", "Inputs", wrong_default, declared) == [
        "docs/x.md § Inputs: `output-path` is documented as ('output-path', 'no', './output'), `action.yml` says "
        "('output-path', 'no', './output/collector-gh')"
    ]


def test_the_table_reader_unticks_cells_and_reads_an_empty_default():
    """A ticked name and an empty-string default read as `action.yml` writes them."""
    lines = ["| Input | Required | Default | Meaning |", "|---|---|---|---|", "| `github-token` | no | `''` | unused |"]
    assert documented_options(lines) == [("github-token", "no", "")]


def _code_problems(page: str, text: str, known: set[str]) -> list[str]:
    """Every upper-case name a page writes - ticked, bold or bare - that is neither a registered code nor a name the
    repository's code uses; in an `## Errors` chapter, every one must be a registered code. Link targets and
    `path::symbol` anchors are left out: the anchor check resolves those."""
    problems: list[str] = []
    chapter = ""
    for line in unfenced_lines(text):
        if line.startswith("## "):
            chapter = line[3:].strip()
            continue
        for name in _CONSTANT_WORD_RE.findall(ANCHOR_RE.sub("", _LINK_TARGET_RE.sub("]", line))):
            if name in ALL_CODES:
                continue
            if chapter == "Errors":
                problems.append(f"{page} § Errors: `{name}` is not a registered code")
            elif name not in known and name not in EXTERNAL_NAMES and name not in DOCUMENTED_TEST_NAMES:
                problems.append(f"{page}: `{name}` is neither a registered code nor a name in the repository's code")
    return problems


def _names_in_code() -> set[str]:
    """Upper-case names in non-test, non-Markdown files, plus the external `ALL_CODES` registry."""
    listed = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", ":!*.md", ":!tests/**"],
        cwd=REPO_ROOT,
        capture_output=True,
        check=True,
        text=True,
    ).stdout.splitlines()
    names: set[str] = {"ALL_CODES"}
    for path in listed:
        try:
            text = (REPO_ROOT / path).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        names.update(re.findall(r"\b[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+\b", text))
    return names


def test_code_name_inventory_excludes_planted_test_names() -> None:
    names = _names_in_code()
    assert "SOURCE_UNAVAILABEL" not in names
    assert "NOT_PRODUCED" not in names
    assert "ALL_CODES" in names


@pytest.mark.parametrize("page", sorted(APPROVED_PAGES))
def test_every_code_a_page_names_is_registered(page):
    """A code on a page is in `ALL_CODES`; any other upper-case name exists in the repository's code."""
    assert _code_problems(page, read_page(page), _names_in_code()) == []


def test_planted_unknown_code_is_reported():
    """A misspelt code fails in an `## Errors` chapter and elsewhere; a real env variable passes outside one."""
    text = "## Usage\n\n`GITHUB_OUTPUT`, `SOURCE_UNAVAILABEL`\n\n## Errors\n\n| x | `EMPTY_SOURCES` |\n"
    assert _code_problems("docs/x.md", text, {"GITHUB_OUTPUT"}) == [
        "docs/x.md: `SOURCE_UNAVAILABEL` is neither a registered code nor a name in the repository's code",
        "docs/x.md § Errors: `EMPTY_SOURCES` is not a registered code",
    ]


@pytest.mark.parametrize(
    "cell",
    ["SOURCE_UNAVAILABEL (error)", "**SOURCE_UNAVAILABEL**", "`SOURCE_UNAVAILABEL (error)`", "`SOURCE_UNAVAILABEL:`"],
    ids=["bare", "bold", "code-span-with-space", "code-span-with-colon"],
)
def test_planted_unknown_code_in_any_markup_is_reported(cell):
    """A misspelt code in an Errors table is caught bare, in bold, or in a code span with more text."""
    text = f"## Errors\n\n| Situation | Code |\n|---|---|\n| x | {cell} |\n"
    assert _code_problems("docs/x.md", text, set()) == [
        "docs/x.md § Errors: `SOURCE_UNAVAILABEL` is not a registered code"
    ]


def test_an_anchor_or_link_target_is_not_read_as_a_code():
    """`main.py::DOC_ISSUES_PLANNED_MESSAGE` is an anchor, and a URL's upper-case words are a link target."""
    text = "## Errors\n\n| x | `INVALID_CONFIGURATION` | `main.py::DOC_ISSUES_PLANNED_MESSAGE` |\n\n[x](https://e.org/A_B)\n"
    assert _code_problems("docs/x.md", text, set()) == []
