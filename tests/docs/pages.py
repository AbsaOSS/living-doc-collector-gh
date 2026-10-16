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

"""
The approved documentation pages and the checks the page rules need (DEVELOPER.md, "Writing documentation").
Each check takes page text and returns one message per problem, each naming the page, so a test can also
plant a violation in a synthetic page and see it reported.
"""

import re
import subprocess
from functools import lru_cache
from pathlib import Path, PurePosixPath
from typing import Any, NamedTuple

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]

# Every shipped page and its depth; a new page is added here and linked from README.md.
APPROVED_PAGES: dict[str, int] = {
    "README.md": 1,
    "DEVELOPER.md": 1,
    "CONTRIBUTING.md": 1,
    "SPEC.md": 1,
    "docs/action.md": 2,
    "doc_source/README.md": 2,
    "ui_tests/README.md": 2,
    "doc_issues/README.md": 2,
}

# Tracked Markdown that is not a page: the agent board, the review rules and the test fixtures.
NOT_PAGES = (".claude/", ".github/", "tests/fixtures/")

# A fence may sit in a list item or a blockquote, so `>` markers, list markers and indentation may precede it.
_LIST_MARKER = r"(?:[-*+]|\d{1,9}[.)])"
_CONTAINER_PREFIX = rf"(?:[ \t]*(?:>|{_LIST_MARKER}(?=[ \t])))*[ \t]*"
_FENCE_RE = re.compile(rf"^(?P<prefix>{_CONTAINER_PREFIX})(?P<fence>`{{3,}}|~{{3,}})(?P<info>.*)$")
_FENCE_RUN_RE = re.compile(r"`{3,}|~{3,}")
_QUOTES_RE = re.compile(r"^(?:[ \t]*>)*")
_LIST_MARKER_RE = re.compile(_LIST_MARKER)
# A code span: an exact run of backticks closed by the same run, across line breaks but not across a blank line.
_CODE_SPAN = r"(?<!`)(?P<ticks>`+)(?:(?!\n[ \t]*\n).)+?(?<!`)(?P=ticks)(?!`)"
_CODE_SPAN_RE = re.compile(_CODE_SPAN, re.S)
# One left-to-right pass, so `<!--` inside a code span is text, not the start of a comment.
_CODE_SPAN_OR_COMMENT_RE = re.compile(rf"(?P<span>{_CODE_SPAN})|<!--.*?-->", re.S)

# The file kinds a `path::symbol` anchor may point into, and the anchor itself; `ANCHOR_PATTERN` has no groups,
# so it can be embedded. A trailing `()` or pytest `[id]` is allowed and not part of the symbol.
FILE_TYPES = "py|md|yml|yaml|toml|sh|txt|json|example|cfg|ini|feature|ts"
_ANCHOR_PATH = rf"(?:[\w.-]+/)*(?:[\w-][\w.-]*\.(?:{FILE_TYPES})|Makefile|\.[\w-][\w.-]*)"
_ANCHOR_SYMBOL = r"[\w.-]*\w"
_ANCHOR_SUFFIX = r"(?:\(\)|\[[^\]\s]*\])?"
ANCHOR_PATTERN = rf"{_ANCHOR_PATH}::{_ANCHOR_SYMBOL}{_ANCHOR_SUFFIX}"
ANCHOR_RE = re.compile(rf"(?<![\w./<>-])(?P<path>{_ANCHOR_PATH})::(?P<symbol>{_ANCHOR_SYMBOL}){_ANCHOR_SUFFIX}")


def _fence_open(line: str) -> re.Match[str] | None:
    """The opening-fence match for `line`, or `None` when it is not one: CommonMark forbids a backtick in a
    backtick fence's info string (a tilde fence's info string is unrestricted)."""
    match = _FENCE_RE.match(line)
    if match and match.group("fence")[0] == "`" and "`" in match.group("info"):
        return None
    return match


