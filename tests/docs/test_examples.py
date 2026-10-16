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

"""Every documentation example parses: `yaml` configures only declared inputs, `json` parses, `python` runs."""

import json
import re
from typing import Any

import pytest
import yaml

from tests.docs.pages import APPROVED_PAGES, CodeBlock, action_yml, code_blocks, headings, read_page

ACTION = "AbsaOSS/living-doc-collector-gh"
# GitHub resolves `owner/repo` in `uses:` regardless of case.
_USES_RE = re.compile(rf"uses:\s*(?P<quote>['\"]?){re.escape(ACTION)}@(?P<ref>[^'\"\s]+)(?P=quote)", re.IGNORECASE)
_RELEASE_TAG_RE = re.compile(r"v(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)")
_LANGUAGE_ALIASES = {"yml": "yaml", "py": "python", "python3": "python"}


def example_language(info: str) -> str:
    """The language of a fenced block: the first word of its info string, lowercased, with its aliases folded."""
    words = info.split()
    language = words[0].lower() if words else ""
    return _LANGUAGE_ALIASES.get(language, language)


def _examples(language: str) -> list:
    return [
        pytest.param(block, id=f"{page}#{index}")
        for page in sorted(APPROVED_PAGES)
        for index, block in enumerate(code_blocks(read_page(page)))
        if example_language(block.info) == language
    ]


def action_with_blocks(node: Any) -> list[dict]:
    """Every `with:` mapping in a parsed example that configures this action: a step that `uses` it, or a bare
    `with:` block with no step around it. Another action's `with:` (e.g. `actions/checkout`) is not ours."""
    found: list[dict] = []
    if isinstance(node, list):
        for item in node:
            found.extend(action_with_blocks(item))
    elif isinstance(node, dict):
        uses = node.get("uses")
        if isinstance(node.get("with"), dict) and (uses is None or str(uses).lower().startswith(f"{ACTION.lower()}@")):
            found.append(node["with"])
        for key, value in node.items():
            if key != "with":
                found.extend(action_with_blocks(value))
    return found


def yaml_example_problems(block: CodeBlock) -> list[str]:
    """Why a `yaml` example is wrong: it does not parse, or it sets an input `action.yml` does not declare."""
    try:
        payload = yaml.safe_load(block.code)
    except yaml.YAMLError as e:
        return [f"does not parse: {e}"]
    declared = set(action_yml()["inputs"])
    return [
        f"`with:` sets `{key}`, which `action.yml` does not declare"
        for with_block in action_with_blocks(payload)
        for key in with_block
        if key not in declared
    ]


@pytest.mark.parametrize("block", _examples("yaml"))
def test_yaml_example_parses_and_sets_only_declared_inputs(block):
    """The block parses as YAML, and every `with:` key it gives this action is an `action.yml` input."""
    assert yaml_example_problems(block) == []


@pytest.mark.parametrize("block", _examples("json"))
def test_json_example_parses(block):
    """The block parses as JSON."""
    json.loads(block.code)


@pytest.mark.parametrize("block", _examples("python"))
def test_python_example_runs(block, tmp_path, monkeypatch):
    """The block runs in a fresh namespace, in a temporary working directory."""
    monkeypatch.chdir(tmp_path)
    exec(compile(block.code, "<doc example>", "exec"), {"__name__": "doc_example"})  # pylint: disable=exec-used


def test_the_pages_carry_examples():
    """The example check has something to check: the pages hold several `yaml` examples that use this action."""
    configuring = [param for param in _examples("yaml") if action_with_blocks(yaml.safe_load(param.values[0].code))]
    assert len(configuring) >= 5


def _release_refs_are_valid(refs: set[str]) -> bool:
    if len(refs) != 1:
        return False
    ref = next(iter(refs))
    return ref != "v0.1.0" and _RELEASE_TAG_RE.fullmatch(ref) is not None


def test_every_example_names_one_release_of_this_action():
    """Every `uses:` of this action on every page names the same release, so a release bump changes them all."""
    refs = {ref_m.group("ref") for page in APPROVED_PAGES for ref_m in _USES_RE.finditer(read_page(page))}
    assert _release_refs_are_valid(refs), f"the pages name invalid releases: {sorted(refs)}"


def test_planted_old_release_is_rejected() -> None:
    """The documentation check rejects the old v0.1.0 action reference."""
    assert not _release_refs_are_valid({"v0.1.0"})


@pytest.mark.parametrize("ref", ["main", "v0.2", "v0.2.0-rc.1"])
def test_non_release_refs_are_rejected(ref: str) -> None:
    """Branches and references outside the stable release-tag format are not releases."""
    assert not _release_refs_are_valid({ref})


def test_semver_release_ref_is_accepted() -> None:
    """A stable release tag with major, minor, and patch components is accepted."""
    assert _release_refs_are_valid({"v0.2.0"})


def test_multiple_release_refs_are_rejected() -> None:
    """Every documentation example must continue to use the same release."""
    assert not _release_refs_are_valid({"v0.2.0", "v0.2.1"})


