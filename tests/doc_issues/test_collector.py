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
from tkinter.filedialog import dialogstates

from doc_issues.collector import GHDocIssuesCollector
from doc_issues.model.consolidated_issue import ConsolidatedIssue
from doc_issues.model.project_issue import ProjectIssue
from github import Issue

from living_doc_utilities.model.issues import Issues
from utils.constants import DOC_USER_STORY_LABEL, DOC_FEATURE_LABEL, DOC_FUNCTIONALITY_LABEL


# collect


def test_collect_correct_behaviour(mocker, doc_issues_collector):
    # Arrange
    mock_clean_output_directory = mocker.patch.object(doc_issues_collector, "_clean_output_directory")
    mock_logger_info = mocker.patch("doc_issues.collector.logger.info")
    mock_logger_debug = mocker.patch("doc_issues.collector.logger.debug")

    mock_issue = mocker.Mock()
    project_issue_mock = mocker.Mock()
    consolidated_issue_mock = mocker.Mock()

    mock_fetch_github_issues = mocker.patch.object(
        doc_issues_collector, "_fetch_github_issues", return_value={"test_org/test_repo": [mock_issue]}
    )
    mock_fetch_github_project_issues = mocker.patch.object(
        doc_issues_collector,
        "_fetch_github_project_issues",
        return_value={"test_org/test_repo#1": [project_issue_mock]},
    )
    mock_consolidate_issues_data = mocker.patch.object(
        doc_issues_collector,
        "_consolidate_issues_data",
        return_value={"test_org/test_repo#1": consolidated_issue_mock},
    )

    mock_store_consolidated_issues = mocker.patch.object(
        doc_issues_collector,
        "_store_consolidated_issues",
        return_value=True,
    )

    # Act
    doc_issues_collector.collect()

    # Assert
    mock_clean_output_directory.assert_called_once()
    mock_fetch_github_issues.assert_called_once()
    mock_fetch_github_project_issues.assert_called_once()
    mock_consolidate_issues_data.assert_called_once_with(
        {"test_org/test_repo": [mock_issue]}, {"test_org/test_repo#1": [project_issue_mock]}
    )
    # mock_generate_markdown_pages.assert_called_once_with({"test_org/test_repo#1": consolidated_issue_mock})
    mock_logger_debug.assert_called_once_with("'doc-issues' mode output directory cleaned.")
    mock_logger_info.assert_has_calls(
        [
            mocker.call("Fetching repository GitHub issues - started."),
            mocker.call("Fetching repository GitHub issues - finished."),
            mocker.call("Fetching GitHub project data - started."),
            mocker.call("Fetching GitHub project data - finished."),
            mocker.call("Issue and project data consolidation - started."),
            mocker.call("Issue and project data consolidation - finished."),
            mocker.call("Exporting consolidated issues - started."),
            mocker.call("Exporting consolidated issues - finished."),
        ],
        any_order=True,
    )


def test_collect_returns_false_when_store_fails(mocker, doc_issues_collector):
    # Arrange
    mocker.patch.object(doc_issues_collector, "_clean_output_directory")
    mocker.patch.object(doc_issues_collector, "_fetch_github_issues", return_value={})
    mocker.patch.object(doc_issues_collector, "_fetch_github_project_issues", return_value={})
    mocker.patch.object(doc_issues_collector, "_consolidate_issues_data", return_value={})
    mocker.patch.object(doc_issues_collector, "_store_consolidated_issues", return_value=False)

    # Act
    result = doc_issues_collector.collect()

    # Assert
    assert result is False


# _clean_output_directory


def test_clean_output_directory_correct_behaviour(mocker, doc_issues_collector):
    # Arrange
    mock_exists = mocker.patch("os.path.exists", return_value=True)
    mock_rmtree = mocker.patch("shutil.rmtree")
    mock_makedirs = mocker.patch("os.makedirs")

    # Act
    doc_issues_collector._clean_output_directory()

    # Assert
    mock_exists.assert_called_once()
    mock_rmtree.assert_called_once()
    mock_makedirs.assert_called_once()


# _fetch_github_issues


def test_fetch_github_issues_success(mocker, config_repository, repository_setup, doc_issues_collector):
    mocker.patch(
        "doc_issues.collector.ActionInputs.get_repositories",
        return_value=[config_repository],
    )
    mock_get_repo = mocker.patch.object(
        doc_issues_collector._GHDocIssuesCollector__github_instance,
        "get_repo",
        return_value=repository_setup,
    )

    # Act
    actual = doc_issues_collector._fetch_github_issues()

    # Assert
    assert {'test_org/test_repo': []} == actual



