#
# Copyright 2025 ABSA Group Limited
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

import json
import os
from pathlib import Path

import pytest

from doc_check.checker import GHDocChecker

US_FEATURE_TEMPLATE = """# =============================================================================
# LIVING DOC — US-{num} · Story {num}
# =============================================================================
# status:         active
# business_value:
#   - Value for story {num}.
#
# acceptance_criteria:
#
#   AC:US-{num}-01 (v1.0.0 - active)
#     - Criterion for story {num}.
# =============================================================================

@US_ID:US-{num}
Feature: Story {num}
"""

FUNC_FEATURE_TEMPLATE = """# =============================================================================
# LIVING DOC — FUNC-{num} · Functionality {num}
# =============================================================================
# status:    active
# parent:    FEAT-{num}
# func_type: button_action
#
# acceptance_criteria:
#
#   AC:FUNC-{num}-01 (v1.0.0 - active)
#     - Criterion for functionality {num}.
# =============================================================================

@FUNC_ID:FUNC-{num}
Feature: Functionality {num}
"""

TS_PAGE_OBJECT_TEMPLATE = """/* =============================================================================
 * LIVING DOC — FEAT-{num} · Feature {num}
 * =============================================================================
 * surface_type:          UI
 * route:                 /feat-{num}
 * owners:                Test Team
 * purpose:               Purpose of feature {num}.
 * user_stories:          US-{num}
 * functionalities:       FUNC-{num}
 * external_dependencies: none
 * page-object:           Feature{num}Page.ts
 * ============================================================================= */

export class Feature{num}Page {{}}
"""

# The header the issue's testbed pull request breaks: the `-` before the state is missing.
MALFORMED_AC_LINE = "#   AC:FUNC-{num}-01 (v1.0.0 active)"
MALFORMED_AC_LINE_NO = 10

# Both codes the malformed header gives: the criterion, and the line under it that nothing reads any more.
MALFORMED_CODES = ("MALFORMED_AC", "AUTHORING_WARNING")


@pytest.fixture(autouse=True)
def _outside_github_actions(monkeypatch):
    # CI runs the suite inside GitHub Actions; each test sets the runner variables it needs.
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)


def _func_path(num: int) -> str:
    return f"features/liv_doc_func/func-{num}.feature"


def _write_repository(repo: Path, num: int = 1, malformed: bool = False) -> dict:
    """A checkout with one clean User Story, Functionality and Feature, the Functionality's header broken when
    `malformed`; returns its `doc-source-repositories` entry."""
    (repo / ".git").mkdir(parents=True)
    func_text = FUNC_FEATURE_TEMPLATE.format(num=num)
    if malformed:
        func_text = func_text.replace(f"#   AC:FUNC-{num}-01 (v1.0.0 - active)", MALFORMED_AC_LINE.format(num=num))
    files = {
        f"features/liv_doc_us/us-{num}.feature": US_FEATURE_TEMPLATE.format(num=num),
        _func_path(num): func_text,
        f"pages/Feature{num}Page.ts": TS_PAGE_OBJECT_TEMPLATE.format(num=num),
    }
    for path, text in files.items():
        (repo / path).parent.mkdir(parents=True, exist_ok=True)
        (repo / path).write_text(text, encoding="utf-8")
    return {
        "organization-name": "org",
        "repository-name": repo.name,
        "us-paths": [os.fspath(repo / "features" / "liv_doc_us")],
        "func-paths": [os.fspath(repo / "features" / "liv_doc_func")],
        "pages-paths": [os.fspath(repo / "pages")],
    }


def _configure(monkeypatch, entries: list[dict], changed: list[str]) -> None:
    monkeypatch.setenv("INPUT_DOC_SOURCE_REPOSITORIES", json.dumps(entries))
    monkeypatch.setenv("INPUT_DOC_CHECK_CHANGED_PATHS", "\n".join(changed) + "\n")


def _in_github_actions(monkeypatch, tmp_path: Path) -> Path:
    summary = tmp_path / "step_summary.md"
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", os.fspath(summary))
    return summary


