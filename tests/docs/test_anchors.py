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

"""`path::symbol` anchors resolve to real code, never a line number (DEVELOPER.md, "Writing documentation", Anchors)."""

import ast
import os
import re
from pathlib import Path
from typing import Optional

import pytest

from tests.docs.pages import (
    ANCHOR_PATTERN,
    ANCHOR_RE,
    APPROVED_PAGES,
    FILE_TYPES,
    REPO_ROOT,
    read_page,
    unfenced_lines,
)

_LINE_NUMBER_RE = re.compile(
    rf"(?:\.(?:{FILE_TYPES})|Makefile|\.pylintrc|\.coveragerc)`?(?::L?\d+|#L\d+|,?\s+lines?\s+\d+(?:-\d+)?\b)"
)
_LIST_ITEM_RE = re.compile(r"^(?:[-*+]|\d{1,9}[.)])[ \t]")
# The components a rule may name instead of an anchor (DEVELOPER.md, "Writing documentation", Anchors).
COMPONENTS = ("utilities", "toolkit")
_DESTINATION = rf"(?:`{ANCHOR_PATTERN}`|{ANCHOR_PATTERN}|\[[^\]]*\]\([^)\s]+\)|(?:{'|'.join(COMPONENTS)})\b)"
_TRAILING_DESTINATIONS_RE = re.compile(rf"→\s*{_DESTINATION}(?:\s*(?:,|\band\b)\s*{_DESTINATION})*\s*$")
_LEAD_IN_DESTINATION_RE = re.compile(rf"→\s*{_DESTINATION}")


def _resolve(path: str) -> Optional[Path]:
    """An anchor path, relative to the repository root; never a `..`-laden path that escapes the repository, however
    it resolves on disk."""
    repo_root = REPO_ROOT.resolve()
    resolved = (REPO_ROOT / path).resolve()
    if resolved.is_file() and resolved.is_relative_to(repo_root):
        return resolved
    return None


def _bound_name(node: ast.stmt) -> Optional[str]:
    """The single name `node` binds at its own nesting level, or `None` when it binds none."""
    if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
        return node.name
    if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
        return node.targets[0].id
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        return node.target.id
    return None


def _first_undefined_part(body: list[ast.stmt], parts: list[str]) -> Optional[str]:
    """The first dotted `parts` segment with no definition nested at its position in `body`, so `Class.member`
    only resolves when `member` is defined inside `Class` - not merely present anywhere in the file."""
    for index, part in enumerate(parts):
        node = next((candidate for candidate in body if _bound_name(candidate) == part), None)
        if node is None:
            return ".".join(parts[index:])
        body = getattr(node, "body", [])
    return None


def _anchor_problem(path: str, symbol: str) -> Optional[str]:
    """Why `path::symbol` does not resolve, or `None` when it does."""
    resolved = _resolve(path)
    if resolved is None:
        return f"no file '{path}'"
    text = resolved.read_text(encoding="utf-8")
    if resolved.suffix == ".py":
        missing = _first_undefined_part(ast.parse(text).body, symbol.split("."))
        return f"'{path}' defines no {missing!r}" if missing else None
    return None if symbol in text else f"'{path}' does not contain {symbol!r}"


def anchors(text: str) -> list[tuple[str, str]]:
    """Every `path::symbol` of a page, ticked or not; a trailing `()` or pytest `[id]` is dropped from the symbol."""
    return [(anchor_m.group("path"), anchor_m.group("symbol")) for anchor_m in ANCHOR_RE.finditer(text)]


def _anchors(page: str) -> list[tuple[str, str]]:
    return anchors(read_page(page))


@pytest.mark.parametrize("page", sorted(APPROVED_PAGES))
def test_every_anchor_resolves(page):
    """Each `path::symbol` on the page names an existing file that defines, or contains, the symbol."""
    problems = [
        f"{page}: `{path}::{symbol}`: {problem}"
        for path, symbol in _anchors(page)
        if (problem := _anchor_problem(path, symbol)) is not None
    ]
    assert problems == []


@pytest.mark.parametrize("page", sorted(APPROVED_PAGES))
def test_no_anchor_uses_a_line_number(page):
    """No page points at code by line number (`main.py:42`, `#L42`, prose "file.py lines 12-34"); line numbers
    drift."""
    assert _LINE_NUMBER_RE.findall(read_page(page)) == []


