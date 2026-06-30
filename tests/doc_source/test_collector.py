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

from doc_source.collector import GHDocSourceCollector

FEATURE_TEMPLATE = """# =============================================================================
# LIVING DOC — US-{num} · Story {num}
# =============================================================================
# source:         https://github.com/org/repo/issues/{num}
# status:         active
# business_value:
#   - Value for story {num}.
# preconditions:
#   - The user has logged in.
# acceptance_criteria:
#   AC:US-{num}-01 (v1.0.0 - Active)
#     - Criterion for story {num}.
# =============================================================================

@US_ID:US-{num}
Feature: Story {num}
As a user, I want story {num} so that value.
"""


def _write_feature(directory, num):
    path = directory / f"story_{num}.feature"
    path.write_text(FEATURE_TEMPLATE.format(num=num), encoding="utf-8")
    return path


def test_collect_single_repo(tmp_path, mocker):
    # Arrange
    repo_dir = tmp_path / "repo"
    features_dir = repo_dir / "features"
    features_dir.mkdir(parents=True)
    _write_feature(features_dir, 1)
    _write_feature(features_dir, 2)

    output_dir = tmp_path / "output"
    output_dir.mkdir()

    mocker.patch(
        "doc_source.collector.ActionInputs.get_doc_source_repositories",
        return_value=[
            {
                "organization-name": "absa-group",
                "repository-name": "aul-ui",
                "local-path": str(repo_dir),
                "paths": ["features/*.feature"],
            }
        ],
    )

    # Act
    result = GHDocSourceCollector(str(output_dir)).collect()

    # Assert
    assert result is True
    output_file = os.path.join(str(output_dir), "doc-source", "doc-source.json")
    with open(output_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert len(data["items"]) == 2
    ids = sorted(item["id"] for item in data["items"])
    assert ids == ["absa-group/aul-ui/US-1", "absa-group/aul-ui/US-2"]
    assert all(item["timestamps"] is None for item in data["items"])
    assert all(item["tags"] == [] for item in data["items"])


def test_collect_local_path_missing(tmp_path, mocker):
    # Arrange
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    mocker.patch(
        "doc_source.collector.ActionInputs.get_doc_source_repositories",
        return_value=[
            {
                "organization-name": "absa-group",
                "repository-name": "aul-ui",
                "local-path": str(tmp_path / "does-not-exist"),
                "paths": ["features/*.feature"],
            }
        ],
    )

    # Act
    result = GHDocSourceCollector(str(output_dir)).collect()

    # Assert
    assert result is True
    output_file = os.path.join(str(output_dir), "doc-source", "doc-source.json")
    with open(output_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["items"] == []


def test_collect_no_matching_files(tmp_path, mocker):
    # Arrange
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    mocker.patch(
        "doc_source.collector.ActionInputs.get_doc_source_repositories",
        return_value=[
            {
                "organization-name": "absa-group",
                "repository-name": "aul-ui",
                "local-path": str(repo_dir),
                "paths": ["features/*.feature"],
            }
        ],
    )

    # Act
    result = GHDocSourceCollector(str(output_dir)).collect()

    # Assert
    assert result is True
    output_file = os.path.join(str(output_dir), "doc-source", "doc-source.json")
    with open(output_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["items"] == []


def test_collect_invalid_repository_json_logs_error(tmp_path, mocker):
    # Arrange
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    mock_log_error = mocker.patch("doc_source.collector.logger.error")
    mocker.patch(
        "doc_source.collector.ActionInputs.get_doc_source_repositories",
        return_value=[{"organization-name": "absa-group"}],
    )

    # Act
    result = GHDocSourceCollector(str(output_dir)).collect()

    # Assert
    assert result is True
    assert mock_log_error.called


def test_collect_write_failure_returns_false(tmp_path, mocker):
    # Arrange
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    mocker.patch("doc_source.collector.ActionInputs.get_doc_source_repositories", return_value=[])
    mocker.patch("doc_source.collector.open", side_effect=OSError("disk full"))

    # Act
    result = GHDocSourceCollector(str(output_dir)).collect()

    # Assert
    assert result is False
