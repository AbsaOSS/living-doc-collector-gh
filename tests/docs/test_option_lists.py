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

from tests.docs.pages import APPROVED_PAGES, REPO_ROOT, action_yml, read_page, section, table_rows, unfenced_lines

ACTION_PAGE = "docs/action.md"
_TICKED_RE = re.compile(r"`([^`\s]+)`")
_CONSTANT_RE = re.compile(r"^[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+$")
_NAME_RE = re.compile(r"^[a-z]+(?:-[a-z]+)+$")
_NO_DEFAULT = "—"
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


def declared_inputs() -> list[tuple[str, str, str]]:
    """`(name, required, default)` per input of `action.yml`, in its order."""
    inputs: dict[str, dict[str, Any]] = action_yml()["inputs"]
    return [
        (
            name,
            "yes" if spec.get("required") else "no",
            str(spec["default"]) if "default" in spec else _NO_DEFAULT,
        )
        for name, spec in inputs.items()
    ]


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


def test_the_readme_overview_names_every_input_and_output():
    """README § Inputs and outputs names every input and output, and no name `action.yml` does not declare."""
    names = {
        token for line in section(read_page("README.md"), "Inputs and outputs") for token in _TICKED_RE.findall(line)
    }
    declared = set(action_yml()["inputs"]) | set(action_yml()["outputs"])
    assert declared - names == set(), "README § Inputs and outputs misses these"
    assert {name for name in names if _NAME_RE.match(name)} - declared == set(), "README names undeclared inputs"


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
    """Every upper-case name a page ticks that is neither a registered code nor a name the repository's code uses;
    in an `## Errors` chapter, every one must be a registered code."""
    problems: list[str] = []
    chapter = ""
    for line in unfenced_lines(text):
        if line.startswith("## "):
            chapter = line[3:].strip()
            continue
        for token in _TICKED_RE.findall(line):
            name = token.strip("[]*")
            if not _CONSTANT_RE.match(name) or name in ALL_CODES:
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
