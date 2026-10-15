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

"""The page-structure rules: `Purpose` then `Contents`, `Contents` links, no orphan page (DEVELOPER.md)."""

import re

import pytest

from tests.docs.pages import (
    APPROVED_PAGES,
    REPO_ROOT,
    check_contents_links,
    check_no_orphans,
    check_purpose_then_contents,
    headings,
    page_depth,
    read_page,
    tracked_markdown,
)

_GOOD_PAGE = """# Title

## Purpose

Who reads this page, and what they get.

## Contents

- [Facts](#facts)

## Facts

- a fact
"""


def test_page_list_matches_the_tracked_pages():
    """Every tracked page is approved, every approved page exists, and its path gives its depth."""
    assert tracked_markdown() - set(APPROVED_PAGES) == set(), "unapproved page(s); add them to APPROVED_PAGES"
    for page, depth in APPROVED_PAGES.items():
        assert (REPO_ROOT / page).is_file(), f"{page}: approved but missing"
        assert page_depth(page) == depth, f"{page}: listed at depth {depth}, but its path gives {page_depth(page)}"


def test_depth_one_is_exactly_the_four_root_pages():
    """Depth 1 is `README.md` and the three solo pages, and no solo page has child pages."""
    solo = ["CONTRIBUTING.md", "DEVELOPER.md", "SPEC.md"]
    assert sorted(page for page, depth in APPROVED_PAGES.items() if depth == 1) == sorted(["README.md", *solo])
    assert [page for page in solo if (REPO_ROOT / "docs" / page.removesuffix(".md")).exists()] == []


def test_every_depth_three_page_sits_under_an_approved_hub():
    """A depth-3 page `docs/<topic>/<page>.md` has its hub `docs/<topic>.md` in the approved list."""
    for page, depth in APPROVED_PAGES.items():
        if depth == 3:
            hub = f"docs/{page.split('/')[1]}.md"
            assert hub in APPROVED_PAGES, f"{page}: its hub {hub} is not an approved page"


@pytest.mark.parametrize("page", sorted(APPROVED_PAGES))
def test_page_opens_with_purpose_then_contents(page):
    """The page's first `##` heading is `Purpose` and its second is `Contents`."""
    assert check_purpose_then_contents(page, read_page(page)) == []


@pytest.mark.parametrize("page", sorted(APPROVED_PAGES))
def test_contents_links_every_chapter_and_nothing_else(page):
    """Every `Contents` link resolves to a `##` chapter of the same page, and every chapter is listed."""
    assert check_contents_links(page, read_page(page)) == []


def test_no_page_is_an_orphan():
    """Every approved page is linked from its hub or from `README.md`."""
    assert check_no_orphans({page: read_page(page) for page in APPROVED_PAGES}) == []


def test_readme_links_repository_files_relatively():
    """README.md is no PyPI description: it links this repository's files relatively, so the link check reads the
    checked-out files, not the published `master`."""
    absolute = re.findall(
        r"\]\((https://github\.com/AbsaOSS/living-doc-collector-gh/(?:blob|tree)/[^)\s]*)\)", read_page("README.md")
    )
    assert absolute == []


def test_a_backtick_in_a_backtick_fence_info_string_does_not_open_a_fence():
    """A backtick in a backtick-fence info string leaves the following heading visible to the parser."""
    page = "# Title\n\n```bad`info\n## Actually A Heading\n```\n"
    assert headings(page, 2) == ["Actually A Heading"]


def test_a_well_formed_page_passes_every_check():
    """The synthetic page the planted-violation tests start from is itself clean."""
    assert check_purpose_then_contents("docs/x.md", _GOOD_PAGE) == []
    assert check_contents_links("docs/x.md", _GOOD_PAGE) == []


def test_planted_missing_purpose_is_reported_naming_the_page():
    """A page without `## Purpose` fails, and the message names the page."""
    page = _GOOD_PAGE.replace("## Purpose\n\nWho reads this page, and what they get.\n\n", "")
    assert check_purpose_then_contents("docs/x.md", page) == [
        "docs/x.md: the first two '##' headings must be 'Purpose', 'Contents'; found ['Contents', 'Facts']"
    ]


def test_planted_wrong_order_is_reported_naming_the_page():
    """`Contents` before `Purpose` fails."""
    page = "# Title\n\n## Contents\n\n- [Purpose](#purpose)\n\n## Purpose\n\nText.\n"
    assert check_purpose_then_contents("docs/x.md", page) == [
        "docs/x.md: the first two '##' headings must be 'Purpose', 'Contents'; found ['Contents', 'Purpose']"
    ]


def test_planted_dead_contents_link_is_reported_naming_the_page():
    """A `Contents` link to a chapter the page does not have fails, as does the chapter it leaves out."""
    page = _GOOD_PAGE.replace("- [Facts](#facts)", "- [Facts](#fact-list)")
    assert check_contents_links("docs/x.md", page) == [
        "docs/x.md: 'Contents' links to '#fact-list', which is no '##' chapter of the page",
        "docs/x.md: chapter '## Facts' is missing from 'Contents'",
    ]


def test_planted_contents_line_that_is_not_a_chapter_link_is_reported():
    """`Contents` holds only chapter links; prose or an outside link fails."""
    page = _GOOD_PAGE.replace("- [Facts](#facts)", "- [Facts](#facts)\n- [Elsewhere](other.md)")
    assert check_contents_links("docs/x.md", page) == [
        "docs/x.md: 'Contents' may hold only '- [title](#chapter)' lines; found '- [Elsewhere](other.md)'"
    ]


def test_a_second_chapter_with_the_same_title_needs_its_own_contents_entry():
    """GitHub gives a repeated `## Facts` the fragment `#facts-1`; `Contents` must link that too, not just `#facts`."""
    page = "# Title\n\n## Purpose\n\nText.\n\n## Contents\n\n- [Facts](#facts)\n\n## Facts\n\n- a\n\n## Facts\n\n- b\n"
    assert check_contents_links("docs/x.md", page) == ["docs/x.md: chapter '## Facts' is missing from 'Contents'"]


def test_emphasis_in_a_heading_is_dropped_from_its_fragment():
    """`## **Branch Naming**` is `#branch-naming` on GitHub, so `Contents` links it by that fragment."""
    page = (
        "# Title\n\n## Purpose\n\nText.\n\n## Contents\n\n- [Branch Naming](#branch-naming)\n\n## **Branch Naming**\n"
    )
    assert check_contents_links("docs/x.md", page) == []


def test_planted_orphan_page_is_reported_naming_the_page():
    """A mode page that `README.md` does not link fails."""
    pages = {"README.md": "[Action](docs/action.md)", "docs/action.md": "", "doc_source/README.md": ""}
    assert check_no_orphans(pages) == ["doc_source/README.md: orphan page; link it from README.md"]


def test_a_page_linked_only_from_a_sibling_is_still_an_orphan():
    """A link from another depth-2 page does not count; only `README.md` puts a depth-2 page in the tree."""
    pages = {
        "README.md": "[Action](docs/action.md)",
        "docs/action.md": "[Mode](../doc_source/README.md)",
        "doc_source/README.md": "",
    }
    assert check_no_orphans(pages) == ["doc_source/README.md: orphan page; link it from README.md"]


def test_a_link_inside_a_fenced_code_block_does_not_count_as_navigation():
    """A repository-shaped link inside an illustrative code example is not a real link into the tree."""
    pages = {"README.md": "```text\n[Action](docs/action.md)\n```\n", "docs/action.md": ""}
    assert check_no_orphans(pages) == ["docs/action.md: orphan page; link it from README.md"]