def test_fetch_github_issues_repository_none(mocker, doc_issues_collector, config_repository):
    # Arrange
    mock_get_repo = doc_issues_collector._GHDocIssuesCollector__github_instance.get_repo
    mock_get_repo.return_value = None
    mocker.patch(
        "doc_issues.collector.ActionInputs.get_repositories",
        return_value=[config_repository],
    )

    # Act
    actual = doc_issues_collector._fetch_github_issues()

    # Assert
    assert {} == actual
    mock_get_repo.assert_called_once_with("test_org/test_repo")


# _fetch_github_project_issues


def test_fetch_github_project_issues_correct_behaviour(mocker, doc_issues_collector):
    # Arrange
    mocker.patch(
        "doc_issues.collector.ActionInputs.is_project_state_mining_enabled",
        return_value=True,
    )
    mock_logger_info = mocker.patch("doc_issues.collector.logger.info")
    mock_logger_debug = mocker.patch("doc_issues.collector.logger.debug")

    repository_1 = mocker.Mock()
    repository_1.organization_name = "OrgA"
    repository_1.repository_name = "RepoA"
    repository_1.projects_title_filter = ""

    repository_2 = mocker.Mock()
    repository_2.organization_name = "OrgA"
    repository_2.repository_name = "RepoB"
    repository_2.projects_title_filter = "ProjectB"

    mocker.patch(
        "doc_issues.collector.ActionInputs.get_repositories",
        return_value=[repository_1, repository_2],
    )

    mock_github_projects_instance = mocker.patch.object(
        doc_issues_collector, "_GHDocIssuesCollector__github_projects_instance"
    )

    repo_a = mocker.Mock()
    repo_a.full_name = "OrgA/RepoA"
    repo_b = mocker.Mock()
    repo_b.full_name = "OrgA/RepoB"
    doc_issues_collector._GHDocIssuesCollector__github_instance.get_repo.side_effect = [
        repo_a,
        repo_b,
    ]

    project_a = mocker.Mock(title="Project A")
    project_b = mocker.Mock(title="Project B")
    mock_github_projects_instance.get_repository_projects.side_effect = [[project_a], [project_b]]

    project_status_1 = mocker.Mock()
    project_status_1.status = "In Progress"

    project_status_2 = mocker.Mock()
    project_status_2.status = "Done"

    project_issue_1 = mocker.Mock(spec=ProjectIssue)
    project_issue_1.organization_name = "OrgA"
    project_issue_1.repository_name = "RepoA"
    project_issue_1.number = 1
    project_issue_1.project_status = project_status_1

    # By creating two same Project Issues (same unique issue key) that has different project statuses
    # we test the situation where one issue is linked to more projects (need of keeping all project statuses)
    project_issue_2 = mocker.Mock(spec=ProjectIssue)
    project_issue_2.organization_name = "OrgA"
    project_issue_2.repository_name = "RepoA"
    project_issue_2.number = 1
    project_issue_2.project_status = project_status_2

    mock_github_projects_instance.get_project_issues.side_effect = [[project_issue_1], [project_issue_2]]

    mock_make_issue_key = mocker.patch(
        "living_doc_utilities.model.issues.Issues.make_issue_key",
        side_effect=lambda org, repo, num: f"{org}/{repo}#{num}",
    )

    # Act
    actual = doc_issues_collector._fetch_github_project_issues()

    # Assert
    assert mock_make_issue_key.call_count == 2
    assert len(actual) == 1
    assert "OrgA/RepoA#1" in actual
    assert actual["OrgA/RepoA#1"] == [project_issue_1, project_issue_2]

    doc_issues_collector._GHDocIssuesCollector__github_instance.get_repo.assert_any_call("OrgA/RepoA")
    doc_issues_collector._GHDocIssuesCollector__github_instance.get_repo.assert_any_call("OrgA/RepoB")
    mock_github_projects_instance.get_repository_projects.assert_any_call(repository=repo_a, projects_title_filter="")
    mock_github_projects_instance.get_repository_projects.assert_any_call(
        repository=repo_b, projects_title_filter="ProjectB"
    )
    mock_github_projects_instance.get_project_issues.assert_any_call(project=project_a)
    mock_github_projects_instance.get_project_issues.assert_any_call(project=project_b)
    mock_logger_info.assert_has_calls(
        [
            mocker.call("Fetching GitHub project data - for repository `%s` found `%i` project/s.", "OrgA/RepoA", 1),
            mocker.call("Fetching GitHub project data - fetching project data from `%s`.", "Project A"),
            mocker.call("Fetching GitHub project data - successfully fetched project data from `%s`.", "Project A"),
            mocker.call("Fetching GitHub project data - for repository `%s` found `%i` project/s.", "OrgA/RepoB", 1),
            mocker.call("Fetching GitHub project data - fetching project data from `%s`.", "Project B"),
            mocker.call("Fetching GitHub project data - successfully fetched project data from `%s`.", "Project B"),
        ],
        any_order=True,
    )
    mock_logger_debug.assert_has_calls(
        [
            mocker.call("Project data mining allowed."),
            mocker.call("Filtering projects: %s. If filter is empty, fetching all.", ""),
            mocker.call("Filtering projects: %s. If filter is empty, fetching all.", "ProjectB"),
            mocker.call("Fetching GitHub project data - looking for repository `%s` projects.", "OrgA/RepoA"),
            mocker.call("Fetching GitHub project data - looking for repository `%s` projects.", "OrgA/RepoB"),
        ],
        any_order=True,
    )