def test_the_detail_pages_carry_anchors():
    """The anchor check has something to check: every depth-2 page carries anchors."""
    assert [page for page, depth in APPROVED_PAGES.items() if depth > 1 and not _anchors(page)] == []


def test_anchor_resolution_rejects_a_missing_file_and_a_missing_symbol():
    """A planted wrong path or wrong symbol is reported; a dotted member is checked part by part."""
    assert _anchor_problem("utils/artifact.py", "store_artifact") is None
    assert _anchor_problem("action_inputs.py", "ActionInputs._validate") is None
    assert _anchor_problem("utils/nowhere.py", "x") == "no file 'utils/nowhere.py'"
    assert (
        _anchor_problem("utils/artifact.py", "store_everything") == "'utils/artifact.py' defines no 'store_everything'"
    )
    assert _anchor_problem("Makefile", "no-such-target") == "'Makefile' does not contain 'no-such-target'"


def test_anchor_resolution_rejects_a_member_that_belongs_to_a_different_class():
    """`Class.member` only resolves when `member` is nested in `Class`, not merely present elsewhere in the file."""
    assert _anchor_problem("utils/artifact.py", "SourceRepository.store_artifact") == (
        "'utils/artifact.py' defines no 'store_artifact'"
    )


def test_anchor_resolution_rejects_a_path_that_escapes_the_repository(tmp_path):
    """A `..`-laden path that exists on disk is still rejected when it resolves outside the repository."""
    outside = tmp_path / "escaped.py"
    outside.write_text("ESCAPED = 1\n", encoding="utf-8")
    escaping = os.path.relpath(outside, REPO_ROOT)
    assert _anchor_problem(escaping, "ESCAPED") == f"no file '{escaping}'"


def test_a_line_number_anchor_is_found():
    """A planted `main.py:42` or `#L42` pointer is caught."""
    assert _LINE_NUMBER_RE.findall("see `main.py:42` and [run](main.py#L42)") == [".py:42", ".py#L42"]


@pytest.mark.parametrize(
    "text",
    [
        "`main.py` lines 12-34",
        "main.py, line 42",
        "main.py:L42",
        "`requirements.txt:3`",
        "[pin](requirements.txt#L3)",
        "[qa](Makefile#L12)",
        "`.pylintrc:10`",
    ],
)
def test_every_line_number_form_is_found(text):
    """A line number after a ticked file, after a comma, as `:L42`, or into a non-Python file is caught too."""
    assert len(_LINE_NUMBER_RE.findall(text)) == 1


def test_an_anchor_into_a_non_python_file_is_no_line_number():
    """`test.yml::3.14` and `Makefile::qa` name a text, not a line."""
    assert _LINE_NUMBER_RE.findall("`.github/workflows/test.yml::3.14` and `Makefile::qa`") == []


@pytest.mark.parametrize(
    "text, found",
    [
        ("→ `utils/artifact.py::store_artifacts()`", ("utils/artifact.py", "store_artifacts")),
        ("→ utils/artifact.py::store_artifacts", ("utils/artifact.py", "store_artifacts")),
        ("→ `tests/test_main.py::test_no_such_case[param]`", ("tests/test_main.py", "test_no_such_case")),
        ("→ `.coveragerc::fail_under`", (".coveragerc", "fail_under")),
    ],
    ids=["call-parentheses", "unticked", "pytest-id", "dotfile"],
)
def test_every_anchor_form_is_found_so_a_wrong_one_is_reported(text, found):
    """An anchor with `()`, a pytest id, no ticks, or into a dotfile is still read, so its resolution is checked."""
    assert anchors(text) == [found]
    assert _anchor_problem(*found) is not None


def test_a_placeholder_is_no_anchor():
    """The rule's own placeholders, `path::symbol` and `tests/<path>.py::test_name`, are not read as anchors."""
    assert anchors("`path::symbol`, `tests/<path>.py::test_name`") == []