def test_planted_quoted_old_release_is_rejected() -> None:
    """The documentation check extracts quoted YAML `uses:` refs before rejecting old releases."""
    page = f'- uses: {ACTION}@v0.2.0\n- uses: "{ACTION}@v0.1.0"\n'
    assert yaml.safe_load(page) == [
        {"uses": f"{ACTION}@v0.2.0"},
        {"uses": f"{ACTION}@v0.1.0"},
    ]
    refs = {match.group("ref") for match in _USES_RE.finditer(page)}
    assert refs == {"v0.2.0", "v0.1.0"}
    assert not _release_refs_are_valid(refs)


def test_planted_undeclared_input_is_reported():
    """A step of this action that sets an input `action.yml` does not declare fails; another action's step does not."""
    code = (
        "- uses: actions/checkout@v4\n  with:\n    fetch-depth: 0\n"
        f"- uses: {ACTION}@v0.2.0\n  with:\n    project-id: p\n    doc-sources: true\n"
    )
    assert yaml_example_problems(CodeBlock("yaml", code, "")) == [
        "`with:` sets `doc-sources`, which `action.yml` does not declare"
    ]


def test_planted_lowercase_owner_is_checked_and_its_release_read():
    """`absaoss/living-doc-collector-gh` is the same action on GitHub, so its inputs and its release are checked."""
    code = "- uses: absaoss/living-doc-collector-gh@v0.1.0\n  with:\n    doc-sources: true\n"
    assert yaml_example_problems(CodeBlock("yaml", code, "")) == [
        "`with:` sets `doc-sources`, which `action.yml` does not declare"
    ]
    assert {ref_m.group("ref") for ref_m in _USES_RE.finditer(code)} == {"v0.1.0"}


@pytest.mark.parametrize(
    "info, language",
    [
        ("yaml", "yaml"),
        ("yml", "yaml"),
        ("YAML", "yaml"),
        ("yaml title=step.yml", "yaml"),
        ("JSON", "json"),
        ("py", "python"),
        ("python3", "python"),
        ("shell", "shell"),
        ("", ""),
    ],
)
def test_every_spelling_of_a_language_is_checked(info, language):
    """A `yml`, `YAML` or annotated block is a `yaml` example; `py` and `python3` are `python`."""
    assert example_language(info) == language


def test_a_fence_in_a_list_item_or_a_blockquote_is_an_example():
    """GitHub renders an indented fence under a list item, and a quoted one, as code, so both are checked."""
    page = (
        "1. Add the step:\n\n    ```yaml\n    - uses: AbsaOSS/living-doc-collector-gh@v0.2.0\n      with:\n"
        "        doc-sources: true\n    ```\n\n> ```yml\n> with:\n>   ui-test: true\n> ```\n"
    )
    blocks = code_blocks(page)
    assert [block.info for block in blocks] == ["yaml", "yml"]
    assert [problem for block in blocks for problem in yaml_example_problems(block)] == [
        "`with:` sets `doc-sources`, which `action.yml` does not declare",
        "`with:` sets `ui-test`, which `action.yml` does not declare",
    ]


def test_a_fence_on_the_list_marker_line_is_an_example():
    """`1. ```yaml` opens a block inside the item, so its inputs are checked and the page after it is still read."""
    page = (
        "1. ```yaml\n   - uses: AbsaOSS/living-doc-collector-gh@v0.2.0\n     with:\n       doc-sources: true\n   ```\n\n"
        "## Next\n"
    )
    blocks = code_blocks(page)
    assert [block.info for block in blocks] == ["yaml"]
    assert yaml_example_problems(blocks[0]) == ["`with:` sets `doc-sources`, which `action.yml` does not declare"]
    assert headings(page, 2) == ["Next"]


@pytest.mark.parametrize(
    "page",
    [
        "- ```markdown\n  > [!NOTE]\n  > Text.\n  ```\n\n## Errors\n",
        "```markdown\n> ```\n## Not a heading\n```\n\n## Errors\n",
    ],
    ids=["list-item-fence", "top-level-fence"],
)
def test_a_quote_marker_inside_a_fence_is_code(page):
    """A `>` deeper than the fence's own blockquote is code: it neither ends nor closes the block."""
    assert headings(page, 2) == ["Errors"]


def test_an_unclosed_fence_ends_with_its_container():
    """A quoted fence with no closing run ends where the blockquote ends, as on GitHub, so the page goes on."""
    page = "> ```yaml\n> with:\n>   project-id: p\n\n## Contents\n"
    assert headings(page, 2) == ["Contents"]
    assert [block.code for block in code_blocks(page)] == ["with:\n  project-id: p\n"]


def test_an_indented_run_inside_a_top_level_fence_does_not_close_it():
    """Four spaces before a run inside a top-level fence make it code, not a closing fence."""
    page = "```markdown\n    ```\n## Not a heading\n```\n\n## Next\n"
    assert headings(page, 2) == ["Next"]


def test_planted_bare_with_block_is_checked_too():
    """A bare `with:` snippet configures this action, so its keys are checked."""
    assert yaml_example_problems(CodeBlock("yaml", "with:\n  ui-test: true\n", "")) == [
        "`with:` sets `ui-test`, which `action.yml` does not declare"
    ]


def test_planted_unparseable_yaml_is_reported():
    """A block that is not YAML fails."""
    problems = yaml_example_problems(CodeBlock("yaml", "with:\n  project-id: [unclosed\n", ""))
    assert len(problems) == 1 and problems[0].startswith("does not parse:")