def test_fetch_github_project_issues_project_mining_disabled(mocker, doc_issues_collector):
    # Arrange
    mock_get_project_mining_enabled = mocker.patch(
        "doc_issues.collector.ActionInputs.is_project_state_mining_enabled",
        return_value=False,
    )
    mock_logger_info = mocker.patch("doc_issues.collector.logger.info")

    # Act
    actual = doc_issues_collector._fetch_github_project_issues()

    # Assert
    assert {} == actual
    mock_get_project_mining_enabled.assert_called_once()
    mock_logger_info.assert_called_once_with("Fetching GitHub project data - project mining is not allowed.")


def test_fetch_github_project_issues_no_repositories(mocker, doc_issues_collector, config_repository):
    # Arrange
    mock_get_repo = doc_issues_collector._GHDocIssuesCollector__github_instance.get_repo
    mock_get_repo.return_value = None

    mocker.patch(
        "doc_issues.collector.ActionInputs.is_project_state_mining_enabled",
        return_value=True,
    )
    mocker.patch(
        "doc_issues.collector.ActionInputs.get_repositories",
        return_value=[config_repository],
    )

    # Act
    actual = doc_issues_collector._fetch_github_project_issues()

    # Assert
    assert {} == actual
    mock_get_repo.assert_called_once_with("test_org/test_repo")


def test_fetch_github_project_issues_with_no_projects(mocker, doc_issues_collector, config_repository):
    # Arrange
    mock_get_repo = doc_issues_collector._GHDocIssuesCollector__github_instance.get_repo
    repo_a = mocker.Mock()
    repo_a.full_name = "test_org/test_repo"
    mock_get_repo.return_value = repo_a

    mocker.patch(
        "doc_issues.collector.ActionInputs.is_project_state_mining_enabled",
        return_value=True,
    )
    mocker.patch(
        "doc_issues.collector.ActionInputs.get_repositories",
        return_value=[config_repository],
    )
    mock_logger_info = mocker.patch("doc_issues.collector.logger.info")
    mock_get_repository_projects = mocker.patch.object(
        doc_issues_collector._GHDocIssuesCollector__github_projects_instance,
        "get_repository_projects",
        return_value=[],
    )

    # Act
    actual = doc_issues_collector._fetch_github_project_issues()

    # Assert
    assert {} == actual
    mock_get_repo.assert_called_once_with("test_org/test_repo")
    mock_get_repository_projects.assert_called_once_with(repository=repo_a, projects_title_filter=[])
    mock_logger_info.assert_called_once_with(
        "Fetching GitHub project data - no project data found for repository `%s`.", "test_org/test_repo"
    )


# _consolidate_issues_data


def test__consolidate_issues_data_sets_type_and_updates_project(mocker):
    # --- Arrange ---
    # Mock a GitHub issue
    github_issue_us = mocker.Mock()
    github_issue_us.number = 42
    label_mock_us = mocker.Mock()
    label_mock_us.name = DOC_USER_STORY_LABEL
    github_issue_us.labels = [label_mock_us]

    github_issue_feat = mocker.Mock()
    github_issue_feat.number = 43
    label_mock_feat = mocker.Mock()
    label_mock_feat.name = DOC_FEATURE_LABEL
    github_issue_feat.labels = [label_mock_feat]

    github_issue_func = mocker.Mock()
    github_issue_func.number = 44
    label_mock_func = mocker.Mock()
    label_mock_func.name = DOC_FUNCTIONALITY_LABEL
    github_issue_func.labels = [label_mock_func]

    repository_issues = {
        "TestOrg/TestRepo": [github_issue_us, github_issue_feat, github_issue_func, github_issue_func]
    }

    # Mock a ProjectIssue
    project_issue = mocker.Mock()
    project_issue.project_status = "In Progress"
    project_issues = {
        "TestOrg/TestRepo/42": [project_issue]
    }

    # Patch make_issue_key to produce known key
    mocker.patch.object(Issues, "make_issue_key", side_effect=lambda org, repo, number: f"{org}/{repo}/{number}")

    # Patch logger
    mock_logger_info = mocker.patch("doc_issues.collector.logger.info")
    mock_logger_debug = mocker.patch("doc_issues.collector.logger.debug")

    # --- Act ---
    result = GHDocIssuesCollector._consolidate_issues_data(repository_issues, project_issues)

    # --- Assert ---
    assert "TestOrg/TestRepo/42" in result
    issue_us = result["TestOrg/TestRepo/42"]
    issue_feat = result["TestOrg/TestRepo/43"]
    issue_func = result["TestOrg/TestRepo/44"]
    assert isinstance(issue_us, ConsolidatedIssue)
    assert issue_us.issue_type == "UserStoryIssue"
    assert issue_us.project_issue_statuses == ["In Progress"]
    assert issue_feat.issue_type == "FeatureIssue"
    assert issue_func.issue_type == "FunctionalityIssue"

    mock_logger_debug.assert_called_once_with("Updating consolidated issue structure with project data.")
    mock_logger_info.assert_called_once_with(
        "Issue and project data consolidation - consolidated `%i` repository issues with extra project data.", 3
    )

