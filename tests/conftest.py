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
import datetime
import time
import pytest
from github import Github
from github.Rate import Rate
from github.RateLimit import RateLimit
from github.Repository import Repository

from doc_issues.collector import GHDocIssuesCollector
from doc_issues.model.config_repository import ConfigRepository
from doc_issues.model.consolidated_issue import ConsolidatedIssue
from doc_issues.model.github_project import GitHubProject
from utils.constants import OUTPUT_PATH
from utils.github_rate_limiter import GithubRateLimiter
from utils.issue import Issue
from utils.utils import make_absolute_path


@pytest.fixture
def rate_limiter(mocker, request):
    mock_github_client = mocker.Mock(spec=Github)
    mock_github_client.get_rate_limit.return_value = request.getfixturevalue("mock_rate_limiter")
    return GithubRateLimiter(mock_github_client)


@pytest.fixture
def mock_rate_limiter(mocker):
    mock_rate = mocker.Mock(spec=Rate)
    mock_rate.timestamp = mocker.Mock(return_value=time.time() + 3600)

    mock_core = mocker.Mock(spec=RateLimit)
    mock_core.reset = mock_rate

    mock = mocker.Mock(spec=GithubRateLimiter)
    mock.core = mock_core
    mock.core.remaining = 10

    return mock


@pytest.fixture
def mock_logging_setup(mocker):
    mock_log_config = mocker.patch("logging.basicConfig")
    yield mock_log_config


@pytest.fixture
def github_project_setup(mocker):
    project = mocker.Mock(spec=GitHubProject)
    project_json = {"id": "123", "number": 1, "title": "Test Project"}

    repository = mocker.Mock(spec=Repository)
    repository.owner.login = "organizationABC"
    repository.full_name = "organizationABC/repoABC"

    field_option_response = {}
    project.loads(project_json, repository, field_option_response)

    return project


@pytest.fixture
def repository_setup(mocker):
    repository = mocker.Mock(spec=Repository)
    repository.owner.login = "test_owner"
    repository.name = "test_repo"
    repository.full_name = "test_owner/test_repo"
    repository.get_issues.return_value = []

    return repository


@pytest.fixture
def doc_issues_collector(mocker):
    mock_github_class = mocker.patch("doc_issues.collector.Github")
    mock_github_instance = mock_github_class.return_value

    mock_rate_limit = mocker.Mock()
    mock_rate_limit.remaining = 5000
    mock_rate_limit.reset = datetime.datetime.now() + datetime.timedelta(minutes=10)

    mock_github_instance.get_rate_limit.return_value = mocker.Mock(core=mock_rate_limit)
    mock_github_instance.get_repo.return_value = mocker.Mock()

    mocker.patch(
        "doc_issues.collector.ActionInputs.get_github_token",
        return_value="FakeGithubToken",
    )
    return GHDocIssuesCollector(make_absolute_path(OUTPUT_PATH))


@pytest.fixture
def config_repository(mocker):
    config_repository = mocker.Mock(spec=ConfigRepository)
    config_repository.organization_name = "test_org"
    config_repository.repository_name = "test_repo"
    config_repository.projects_title_filter = []
    config_repository.full_name = "test_org/test_repo"

    return config_repository


@pytest.fixture
def consolidated_issue(mocker):
    consolidated_issue = mocker.Mock(spec=ConsolidatedIssue)
    consolidated_issue.repository_id = "TestOrg/TestRepo"
    consolidated_issue.organization_name = "TestOrg"
    consolidated_issue.repository_name = "TestRepo"
    consolidated_issue.number = 42
    consolidated_issue.title = "Sample Issue"
    consolidated_issue.state = "OPEN"
    consolidated_issue.html_url = "https://github.com/TestOrg/TestRepo/issues/42"
    consolidated_issue.created_at = "2024-01-01T00:00:00Z"
    consolidated_issue.updated_at = "2024-01-02T00:00:00Z"
    consolidated_issue.closed_at = None
    consolidated_issue.labels = ["bug", "urgent"]
    consolidated_issue.body = "This is the issue content."
    consolidated_issue.linked_to_project = False
    consolidated_issue.errors = {}
    consolidated_issue.project_issue_statuses = [
        mocker.Mock(
            project_title="Project A",
            status="In Progress",
            priority="High",
            size="Large",
            moscow="Must Have",
        )
    ]

    return consolidated_issue


@pytest.fixture
def sample_issues():
    issue1 = Issue(repository_id="TestOrg/TestRepo", title="Issue 1", number=1)
    issue2 = Issue(repository_id="TestOrg/TestRepo", title="Issue 2", number=2)
    return {"1": issue1, "2": issue2}