def test_a_malformed_header_in_a_changed_file_fails_with_an_annotation_on_its_line(tmp_path, monkeypatch, capsys):
    # Arrange
    entry = _write_repository(tmp_path / "repo", malformed=True)
    _configure(monkeypatch, [entry], [_func_path(1)])
    summary = _in_github_actions(monkeypatch, tmp_path)

    # Act
    passed = GHDocChecker().check()

    # Assert
    out = capsys.readouterr().out
    assert passed is False
    assert f"{_func_path(1)}:{MALFORMED_AC_LINE_NO}: MALFORMED_AC Acceptance criterion failed validation" in out
    assert f"::error file={_func_path(1)},line={MALFORMED_AC_LINE_NO},title=MALFORMED_AC::" in out
    assert "MALFORMED\\_AC" in summary.read_text(encoding="utf-8")


def test_a_finding_the_policy_relaxes_only_warns_and_passes(tmp_path, monkeypatch, capsys):
    # Arrange
    entry = _write_repository(tmp_path / "repo", malformed=True)
    (tmp_path / "repo" / "living-doc-policy.yaml").write_text(
        "check:\n  warn:\n" + "".join(f"    - {code}\n" for code in MALFORMED_CODES), encoding="utf-8"
    )
    _configure(monkeypatch, [entry], [_func_path(1)])
    _in_github_actions(monkeypatch, tmp_path)

    # Act
    passed = GHDocChecker().check()

    # Assert
    out = capsys.readouterr().out
    assert passed is True
    assert f"::warning file={_func_path(1)},line={MALFORMED_AC_LINE_NO},title=MALFORMED_AC::" in out
    assert "::error " not in out


def test_each_finding_fails_under_the_policy_of_its_own_repository(tmp_path, monkeypatch, capsys):
    # Arrange: both repositories break a header; only the first one's policy relaxes the codes.
    relaxed = _write_repository(tmp_path / "relaxed", num=1, malformed=True)
    (tmp_path / "relaxed" / "living-doc-policy.yaml").write_text(
        "check:\n  warn: [" + ", ".join(MALFORMED_CODES) + "]\n", encoding="utf-8"
    )
    strict = _write_repository(tmp_path / "strict", num=2, malformed=True)
    _configure(monkeypatch, [relaxed, strict], [_func_path(1), _func_path(2)])
    _in_github_actions(monkeypatch, tmp_path)

    # Act
    passed = GHDocChecker().check()

    # Assert
    out = capsys.readouterr().out
    assert passed is False
    assert f"::warning file={_func_path(1)},line={MALFORMED_AC_LINE_NO},title=MALFORMED_AC::" in out
    assert f"::error file={_func_path(2)},line={MALFORMED_AC_LINE_NO},title=MALFORMED_AC::" in out


def test_a_changed_path_outside_the_corpus_is_skipped(tmp_path, monkeypatch, capsys):
    # Arrange: a clean living-doc change, next to a source file and a deleted file the corpus does not hold.
    entry = _write_repository(tmp_path / "repo")
    _configure(monkeypatch, [entry], ["src/app.ts", "features/liv_doc_us/us-deleted.feature", _func_path(1)])
    _in_github_actions(monkeypatch, tmp_path)

    # Act
    passed = GHDocChecker().check()

    # Assert
    assert passed is True
    assert capsys.readouterr().out == ""


def test_a_pull_request_with_no_living_doc_change_reports_nothing_and_passes(tmp_path, monkeypatch, capsys):
    # Arrange: the corpus holds a malformed header, but the pull request changes no file of it.
    entry = _write_repository(tmp_path / "repo", malformed=True)
    _configure(monkeypatch, [entry], ["README.md"])
    summary = _in_github_actions(monkeypatch, tmp_path)

    # Act
    passed = GHDocChecker().check()

    # Assert
    assert passed is True
    assert capsys.readouterr().out == ""
    assert not summary.exists()


def test_outside_github_actions_it_prints_the_plain_finding_lines(tmp_path, monkeypatch, capsys):
    # Arrange
    entry = _write_repository(tmp_path / "repo", malformed=True)
    _configure(monkeypatch, [entry], [_func_path(1)])

    # Act
    passed = GHDocChecker().check()

    # Assert
    lines = capsys.readouterr().out.splitlines()
    assert passed is False
    assert [line.split(" ")[:2] for line in lines] == [
        [f"{_func_path(1)}:{MALFORMED_AC_LINE_NO}:", "MALFORMED_AC"],
        [f"{_func_path(1)}:{MALFORMED_AC_LINE_NO + 1}:", "AUTHORING_WARNING"],
    ]