def unplaced_list_items(page: str, text: str) -> list[str]:
    """Top-level list items that do not end in `→` and their destinations - anchors, links or components - and
    whose lead-in carries none either. A lead-in covers only the list right after it, not one past a table.
    `Contents` is routing, not facts."""
    problems: list[str] = []
    chapter, lead_in, previous = "", "", "blank"
    for line in unfenced_lines(text):
        stripped = line.strip()
        if not stripped:
            previous = "blank"
            continue
        if stripped.startswith("#"):
            chapter = stripped.lstrip("#").strip() if stripped.startswith("## ") else chapter
            lead_in, previous = "", "blank"
            continue
        if stripped.startswith("|"):
            lead_in, previous = "", "blank"  # a table ends the reach of the lead-in above it
            continue
        if line.startswith((" ", "\t")):
            continue  # a sub-item (`Why:`, detail)
        if _LIST_ITEM_RE.match(line) is None:
            lead_in = f"{lead_in} {stripped}" if previous == "text" else stripped
            previous = "text"
            continue
        previous = "item"
        if chapter == "Contents":
            continue
        if _TRAILING_DESTINATIONS_RE.search(stripped) or _LEAD_IN_DESTINATION_RE.search(lead_in):
            continue
        problems.append(f"{page}: '{stripped[:80]}' ends in no anchor, component or link, and its lead-in none either")
    return problems


@pytest.mark.parametrize("page", sorted(page for page, depth in APPROVED_PAGES.items() if depth > 1))
def test_every_list_item_says_where_it_is_realised(page):
    """Each depth-2 list item ends in `→` and a destination; a lead-in's `→` destination covers its items."""
    assert unplaced_list_items(page, read_page(page)) == []


def test_an_unplaced_list_item_is_reported_and_a_lead_in_anchor_covers_its_items():
    """A bare fact fails, as does a trailing arrow with no destination; an anchored lead-in covers its items."""
    bare = "## Facts\n\n- a fact with no home\n"
    dangling_arrow = "## Facts\n\n- a fact with a dangling arrow →\n"
    covered = "## Facts\n\nThe cases → `utils/artifact.py::collect_sources`:\n\n- a fact with no home\n"
    assert unplaced_list_items("docs/x.md", bare) == [
        "docs/x.md: '- a fact with no home' ends in no anchor, component or link, and its lead-in none either"
    ]
    assert unplaced_list_items("docs/x.md", dangling_arrow) == [
        "docs/x.md: '- a fact with a dangling arrow →' ends in no anchor, component or link, and its lead-in none "
        "either"
    ]
    assert unplaced_list_items("docs/x.md", covered) == []


@pytest.mark.parametrize(
    "item",
    [
        "- a fact → somewhere",
        "- collect → normalize → generate is deterministic",
        "- the flow `a → b` is fixed",
        "- see [x](y.md) for a fact with no home",
        "- a fact → `utils/artifact.py::store_artifact` and more text",
    ],
)
def test_an_item_that_does_not_end_in_a_destination_is_reported(item):
    """An arrow mid-sentence, an arrow to no destination, or a link mid-sentence does not say where it is realised."""
    assert len(unplaced_list_items("docs/x.md", f"## Facts\n\n{item}\n")) == 1


@pytest.mark.parametrize(
    "item",
    [
        "- a fact → `utils/artifact.py::store_artifact`",
        "- a fact → utilities",
        "- a fact → [Errors](../docs/action.md#errors), [Inputs](../docs/action.md#inputs)",
        "- a fact → `main.py::run` and `utils/artifact.py::store_artifact`",
    ],
)
def test_an_item_that_ends_in_destinations_passes(item):
    """An anchor, a component, or several links or anchors joined by `,` or `and` end an item."""
    assert unplaced_list_items("docs/x.md", f"## Facts\n\n{item}\n") == []


def test_a_lead_in_does_not_cover_a_list_after_a_table():
    """A lead-in's `→` covers the list right after it; past a table, each item needs its own destination."""
    page = "## Facts\n\nThe rows → `utils/artifact.py::collect_sources`:\n\n| a | b |\n|---|---|\n\n- a fact with no home\n"
    assert unplaced_list_items("docs/x.md", page) == [
        "docs/x.md: '- a fact with no home' ends in no anchor, component or link, and its lead-in none either"
    ]


@pytest.mark.parametrize("item", ["+ a fact with no home", "1) a fact with no home", "-\ta fact with no home"])
def test_every_list_marker_is_read_as_a_list_item(item):
    """`+`, `1)` and a tab after the marker start a list item on GitHub, so the item is checked."""
    assert len(unplaced_list_items("docs/x.md", f"## Facts\n\n{item}\n")) == 1
