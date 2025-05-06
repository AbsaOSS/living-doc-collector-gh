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

from doc_issues.model.project_status import ProjectStatus
from utils.issue import Issue


def test_issue_initialization():
    # Arrange & Act
    issue = Issue(repository_id="TestOrg/TestRepo", title="Test Issue", number=42)

    # Assert
    assert issue.repository_id == "TestOrg/TestRepo"
    assert issue.title == "Test Issue"
    assert issue.issue_number == 42
    assert issue.state is None
    assert issue.created_at is None
    assert issue.updated_at is None
    assert issue.closed_at is None
    assert issue.html_url is None
    assert issue.body is None
    assert issue.labels is None
    assert issue.linked_to_project is None
    assert issue.project_statuses is None


def test_issue_to_dict():
    # Arrange
    issue = Issue(repository_id="TestOrg/TestRepo", title="Test Issue", number=42)
    issue.state = "OPEN"
    issue.created_at = "2025-01-01T00:00:00Z"
    issue.updated_at = "2025-01-01T00:00:00Z"
    issue.closed_at = "2025-01-01T00:00:00Z"
    issue.labels = ["bug", "urgent"]
    issue.body = "This is a body"
    issue.linked_to_project = False
    issue.html_url = "http://example.com"
    ps = ProjectStatus()
    ps.project_title = "Project A"
    ps.status = "In Progress"
    ps.priority = "High"
    ps.size = "Large"
    ps.moscow = "Must Have"
    issue.project_statuses = [ps]

    # Act
    result = issue.to_dict()

    # Assert
    assert result == {
        "repository_id": "TestOrg/TestRepo",
        "title": "Test Issue",
        "number": 42,
        "state": "OPEN",
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-01T00:00:00Z",
        "closed_at": "2025-01-01T00:00:00Z",
        "labels": ["bug", "urgent"],
        "body": "This is a body",
        "linked_to_project": False,
        "html_url": "http://example.com",
        "project_status": [
            {
                "project_title": "Project A",
                "status": "In Progress",
                "priority": "High",
                "size": "Large",
                "moscow": "Must Have",
            }
        ],
    }


def test_issue_from_dict():
    # Arrange
    data = {
        "repository_id": "TestOrg/TestRepo",
        "title": "Test Issue",
        "number": 42,
        "state": "OPEN",
        "created_at": "2025-01-01T00:00:00Z",
        "labels": ["bug", "urgent"],
        "project_status": [
            {
                "project_title": "Project A",
                "status": "In Progress",
                "priority": "High",
                "size": "Large",
                "moscow": "Must Have",
            }
        ],
    }

    # Act
    issue = Issue.from_dict(data)

    # Assert
    assert issue.repository_id == "TestOrg/TestRepo"
    assert issue.title == "Test Issue"
    assert issue.issue_number == 42
    assert issue.state == "OPEN"
    assert issue.created_at == "2025-01-01T00:00:00Z"
    assert issue.labels == ["bug", "urgent"]
    assert len(issue.project_statuses) == 1
    assert issue.project_statuses[0].project_title == "Project A"
    assert issue.project_statuses[0].status == "In Progress"


def test_issue_from_dict_no_project_data():
    # Arrange
    data = {
        "repository_id": "TestOrg/TestRepo",
        "title": "Test Issue",
        "number": 42,
        "state": "OPEN",
        "created_at": "2025-01-01T00:00:00Z",
        "labels": ["bug", "urgent"],
    }

    # Act
    issue = Issue.from_dict(data)

    # Assert
    assert issue.repository_id == "TestOrg/TestRepo"
    assert issue.title == "Test Issue"
    assert issue.issue_number == 42
    assert issue.state == "OPEN"
    assert issue.created_at == "2025-01-01T00:00:00Z"
    assert issue.labels == ["bug", "urgent"]
    assert issue.project_statuses is None


def test_issue_organization_name():
    # Arrange
    issue = Issue(repository_id="TestOrg/TestRepo", title="Test Issue", number=42)

    # Act
    org_name = issue.organization_name()

    # Assert
    assert org_name == "TestOrg"


def test_issue_repository_name():
    # Arrange
    issue = Issue(repository_id="TestOrg/TestRepo", title="Test Issue", number=42)

    # Act
    repo_name = issue.repository_name()

    # Assert
    assert repo_name == "TestRepo"
