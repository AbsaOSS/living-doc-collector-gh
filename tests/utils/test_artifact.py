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
from pathlib import Path

from living_doc_utilities.contracts.envelope import Cardinality, ContractWarning

from utils.artifact import (
    DEFAULT_PROJECT_ID,
    SourceRepository,
    build_metadata,
    find_repo_root,
    relative_path,
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


# build_metadata


def test_build_metadata_lists_each_organization_and_repository_once():
    # Arrange
    repositories = [SourceRepository("org", "a"), SourceRepository("org", "b"), SourceRepository("org", "a")]

    # Act
    metadata = build_metadata(repositories, Cardinality(sources_configured=3))

    # Assert
    assert metadata.source.project_id == DEFAULT_PROJECT_ID
    assert metadata.source.organizations == ["org"]
    assert metadata.source.repositories == ["org/a", "org/b"]
    assert metadata.source.extraction_mode is None
    assert metadata.producer.name == "AbsaOSS/living-doc-collector-gh"
    assert metadata.stats.cardinality.sources_configured == 3
