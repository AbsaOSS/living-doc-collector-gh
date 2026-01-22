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


# Audit data tests


def test_get_audit_data_with_no_github_issue():
    # Arrange
    issue = ConsolidatedIssue("test_org/test_repo", repository_issue=None)

    # Act
    audit_data = issue.get_audit_data()

    # Assert
    assert audit_data == {}


def test_get_audit_data_with_creator_and_closer(mocker):
    # Arrange
    mock_user = mocker.Mock()
    mock_user.login = "test_creator"
    mock_closer = mocker.Mock()
    mock_closer.login = "test_closer"

    mock_github_issue = mocker.Mock()
    mock_github_issue.user = mock_user
    mock_github_issue.closed_by = mock_closer
    mock_github_issue.comments = 0

    issue = ConsolidatedIssue("test_org/test_repo", repository_issue=mock_github_issue)

    # Act
    audit_data = issue.get_audit_data()

    # Assert
    assert audit_data["created_by"] == "test_creator"
    assert audit_data["closed_by"] == "test_closer"


def test_get_audit_data_with_comments(mocker):
    # Arrange
    mock_user = mocker.Mock()
    mock_user.login = "test_creator"

    mock_comment_user = mocker.Mock()
    mock_comment_user.login = "commenter"
    mock_comment = mocker.Mock()
    mock_comment.created_at = "2025-01-20T12:00:00"
    mock_comment.user = mock_comment_user

    mock_github_issue = mocker.Mock()
    mock_github_issue.user = mock_user
    mock_github_issue.closed_by = None
    mock_github_issue.comments = 1
    mock_github_issue.get_comments.return_value = [mock_comment]

    issue = ConsolidatedIssue("test_org/test_repo", repository_issue=mock_github_issue)

    # Act
    audit_data = issue.get_audit_data()

    # Assert
    assert audit_data["created_by"] == "test_creator"
    assert audit_data["comments_count"] == 1
    assert audit_data["last_commented_at"] == "2025-01-20T12:00:00"
    assert audit_data["last_commented_by"] == "commenter"


def test_get_audit_data_graceful_degradation_on_comment_fetch_error(mocker):
    # Arrange
    from github.GithubException import GithubException

    mock_user = mocker.Mock()
    mock_user.login = "test_creator"

    mock_github_issue = mocker.Mock()
    mock_github_issue.user = mock_user
    mock_github_issue.closed_by = None
    mock_github_issue.comments = 1
    mock_github_issue.get_comments.side_effect = GithubException(403, "API error", {})

    issue = ConsolidatedIssue("test_org/test_repo", repository_issue=mock_github_issue)

    # Act
    audit_data = issue.get_audit_data()

    # Assert - should have creator but not comment details
    assert audit_data["created_by"] == "test_creator"
    assert "last_commented_at" not in audit_data
    assert "last_commented_by" not in audit_data


def test_parse_timeline_event_labeled(mocker):
    # Arrange
    issue = ConsolidatedIssue("test_org/test_repo")

    mock_actor = mocker.Mock()
    mock_actor.login = "test_actor"
    mock_label = mocker.Mock()
    mock_label.name = "bug"

    mock_event = mocker.Mock()
    mock_event.event = "labeled"
    mock_event.created_at = "2025-01-20T12:00:00"
    mock_event.actor = mock_actor
    mock_event.label = mock_label

    # Act
    result = issue._parse_timeline_event(mock_event)  # pylint: disable=protected-access

    # Assert
    assert result is not None
    assert result["action"] == "labeled"
    assert result["timestamp"] == "2025-01-20T12:00:00"
    assert result["actor"] == "test_actor"
    assert result["label"] == "bug"


def test_parse_timeline_event_assigned(mocker):
    # Arrange
    issue = ConsolidatedIssue("test_org/test_repo")

    mock_actor = mocker.Mock()
    mock_actor.login = "test_actor"
    mock_assignee = mocker.Mock()
    mock_assignee.login = "assignee_user"

    mock_event = mocker.Mock()
    mock_event.event = "assigned"
    mock_event.created_at = "2025-01-20T12:00:00"
    mock_event.actor = mock_actor
    mock_event.assignee = mock_assignee

    # Act
    result = issue._parse_timeline_event(mock_event)  # pylint: disable=protected-access

    # Assert
    assert result is not None
    assert result["action"] == "assigned"
    assert result["timestamp"] == "2025-01-20T12:00:00"
    assert result["actor"] == "test_actor"
    assert result["assignee"] == "assignee_user"


def test_parse_timeline_event_milestoned(mocker):
    # Arrange
    issue = ConsolidatedIssue("test_org/test_repo")

    mock_actor = mocker.Mock()
    mock_actor.login = "test_actor"
    mock_milestone = mocker.Mock()
    mock_milestone.title = "v1.0"

    mock_event = mocker.Mock()
    mock_event.event = "milestoned"
    mock_event.created_at = "2025-01-20T12:00:00"
    mock_event.actor = mock_actor
    mock_event.milestone = mock_milestone

    # Act
    result = issue._parse_timeline_event(mock_event)  # pylint: disable=protected-access

    # Assert
    assert result is not None
    assert result["action"] == "milestoned"
    assert result["timestamp"] == "2025-01-20T12:00:00"
    assert result["actor"] == "test_actor"
    assert result["milestone"] == "v1.0"


def test_parse_timeline_event_irrelevant_event(mocker):
    # Arrange
    issue = ConsolidatedIssue("test_org/test_repo")

    mock_event = mocker.Mock()
    mock_event.event = "commented"  # Not in relevant_events

    # Act
    result = issue._parse_timeline_event(mock_event)  # pylint: disable=protected-access

    # Assert
    assert result is None


def test_fetch_audit_events_timeline_unavailable(mocker):
    # Arrange
    from github.GithubException import GithubException

    mock_github_issue = mocker.Mock()
    mock_github_issue.get_timeline.side_effect = GithubException(403, "Timeline not available", {})

    issue = ConsolidatedIssue("test_org/test_repo", repository_issue=mock_github_issue)

    # Act
    events = issue._fetch_audit_events()  # pylint: disable=protected-access

    # Assert - should return empty list gracefully
    assert events == []

