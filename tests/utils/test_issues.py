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
import os.path

from utils.issue import Issue
from utils.issues import Issues


def test_issues_initialization(sample_issues):
    # Arrange & Act
    issues = Issues(sample_issues)

    # Assert
    assert issues.count() == 2
    assert issues.get_issue("1").title == "Issue 1"
    assert issues.get_issue("2").title == "Issue 2"


def test_add_issue(sample_issues):
    # Arrange
    issues = Issues(sample_issues)
    new_issue = Issue(repository_id="TestOrg/TestRepo", title="Issue 3", number=3)

    # Act
    issues.add_issue("3", new_issue)

    # Assert
    assert issues.count() == 3
    assert issues.get_issue("3").title == "Issue 3"


def test_get_issue(sample_issues):
    # Arrange
    issues = Issues(sample_issues)

    # Act
    issue = issues.get_issue("1")

    # Assert
    assert issue.title == "Issue 1"
    assert issue.issue_number == 1


def test_all_issues(sample_issues):
    # Arrange
    issues = Issues(sample_issues)

    # Act
    all_issues = issues.all_issues()

    # Assert
    assert len(all_issues) == 2
    assert all_issues["1"].title == "Issue 1"
    assert all_issues["2"].title == "Issue 2"


def test_count(sample_issues):
    # Arrange
    issues = Issues(sample_issues)

    # Act
    count = issues.count()

    # Assert
    assert count == 2


def test_save_to_json_path(tmp_path, sample_issues):
    # Arrange
    issues = Issues(sample_issues)
    file_path = tmp_path / "issues.json"

    # Act
    issues.save_to_json(file_path)

    # Assert
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert len(data) == 2
    assert data["1"]["title"] == "Issue 1"
    assert data["2"]["title"] == "Issue 2"


def test_load_from_json(tmp_path, sample_issues):
    # Arrange
    file_path = tmp_path / "issues.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "1": {"repository_id": "TestOrg/TestRepo", "title": "Issue 1", "number": 1},
                "2": {"repository_id": "TestOrg/TestRepo", "title": "Issue 2", "number": 2},
            },
            f,
            indent=4,
        )

    # Act
    issues = Issues.load_from_json(file_path)

    # Assert
    assert issues.count() == 2
    assert issues.get_issue("1").title == "Issue 1"
    assert issues.get_issue("2").title == "Issue 2"