_HEADING_RE = re.compile(r"^(?P<hashes>#{1,6})\s+(?P<text>.*?)\s*#*\s*$")
_LIST_LINK_RE = re.compile(r"^[-*]\s+\[[^\]]*\]\((?P<target>[^)\s]*)\)\s*$")
_LINK_TARGET_RE = re.compile(r"\]\((?P<target>[^)\s]+)\)")


class CodeBlock(NamedTuple):
    """One fenced block: its info string (e.g. `yaml`), its code, and the non-blank line right above it."""

    info: str
    code: str
    line_above: str


class _Fence(NamedTuple):
    """An open fence: its run, its `>` depth, its column after the quotes, whether a list item or blockquote holds
    it (the block then ends where that container ends), and the prefix its code lines carry."""

    run: str
    depth: int
    column: int
    contained: bool
    indent: str


def _quotes(line: str, depth: int | None = None) -> str:
    """The `>` markers `line` opens with - at most `depth` of them, so a deeper `>` stays code - and the whitespace
    between them."""
    quotes_m = _QUOTES_RE.match(line) if depth is None else re.match(rf"^(?:[ \t]*>){{0,{depth}}}", line)
    return quotes_m.group(0) if quotes_m else ""


def _open(fence_m: re.Match[str]) -> _Fence:
    """The fence an opening-fence match starts; a list marker in its prefix counts as indentation."""
    prefix = fence_m.group("prefix")
    quotes = _quotes(prefix)
    after = _LIST_MARKER_RE.sub(lambda marker_m: " " * len(marker_m.group(0)), prefix[len(quotes) :])
    contained = bool(quotes) or after != prefix[len(quotes) :] or len(after) >= 4
    return _Fence(fence_m.group("fence"), quotes.count(">"), len(after), contained, quotes + after)


def _step(line: str, fence: _Fence) -> str:
    """`close` when `line` closes the block, `end` when the block's container ended before `line`, else `code`."""
    quotes = _quotes(line, fence.depth)
    if quotes.count(">") < fence.depth:
        return "end"
    after = line[len(quotes) :]
    lead = len(after) - len(after.lstrip(" "))
    stripped = after.strip()
    run_m = _FENCE_RUN_RE.fullmatch(stripped)
    if run_m and stripped[0] == fence.run[0] and len(stripped) >= len(fence.run) and lead <= fence.column + 3:
        return "close"
    if fence.contained and stripped and lead < fence.column:
        return "end"
    return "code"


def _code_line(line: str, fence: _Fence) -> str:
    """A line of the block without its container's prefix: the quotes, and indentation up to the fence's column."""
    if line.startswith(fence.indent):
        return line[len(fence.indent) :]
    after = line[len(_quotes(line, fence.depth)) :]
    return after[min(fence.column, len(after) - len(after.lstrip(" "))) :]


def read_page(page: str) -> str:
    """The text of an approved page, read from the repository."""
    return (REPO_ROOT / page).read_text(encoding="utf-8")


def tracked_markdown() -> set[str]:
    """Every Markdown file git tracks - `.md` or `.markdown`, in any case - that is a page, not part of the agent
    board or a test fixture."""
    listed = subprocess.run(
        ["git", "ls-files", "--", ":(icase)*.md", ":(icase)*.markdown"],
        cwd=REPO_ROOT,
        capture_output=True,
        check=True,
        text=True,
    ).stdout.splitlines()
    return {path for path in listed if not path.startswith(NOT_PAGES)}


def check_page_list(listed: set[str], approved: dict[str, int]) -> list[str]:
    """Every listed page is approved, every approved page is listed, and its path gives its depth."""
    problems = [f"{page}: unapproved page; add it to APPROVED_PAGES" for page in sorted(listed - set(approved))]
    problems += [f"{page}: approved but not tracked" for page in sorted(set(approved) - listed)]
    problems += [
        f"{page}: listed at depth {depth}, but its path gives {page_depth(page)}"
        for page, depth in approved.items()
        if page_depth(page) != depth
    ]
    return problems


