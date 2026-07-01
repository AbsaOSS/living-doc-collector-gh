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

US_FEATURE_TEMPLATE = """# =============================================================================
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

FUNC_FEATURE_TEMPLATE = """# =============================================================================
# LIVING DOC — FUNC-{num} · Functionality {num}
# =============================================================================
# status:    active
# parent:    FEAT-001
# func_type: button_action
#
# acceptance_criteria:
#
#   AC:FUNC-{num}-01 (v1.0.0 - Active)
#     - Criterion for functionality {num}.
# =============================================================================

@FUNC_ID:FUNC-{num}
Feature: Functionality {num}
Description of functionality {num}.
"""

TS_PAGE_OBJECT_TEMPLATE = """/* =============================================================================
 * LIVING DOC — FEAT-{num} · Feature {num}
 * =============================================================================
 * surface_type:          UI
 * route:                 /feat-{num}
 * owners:                Test Team
 * status:                active
 * purpose:               Purpose of feature {num}.
 * user_stories:          US-{num}
 * functionalities:       FUNC-{num}
 * external_dependencies: none
 * page-object:           Feature{num}Page.ts
 * ============================================================================= */

import type {{ Page }} from '@playwright/test';

export class Feature{num}Page {{}}
"""


def _write_us_feature(directory, num):
    path = directory / f"story_{num}.feature"
    path.write_text(US_FEATURE_TEMPLATE.format(num=num), encoding="utf-8")
    return path


def _write_func_feature(directory, num):
    path = directory / f"func_{num}.feature"
    path.write_text(FUNC_FEATURE_TEMPLATE.format(num=num), encoding="utf-8")
    return path


def _write_ts_page_object(directory, num):
    path = directory / f"Feature{num}Page.ts"
    path.write_text(TS_PAGE_OBJECT_TEMPLATE.format(num=num), encoding="utf-8")
    return path


def test_collect_single_repo(tmp_path, mocker):
    # Arrange
    repo_dir = tmp_path / "repo"
    us_dir = repo_dir / "us"
    us_dir.mkdir(parents=True)
    _write_us_feature(us_dir, 1)
    _write_us_feature(us_dir, 2)

    output_dir = tmp_path / "output"
    output_dir.mkdir()

    mocker.patch(
        "doc_source.collector.ActionInputs.get_doc_source_repositories",
        return_value=[
            {
                "organization-name": "absa-group",
                "repository-name": "aul-ui",
                "us-paths": [str(repo_dir)],
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
    assert len(data["user_stories"]) == 2
    ids = sorted(item["id"] for item in data["user_stories"])
    assert ids == ["absa-group/aul-ui/US-1", "absa-group/aul-ui/US-2"]
    assert all(item["timestamps"] is None for item in data["user_stories"])
    assert all(item["tags"] == [] for item in data["user_stories"])
    assert all(item["repository_name"] == "aul-ui" for item in data["user_stories"])


def test_collect_user_stories_url_built_from_git_root(tmp_path, mocker):
    # Arrange
    repo_dir = tmp_path / "repo"
    us_dir = repo_dir / "us"
    us_dir.mkdir(parents=True)
    (repo_dir / ".git").mkdir()  # mark repo root
    _write_us_feature(us_dir, 1)

    output_dir = tmp_path / "output"
    output_dir.mkdir()

    mocker.patch(
        "doc_source.collector.ActionInputs.get_doc_source_repositories",
        return_value=[
            {
                "organization-name": "absa-group",
                "repository-name": "aul-ui",
                "us-paths": [str(us_dir)],
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
    assert len(data["user_stories"]) == 1
    assert data["user_stories"][0]["url"] == "https://github.com/absa-group/aul-ui/blob/main/us/story_1.feature"


def test_collect_user_stories_url_is_none_outside_git_repo(tmp_path, mocker):
    # Arrange - no .git directory anywhere above, so repo root detection fails
    repo_dir = tmp_path / "repo"
    us_dir = repo_dir / "us"
    us_dir.mkdir(parents=True)
    _write_us_feature(us_dir, 1)

    output_dir = tmp_path / "output"
    output_dir.mkdir()

    mock_log_warning = mocker.patch("doc_source.collector.logger.warning")
    mocker.patch(
        "doc_source.collector.ActionInputs.get_doc_source_repositories",
        return_value=[
            {
                "organization-name": "absa-group",
                "repository-name": "aul-ui",
                "us-paths": [str(us_dir)],
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
    assert data["user_stories"][0]["url"] is None
    assert mock_log_warning.called


def test_collect_functionalities(tmp_path, mocker):
    # Arrange
    func_dir = tmp_path / "func"
    func_dir.mkdir(parents=True)
    _write_func_feature(func_dir, 1)
    _write_func_feature(func_dir, 2)

    output_dir = tmp_path / "output"
    output_dir.mkdir()

    mocker.patch(
        "doc_source.collector.ActionInputs.get_doc_source_repositories",
        return_value=[
            {
                "organization-name": "absa-group",
                "repository-name": "aul-ui",
                "us-paths": [],
                "func-paths": [str(func_dir)],
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
    assert data["user_stories"] == []
    assert len(data["functionalities"]) == 2
    ids = sorted(item["id"] for item in data["functionalities"])
    assert ids == ["absa-group/aul-ui/FUNC-1", "absa-group/aul-ui/FUNC-2"]
    assert all(item["parent"] == "FEAT-001" for item in data["functionalities"])
    assert all(item["func_type"] == "button_action" for item in data["functionalities"])
    assert all(item["repository_name"] == "aul-ui" for item in data["functionalities"])


def test_collect_features(tmp_path, mocker):
    # Arrange
    pages_dir = tmp_path / "pages"
    pages_dir.mkdir(parents=True)
    _write_ts_page_object(pages_dir, 1)
    _write_ts_page_object(pages_dir, 2)

    output_dir = tmp_path / "output"
    output_dir.mkdir()

    mocker.patch(
        "doc_source.collector.ActionInputs.get_doc_source_repositories",
        return_value=[
            {
                "organization-name": "absa-group",
                "repository-name": "aul-ui",
                "us-paths": [],
                "pages-paths": [str(pages_dir)],
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
    assert data["user_stories"] == []
    assert len(data["features"]) == 2
    ids = sorted(item["id"] for item in data["features"])
    assert ids == ["absa-group/aul-ui/FEAT-1", "absa-group/aul-ui/FEAT-2"]
    feat = next(item for item in data["features"] if item["id"] == "absa-group/aul-ui/FEAT-1")
    assert feat["surface_type"] == "UI"
    assert feat["route"] == "/feat-1"
    assert feat["user_stories"] == ["US-1"]
    assert feat["functionalities"] == ["FUNC-1"]
    assert feat["page_object"] == "Feature1Page.ts"
    assert feat["repository_name"] == "aul-ui"


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
                "us-paths": [str(tmp_path / "does-not-exist")],
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
    assert data["user_stories"] == []


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
                "us-paths": [str(repo_dir)],
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
    assert data["user_stories"] == []


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
