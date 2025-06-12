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
from living_doc_utilities.model.project_status import ProjectStatus

from doc_issues.model.consolidated_issue import ConsolidatedIssue


def test_consolidated_issue_initialization():
    # Arrange, Act
    issue = ConsolidatedIssue("test_org/test_repo")

    # Assert
    assert issue.repository_id == "test_org/test_repo"
    assert issue.number == 0
    assert issue.title == ""
    assert issue.state == ""
    assert issue.labels == []
    assert issue.linked_to_project is False
    assert issue.project_issue_statuses == []
    assert issue.errors == {}
    assert issue.organization_name == "test_org"
    assert issue.repository_name == "test_repo"


def test_update_with_project_data():
    # Arrange
    issue = ConsolidatedIssue("test_org/test_repo")
    project_status = ProjectStatus()
    project_status.project_title = "Test Project"
    project_status.status = "In Progress"
    project_status.priority = "High"
    project_status.size = "Large"
    project_status.moscow = "Must Have"

    # Act
    issue.update_with_project_data(project_status)

    # Assert
    assert issue.linked_to_project is True
    assert len(issue.project_issue_statuses) == 1
    assert issue.project_issue_statuses[0] == project_status


#  to_issue_for_persist


def test_to_issue_for_persist(mocker):
    # Arrange
    mocker.patch.object(ConsolidatedIssue, "number", new_callable=mocker.PropertyMock, return_value=1)
    mocker.patch.object(ConsolidatedIssue, "title", new_callable=mocker.PropertyMock, return_value="Some title")
    consolidated_issue = ConsolidatedIssue("test_org/test_repo", repository_issue=None)

    # Act
    issue = consolidated_issue.convert_to_issue_for_persist()

    # Assert
    assert issue.repository_id == "test_org/test_repo"
    assert issue.title == "Some title"
    assert issue.issue_number == 1
    assert issue.state == ""
    assert issue.created_at == ""
    assert issue.updated_at == ""
    assert issue.closed_at == ""
    assert issue.html_url == ""
    assert issue.body == ""
    assert issue.labels == []
    assert issue.linked_to_project is False
    assert issue.project_statuses == []


def test_consolidated_issue_labels_fetches_from_issue_when_internal_empty(mocker):
    # Arrange
    issue = ConsolidatedIssue("test_org/test_repo")
    mock_label1 = mocker.Mock()
    mock_label1.name = "bug"
    mock_label2 = mocker.Mock()
    mock_label2.name = "enhancement"
    mock_github_issue = mocker.Mock()
    mock_github_issue.labels = [mock_label1, mock_label2]
    # Inject the mock GitHub issue
    issue._ConsolidatedIssue__issue = mock_github_issue
    issue._ConsolidatedIssue__issue_labels = []

    # Act
    result_1 = issue.labels       # get labels from mock github issue
    result_2 = issue.labels       # get labels from internal cache

    # Assert
    assert result_1 == ["bug", "enhancement"]
    assert result_2 == ["bug", "enhancement"]