@lru_cache(maxsize=1)
def action_yml() -> dict[str, Any]:
    """The parsed `action.yml`: the inputs and outputs every page must agree with."""
    return yaml.safe_load((REPO_ROOT / "action.yml").read_text(encoding="utf-8"))


def unfenced_lines(text: str) -> list[str]:
    """The page's lines outside fenced code blocks and HTML comments, so a `#` comment in a code block, or a
    commented-out heading or link, is never read as one."""
    lines: list[str] = []
    fence: _Fence | None = None
    for line in text.splitlines():
        if fence is not None:
            step = _step(line, fence)
            if step != "end":
                fence = None if step == "close" else fence
                continue
            fence = None
        fence_m = _fence_open(line)
        if fence_m:
            fence = _open(fence_m)
            continue
        lines.append(line)
    return _CODE_SPAN_OR_COMMENT_RE.sub(lambda m: m.group("span") or "", "\n".join(lines)).splitlines()


def code_blocks(text: str) -> list[CodeBlock]:
    """Every fenced block of the page, in order."""
    blocks: list[CodeBlock] = []
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        fence_m = _fence_open(lines[index])
        if fence_m is None:
            index += 1
            continue
        fence = _open(fence_m)
        above = next((line.strip() for line in reversed(lines[:index]) if line.strip()), "")
        body: list[str] = []
        index += 1
        step = "code"
        while index < len(lines) and (step := _step(lines[index], fence)) == "code":
            body.append(_code_line(lines[index], fence))
            index += 1
        blocks.append(CodeBlock(fence_m.group("info").strip(), "\n".join(body) + "\n", above))
        if step == "close":
            index += 1  # a block its container ended leaves that line to be read again
    return blocks


def all_headings(text: str) -> list[tuple[int, str]]:
    """`(level, text)` of every heading outside fenced blocks, in page order."""
    found = []
    for line in unfenced_lines(text):
        heading_m = _HEADING_RE.match(line)
        if heading_m:
            found.append((len(heading_m.group("hashes")), heading_m.group("text")))
    return found


def headings(text: str, level: int) -> list[str]:
    """The text of every heading of exactly `level` (2 for `##`) outside fenced blocks."""
    return [title for heading_level, title in all_headings(text) if heading_level == level]


def slug(heading: str) -> str:
    """The fragment GitHub gives a heading: emphasis and code markers dropped, lowercased, punctuation removed,
    each space a hyphen."""
    rendered = heading.replace("`", "").replace("**", "").lower()
    kept = "".join(char for char in rendered if char.isalnum() or char in " -_")
    return kept.replace(" ", "-")


def _unique_fragments(titles: list[str]) -> list[tuple[str, str]]:
    """`(fragment, title)` per title, GitHub's way: a candidate already used - literal or itself generated -
    gets `-1`, `-2`, ... appended until it is unused."""
    used: set[str] = set()
    fragments: list[tuple[str, str]] = []
    for title in titles:
        base = slug(title)
        candidate, suffix = base, 0
        while candidate in used:
            suffix += 1
            candidate = f"{base}-{suffix}"
        used.add(candidate)
        fragments.append((candidate, title))
    return fragments


def section(text: str, title: str) -> list[str]:
    """The lines under the `## <title>` heading, up to the next `##` heading."""
    body: list[str] = []
    inside = False
    for line in unfenced_lines(text):
        heading_m = _HEADING_RE.match(line)
        if heading_m and len(heading_m.group("hashes")) == 2:
            inside = heading_m.group("text") == title
            continue
        if inside:
            body.append(line)
    return body