# _store_consolidated_issues


def test_store_consolidated_issues_correct_behaviour(mocker, doc_issues_collector):
    # Arrange
    class FakeGitHubIssue:
        number = 1
        title = "Test title"
        state = "open"
        created_at = "2023-01-01"
        updated_at = "2023-01-02"
        closed_at = None
        html_url = "https://github.com/test/repo/issues/1"
        body = "Issue body"
        labels = []

    # Create real ConsolidatedIssue instances with the fake GitHub issue
    issue1 = ConsolidatedIssue("test_org/test_repo", FakeGitHubIssue())
    issue2 = ConsolidatedIssue("test_org/test_repo", FakeGitHubIssue())

    issue1.issue_type = "UserStoryIssue"
    issue2.issue_type = "UserStoryIssue"

    consolidated_issues = {
        "test_org/test_repo#1": issue1,
        "test_org/test_repo#2": issue2,
    }

    mock_logger_info = mocker.patch("doc_issues.collector.logger.info")
    mock_logger_error = mocker.patch("doc_issues.collector.logger.error")
    mock_save_to_json = mocker.patch("living_doc_utilities.model.issues.Issues.save_to_json")

    # Act
    doc_issues_collector._store_consolidated_issues(consolidated_issues)

    # Assert
    mock_save_to_json.assert_called_once()
    assert mock_save_to_json.call_args[0][0].endswith("doc-issues.json")
    assert mock_logger_info.call_count == 1
    mock_logger_error.assert_not_called()


def test_store_consolidated_issues_not_valid(mocker, doc_issues_collector):
    # Arrange
    class FakeGitHubIssue:
        number = 1
        title = "Test title"
        state = "open"
        created_at = "2023-01-01"
        updated_at = "2023-01-02"
        closed_at = None
        html_url = "https://github.com/test/repo/issues/1"
        body = "Issue body"
        labels = []

    # Create real ConsolidatedIssue instances with the fake GitHub issue
    issue1 = ConsolidatedIssue("test_org/test_repo", FakeGitHubIssue())
    issue2 = ConsolidatedIssue("test_org/test_repo", FakeGitHubIssue())
    gh_issue = FakeGitHubIssue()
    gh_issue.title = None
    issue3 = ConsolidatedIssue("test_org/test_repo", gh_issue)

    issue1.issue_type = "UserStoryIssue"
    issue2.issue_type = "UserStoryIssue"

    consolidated_issues = {
        "test_org/test_repo#1": issue1,
        "test_org/test_repo#2": issue2,
        "test_org/test_repo#3": issue3,
    }

    mock_logger_info = mocker.patch("doc_issues.collector.logger.info")
    mock_logger_error = mocker.patch("doc_issues.collector.logger.error")
    mock_save_to_json = mocker.patch("living_doc_utilities.model.issues.Issues.save_to_json")

    # Act
    doc_issues_collector._store_consolidated_issues(consolidated_issues)

    # Assert
    mock_save_to_json.assert_called_once()
    assert mock_save_to_json.call_args[0][0].endswith("doc-issues.json")
    assert mock_logger_info.call_count == 1
    assert mock_logger_error.call_count == 2
    mock_logger_error.assert_has_calls(
        [
            mocker.call("Issue with key `%s` is not valid (Repository ID, title and issue_number have to be defined). Skipping issue.", "test_org/test_repo#3"),
            mocker.call("Exporting consolidated issues - some issues have errors."),
        ],
        any_order=True,
    )
