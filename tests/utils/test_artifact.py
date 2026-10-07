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
import shutil
import subprocess
from pathlib import Path

import pytest
from living_doc_utilities.contracts.codes import Code, ContractError
from living_doc_utilities.contracts.envelope import Cardinality, ContractWarning

from utils.artifact import (
    SourceRepository,
    build_metadata,
    build_source_ref,
    collect_artifact,
    collect_sources,
    find_repo_root,
    head_commit,
    relative_path,
    source_context,
    with_path,
)

# find_repo_root


def test_find_repo_root_returns_the_directory_holding_git(tmp_path):
    # Arrange
    (tmp_path / "repo" / ".git").mkdir(parents=True)
    file_path = tmp_path / "repo" / "a" / "b.feature"

    # Act & Assert
    assert find_repo_root(file_path) == tmp_path / "repo"


def test_find_repo_root_resolves_a_relative_path_before_walking_up(tmp_path, monkeypatch):
    # Arrange: `a.feature` from inside `repo/sub`; walked lexically it would stop at `.` and miss `repo/.git`.
    (tmp_path / "repo" / ".git").mkdir(parents=True)
    (tmp_path / "repo" / "sub").mkdir()
    monkeypatch.chdir(tmp_path / "repo" / "sub")

    # Act & Assert
    assert find_repo_root(Path("a.feature")) == (tmp_path / "repo").resolve()


# head_commit


def test_head_commit_returns_the_checkout_s_head_sha(tmp_path, git_checkout):
    # Arrange
    sha = git_checkout(tmp_path / "repo")

    # Act & Assert
    assert head_commit(tmp_path / "repo") == sha
    assert len(sha) == 40


def test_head_commit_follows_a_submodule_s_relative_gitdir_file(tmp_path, git_checkout):
    # Arrange: a submodule's `.git` is a file pointing at the parent's `.git/modules/<name>` by a relative path.
    sha = git_checkout(tmp_path / "parent" / "sub")
    (tmp_path / "parent" / "modules").mkdir()
    shutil.move(tmp_path / "parent" / "sub" / ".git", tmp_path / "parent" / "modules" / "sub")
    (tmp_path / "parent" / "sub" / ".git").write_text("gitdir: ../modules/sub\n", encoding="utf-8")

    # Act & Assert
    assert head_commit(tmp_path / "parent" / "sub") == sha


def test_head_commit_is_none_for_a_git_directory_git_cannot_resolve(tmp_path):
    # Arrange: an empty `.git` directory is no repository to git.
    (tmp_path / "repo" / ".git").mkdir(parents=True)

    # Act & Assert
    assert head_commit(tmp_path / "repo") is None


def test_head_commit_never_falls_back_to_an_enclosing_repository(tmp_path, git_checkout):
    # Arrange: a broken `.git` inside a real checkout; `git -C` would answer with the outer checkout's commit.
    git_checkout(tmp_path / "outer")
    (tmp_path / "outer" / "inner" / ".git").mkdir(parents=True)

    # Act & Assert
    assert head_commit(tmp_path / "outer" / "inner") is None


def test_head_commit_is_none_for_a_repository_with_no_commit_yet(tmp_path):
    # Arrange
    (tmp_path / "repo").mkdir()
    subprocess.run(["git", "-C", str(tmp_path / "repo"), "init", "-q"], check=True)

    # Act & Assert
    assert head_commit(tmp_path / "repo") is None


def test_head_commit_is_none_when_git_cannot_run(tmp_path, mocker):
    # Arrange
    mocker.patch("utils.artifact.subprocess.run", side_effect=FileNotFoundError("git"))

    # Act & Assert
    assert head_commit(tmp_path) is None


def test_head_commit_reads_each_checkout_once(tmp_path, git_checkout, mocker):
    # Arrange
    git_checkout(tmp_path / "repo")
    spy = mocker.spy(subprocess, "run")

    # Act
    first = head_commit(tmp_path / "repo")
    second = head_commit(tmp_path / "repo")

    # Assert
    assert first == second
    assert spy.call_count == 1


# build_source_ref