def test_the_same_skips_as_doc_source_keep_a_file_out_of_the_corpus(tmp_path, monkeypatch, capsys):
    # Arrange: a `.ts` file with no living-doc header, and a broken header under a `tutorial*` folder.
    entry = _write_repository(tmp_path / "repo")
    (tmp_path / "repo" / "pages" / "helpers.ts").write_text("export const x = 1;\n", encoding="utf-8")
    tutorial = tmp_path / "repo" / "features" / "liv_doc_func" / "tutorial_basics" / "func-9.feature"
    tutorial.parent.mkdir()
    tutorial.write_text(FUNC_FEATURE_TEMPLATE.format(num=9).replace("- active", "active"), encoding="utf-8")
    _configure(monkeypatch, [entry], ["pages/helpers.ts", "features/liv_doc_func/tutorial_basics/func-9.feature"])

    # Act
    passed = GHDocChecker().check()

    # Assert
    assert passed is True
    assert capsys.readouterr().out == ""


def test_a_policy_file_the_model_rejects_fails_and_names_the_file(tmp_path, monkeypatch, mocker):
    # Arrange
    entry = _write_repository(tmp_path / "repo", malformed=True)
    policy = tmp_path / "repo" / "living-doc-policy.yaml"
    policy.write_text("check:\n  warn: [NOT_A_CODE]\n", encoding="utf-8")
    _configure(monkeypatch, [entry], [_func_path(1)])
    mock_log_error = mocker.patch("doc_check.checker.logger.error")

    # Act
    passed = GHDocChecker().check()

    # Assert
    assert passed is False
    fmt, error = mock_log_error.call_args.args
    message = fmt % error
    assert message.startswith("The `doc-check` mode failed: [INVALID_CONFIGURATION]")
    assert os.fspath(policy) in message


def test_a_policy_file_that_is_not_yaml_fails_and_names_the_file(tmp_path, monkeypatch, mocker):
    # Arrange
    entry = _write_repository(tmp_path / "repo", malformed=True)
    policy = tmp_path / "repo" / "living-doc-policy.yaml"
    policy.write_text("check: [unclosed\n", encoding="utf-8")
    _configure(monkeypatch, [entry], [_func_path(1)])
    mock_log_error = mocker.patch("doc_check.checker.logger.error")

    # Act
    passed = GHDocChecker().check()

    # Assert
    assert passed is False
    fmt, error = mock_log_error.call_args.args
    assert os.fspath(policy) in fmt % error


def test_two_repositories_with_a_file_at_the_same_path_fail_as_invalid_configuration(tmp_path, monkeypatch, mocker):
    # Arrange
    first = _write_repository(tmp_path / "first", num=1)
    second = _write_repository(tmp_path / "second", num=1)
    _configure(monkeypatch, [first, second], [_func_path(1)])
    mock_log_error = mocker.patch("doc_check.checker.logger.error")

    # Act
    passed = GHDocChecker().check()

    # Assert
    assert passed is False
    fmt, error = mock_log_error.call_args.args
    message = fmt % error
    assert "[INVALID_CONFIGURATION]" in message
    assert _func_path(1) in message


def test_a_missing_configured_path_fails_as_source_unavailable(tmp_path, monkeypatch, mocker):
    # Arrange
    entry = _write_repository(tmp_path / "repo")
    entry["func-paths"] = [os.fspath(tmp_path / "repo" / "missing")]
    _configure(monkeypatch, [entry], [_func_path(1)])
    mock_log_error = mocker.patch("doc_check.checker.logger.error")

    # Act
    passed = GHDocChecker().check()

    # Assert
    assert passed is False
    fmt, error = mock_log_error.call_args.args
    assert "[SOURCE_UNAVAILABLE]" in fmt % error


def test_a_file_outside_a_git_checkout_is_named_from_its_scan_root_under_the_default_policy(
    tmp_path, monkeypatch, capsys
):
    # Arrange
    entry = _write_repository(tmp_path / "repo", malformed=True)
    (tmp_path / "repo" / ".git").rmdir()
    _configure(monkeypatch, [entry], ["func-1.feature"])

    # Act
    passed = GHDocChecker().check()

    # Assert
    assert passed is False
    assert capsys.readouterr().out.startswith(f"func-1.feature:{MALFORMED_AC_LINE_NO}: MALFORMED_AC ")
