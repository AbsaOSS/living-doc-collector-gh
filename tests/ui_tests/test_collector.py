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

from ui_tests.collector import GHUITestsCollector

FEATURE = """@US_ID:US-26
Feature: Create Domain
    As a user, I want to create domain.

    @AC:US-26-01
    Scenario: First scenario
        Given the user is logged in
        When the user acts
        Then a result happens

    @Regression
    Scenario: Second scenario
        Given another state
        Then another result
"""


def test_collect_single_repo(tmp_path, mocker):
    # Arrange
    repo_dir = tmp_path / "repo"
    features_dir = repo_dir / "features"
    features_dir.mkdir(parents=True)
    (features_dir / "create.feature").write_text(FEATURE, encoding="utf-8")

    output_dir = tmp_path / "output"
    output_dir.mkdir()

    mocker.patch(
        "ui_tests.collector.ActionInputs.get_ui_tests_repositories",
        return_value=[
            {
                "organization-name": "absa-group",
                "repository-name": "aul-ui",
                "paths": [str(repo_dir)],
            }
        ],
    )

    # Act
    result = GHUITestsCollector(str(output_dir)).collect()

    # Assert
    assert result is True
    output_file = os.path.join(str(output_dir), "ui-tests", "ui-tests.json")
    with open(output_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert len(data["items"]) == 2
    assert data["items"][0]["source"]["file"] == "features/create.feature"
    assert data["items"][0]["ac_ids"] == ["US-26-01"]
    assert data["items"][1]["tags"] == ["Regression"]


def test_collect_local_path_missing(tmp_path, mocker):
    # Arrange
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    mocker.patch(
        "ui_tests.collector.ActionInputs.get_ui_tests_repositories",
        return_value=[
            {
                "organization-name": "absa-group",
                "repository-name": "aul-ui",
                "paths": [str(tmp_path / "missing")],
            }
        ],
    )

    # Act
    result = GHUITestsCollector(str(output_dir)).collect()

    # Assert
    assert result is True
    output_file = os.path.join(str(output_dir), "ui-tests", "ui-tests.json")
    with open(output_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["items"] == []


def test_collect_invalid_repository_json_logs_error(tmp_path, mocker):
    # Arrange
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    mock_log_error = mocker.patch("ui_tests.collector.logger.error")
    mocker.patch(
        "ui_tests.collector.ActionInputs.get_ui_tests_repositories",
        return_value=[{"organization-name": "absa-group"}],
    )

    # Act
    result = GHUITestsCollector(str(output_dir)).collect()

    # Assert
    assert result is True
    assert mock_log_error.called


def test_collect_write_failure_returns_false(tmp_path, mocker):
    # Arrange
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    mocker.patch("ui_tests.collector.ActionInputs.get_ui_tests_repositories", return_value=[])
    mocker.patch("ui_tests.collector.open", side_effect=OSError("disk full"))

    # Act
    result = GHUITestsCollector(str(output_dir)).collect()

    # Assert
    assert result is False