def test_build_source_ref_url_is_the_blob_permalink_at_head_on_the_default_server(tmp_path, git_checkout):
    # Arrange
    sha = git_checkout(tmp_path / "repo")
    file_path = tmp_path / "repo" / "features" / "a b.feature"

    # Act
    source_ref, warnings = build_source_ref(
        SourceRepository("org", "repo"), file_path, [str(tmp_path / "repo" / "features")], "scenario"
    )

    # Assert
    assert source_ref.native_id == "features/a b.feature"
    assert source_ref.url == f"https://github.com/org/repo/blob/{sha}/features/a%20b.feature"
    assert warnings == []


def test_build_source_ref_url_uses_the_repository_s_server(tmp_path, git_checkout):
    # Arrange
    sha = git_checkout(tmp_path / "repo")

    # Act
    source_ref, _ = build_source_ref(
        SourceRepository("org", "repo", "https://ghe.example"), tmp_path / "repo" / "a.feature", [], "scenario"
    )

    # Assert
    assert source_ref.url == f"https://ghe.example/org/repo/blob/{sha}/a.feature"


def test_build_source_ref_outside_git_has_no_url_and_a_scan_root_relative_native_id(tmp_path):
    # Arrange
    file_path = tmp_path / "scan" / "x" / "a.feature"

    # Act
    source_ref, warnings = build_source_ref(SourceRepository("org", "repo"), file_path, [str(tmp_path / "scan")], "s")

    # Assert
    assert source_ref.url == ""
    assert source_ref.native_id == "x/a.feature"
    assert [(w.code, w.context) for w in warnings] == [("NO_SOURCE_URL", "path='x/a.feature'")]
    assert "outside a git checkout" in warnings[0].message


def test_build_source_ref_in_a_checkout_with_no_resolvable_head_has_no_url(tmp_path):
    # Arrange: a fake `.git` directory - the root is found, but git resolves no commit.
    (tmp_path / "repo" / ".git").mkdir(parents=True)
    file_path = tmp_path / "repo" / "scan" / "a.feature"

    # Act
    source_ref, warnings = build_source_ref(
        SourceRepository("org", "repo"), file_path, [str(tmp_path / "repo" / "scan")], "s"
    )

    # Assert
    assert source_ref.url == ""
    assert source_ref.native_id == "scan/a.feature"
    assert [(w.code, w.context) for w in warnings] == [("NO_SOURCE_URL", "path='scan/a.feature'")]
    assert "no resolvable HEAD commit" in warnings[0].message


# relative_path


def test_relative_path_uses_the_first_containing_scan_root(tmp_path):
    # Arrange
    file_path = tmp_path / "features" / "x" / "a.feature"

    # Act & Assert
    assert relative_path(file_path, [str(tmp_path / "other"), str(tmp_path / "features")]) == "x/a.feature"


def test_relative_path_falls_back_to_the_file_name(tmp_path):
    # Act & Assert
    assert relative_path(tmp_path / "a.feature", [str(tmp_path / "other")]) == "a.feature"


# with_path


def test_with_path_prefixes_the_context_or_sets_it():
    # Arrange
    warnings = [
        ContractWarning(code="MALFORMED_AC", message="m", context="line_no=3"),
        ContractWarning(code="MALFORMED_AC", message="m"),
    ]

    # Act
    located = with_path(warnings, "a.feature")

    # Assert
    assert [w.context for w in located] == ["path='a.feature' line_no=3", "path='a.feature'"]


# source_context


def test_source_context_names_the_input_the_entry_and_the_repository():
    # Act & Assert
    assert (
        source_context("doc-source-repositories", 1, SourceRepository("org", "repo"))
        == "input='doc-source-repositories' entry=1 repository='org/repo'"
    )


# collect_sources


def _unavailable():
    raise ContractError(Code.SOURCE_UNAVAILABLE, "Configured path `/x` does not exist or is not a directory.")


def test_collect_sources_returns_no_warning_when_every_source_answers():
    # Act
    warnings, failed = collect_sources([("entry=0", lambda: 2), ("entry=1", lambda: 1)], allow_partial=False)

    # Assert
    assert warnings == []
    assert failed == []