def table_rows(lines: list[str]) -> list[list[str]]:
    """The body rows of the first Markdown table in `lines`, each a list of stripped cells; the header row and its
    `|---|` separator are left out."""
    rows: list[list[str]] = []
    started = False
    for line in lines:
        stripped = line.strip()
        if not stripped.startswith("|"):
            if started:
                break
            continue
        started = True
        rows.append([cell.strip() for cell in stripped.strip("|").split("|")])
    return [row for row in rows[1:] if not all(set(cell) <= set("-: ") for cell in row)]


def check_purpose_then_contents(page: str, text: str) -> list[str]:
    """The page opens with its `#` title, then `## Purpose`, then `## Contents`: no heading comes between them."""
    opening = all_headings(text)[:3]
    if opening[:1] and opening[0][0] == 1 and opening[1:] == [(2, "Purpose"), (2, "Contents")]:
        return []
    found = [f"{'#' * level} {title}" for level, title in opening]
    return [f"{page}: the page must open with '# <title>', '## Purpose', '## Contents'; found {found!r}"]


def check_contents_links(page: str, text: str) -> list[str]:
    """`Contents` links to every other `##` chapter of the page, and to nothing else. GitHub numbers a repeated
    fragment across headings of every level, so every heading takes part in the numbering."""
    every = all_headings(text)
    chapters = {
        fragment: title
        for (fragment, title), (level, _) in zip(_unique_fragments([title for _, title in every]), every, strict=True)
        if level == 2 and title not in ("Purpose", "Contents")
    }
    problems: list[str] = []
    linked: set[str] = set()
    for line in section(text, "Contents"):
        if not line.strip():
            continue
        link_m = _LIST_LINK_RE.match(line.strip())
        if link_m is None or not link_m.group("target").startswith("#"):
            problems.append(f"{page}: 'Contents' may hold only '- [title](#chapter)' lines; found {line.strip()!r}")
            continue
        fragment = link_m.group("target")[1:]
        if fragment not in chapters:
            problems.append(f"{page}: 'Contents' links to '#{fragment}', which is no '##' chapter of the page")
        linked.add(fragment)
    for fragment, title in chapters.items():
        if fragment not in linked:
            problems.append(f"{page}: chapter '## {title}' is missing from 'Contents'")
    return problems


def _resolved_links(page: str, text: str) -> set[str]:
    """Every relative link of the page into the repository, as a repository path without its fragment. A link
    inside a fenced code block, an HTML comment or a code span does not count - GitHub renders no link there."""
    base = PurePosixPath(page).parent
    resolved: set[str] = set()
    for link_m in _LINK_TARGET_RE.finditer(_CODE_SPAN_RE.sub("", "\n".join(unfenced_lines(text)))):
        target = link_m.group("target").split("#", 1)[0]
        if not target or "://" in target or target.startswith("mailto:"):
            continue
        parts: list[str] = []
        for part in (base / target).parts:
            if part == "..":
                if parts:
                    parts.pop()
                else:
                    break
            elif part != ".":
                parts.append(part)
        else:
            resolved.add("/".join(parts))
    return resolved


def expected_parents(page: str) -> set[str]:
    """The pages allowed to link `page` into the tree: its hub for a depth-3 page, and `README.md`."""
    parts = PurePosixPath(page).parts
    if len(parts) == 3 and parts[0] == "docs":
        return {f"docs/{parts[1]}.md", "README.md"}
    return {"README.md"}


def check_no_orphans(pages: dict[str, str]) -> list[str]:
    """Every page except `README.md` is linked from its hub or from `README.md`."""
    links = {page: _resolved_links(page, text) for page, text in pages.items()}
    problems = []
    for page in pages:
        if page == "README.md":
            continue
        if not any(page in links.get(parent, set()) for parent in expected_parents(page)):
            parents = " or ".join(sorted(expected_parents(page)))
            problems.append(f"{page}: orphan page; link it from {parents}")
    return problems


def page_depth(page: str) -> int:
    """The depth a page's path gives it: 1 at the root, 2 in `docs/` or a mode's folder, 3 in `docs/<topic>/`."""
    return len(PurePosixPath(page).parts)