def test_collect_sources_with_no_source_is_no_failure():
    # Act & Assert
    assert collect_sources([], allow_partial=False) == ([], [])


def test_collect_sources_reports_a_source_answering_zero_entities_as_empty_source():
    # Act
    warnings, failed = collect_sources([("entry=0", lambda: 1), ("entry=1", lambda: 0)], allow_partial=False)

    # Assert
    assert [(w.code, w.context) for w in warnings] == [("EMPTY_SOURCE", "entry=1")]
    assert failed == []


def test_collect_sources_by_default_tries_every_source_then_fails_the_mode(mocker):
    # Arrange: the first source fails; the later one must still be tried.
    later = mocker.Mock(return_value=3)
    mock_log_error = mocker.patch("utils.artifact.logger.error")

    # Act
    with pytest.raises(ContractError) as error:
        collect_sources([("entry=0", _unavailable), ("entry=1", later)], allow_partial=False)

    # Assert
    later.assert_called_once_with()
    assert error.value.code == Code.SOURCE_UNAVAILABLE
    assert error.value.message == "1 of 2 configured sources failed."
    mock_log_error.assert_called_once()
    logged = mock_log_error.call_args.args[1]
    assert str(logged) == (
        "[SOURCE_UNAVAILABLE] Configured path `/x` does not exist or is not a directory. (entry=0)"
    )


def test_collect_sources_with_allow_partial_turns_each_failed_source_into_a_warning(mocker):
    # Arrange
    mock_log_warning = mocker.patch("utils.artifact.logger.warning")

    # Act
    warnings, failed = collect_sources(
        [("entry=0", lambda: 1), ("entry=1", _unavailable), ("entry=2", lambda: 0)], allow_partial=True
    )

    # Assert
    assert [(w.code, w.context) for w in warnings] == [("SOURCE_UNAVAILABLE", "entry=1"), ("EMPTY_SOURCE", "entry=2")]
    assert warnings[0].message == "Configured path `/x` does not exist or is not a directory."
    assert failed == [1]
    mock_log_warning.assert_called_once()


def test_collect_sources_with_allow_partial_still_fails_when_every_source_failed():
    # Act
    with pytest.raises(ContractError) as error:
        collect_sources([("entry=0", _unavailable), ("entry=1", _unavailable)], allow_partial=True)

    # Assert
    assert error.value.code == Code.SOURCE_UNAVAILABLE
    assert error.value.message == "2 of 2 configured sources failed."


# collect_artifact


def test_collect_artifact_returns_false_and_writes_nothing_when_the_mode_fails(tmp_path, mocker):
    # Arrange: a previous run's artifact is still in place.
    output_dir = tmp_path / "doc-source"
    output_dir.mkdir()
    (output_dir / "doc-source.json").write_text("{}", encoding="utf-8")
    mock_log_error = mocker.patch("utils.artifact.logger.error")

    def failing_build():
        raise ContractError(Code.SOURCE_UNAVAILABLE, "1 of 1 configured sources failed.")

    # Act
    actual = collect_artifact(failing_build, str(output_dir), "doc-source.json", "doc-source")

    # Assert
    assert actual is False
    assert not output_dir.exists()
    fmt, mode, error = mock_log_error.call_args.args
    assert fmt % (mode, error) == (
        "The `doc-source` mode failed, nothing written: [SOURCE_UNAVAILABLE] 1 of 1 configured sources failed."
    )


# build_metadata


def test_build_metadata_lists_each_organization_and_repository_once():
    # Arrange
    repositories = [SourceRepository("org", "a"), SourceRepository("org", "b"), SourceRepository("org", "a")]

    # Act
    metadata = build_metadata("test-project", repositories, Cardinality(sources_configured=3))

    # Assert
    assert metadata.source.project_id == "test-project"
    assert metadata.source.organizations == ["org"]
    assert metadata.source.repositories == ["org/a", "org/b"]
    assert metadata.source.extraction_mode is None
    assert metadata.producer.name == "AbsaOSS/living-doc-collector-gh"
    assert metadata.stats.cardinality.sources_configured == 3
