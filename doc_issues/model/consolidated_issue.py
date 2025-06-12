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

"""
This module contains a data container for Consolidated Issue, which holds all the essential logic.
"""
import logging
from typing import Optional, Any

from living_doc_utilities.factory.issue_factory import IssueFactory
from living_doc_utilities.model.issue import Issue
from living_doc_utilities.model.project_status import ProjectStatus

from github.Issue import Issue as GitHubIssue

logger = logging.getLogger(__name__)


class ConsolidatedIssue:
    """
    A class representing a consolidated issue from the repository and project data.
    It provides methods for updating project data and generating page filenames and
    properties to access consolidated issue details.
    """

    def __init__(self, repository_id: str, repository_issue: Optional[GitHubIssue] = None):
        # save issue from repository (got from GitHub library & keep connection to repository for lazy loading)
        # Warning: several issue properties require additional API calls - use wisely to keep low API usage
        self.__issue: Optional[GitHubIssue] = repository_issue
        self.__repository_id: str = repository_id

        self.issue_type: str = "Issue"

        # Extra project data (optionally provided from the GithubProjects class)
        self.__linked_to_project: bool = False
        self.__project_issue_statuses: list[ProjectStatus] = []

        # Labels of the issue - saved during mining to reduce API calls and protect against rate limits
        self.__issue_labels: list[str] = []

        self.__errors: dict[str, str] = {}

    # Issue properties
    @property
    def number(self) -> int:
        """Getter of the issue number."""
        return self.__issue.number if self.__issue else 0

    @property
    def repository_id(self) -> str:
        """Getter of the repository id."""
        return self.__repository_id

    @property
    def organization_name(self) -> str:
        """Getter of the organization where the issue was fetched from."""
        parts = self.__repository_id.split("/")
        return parts[0] if len(parts) == 2 else ""

    @property
    def repository_name(self) -> str:
        """Getter of the repository name where the issue was fetched from."""
        parts = self.__repository_id.split("/")
        return parts[1] if len(parts) == 2 else ""

    @property
    def title(self) -> str:
        """Getter of the issue title."""
        return self.__issue.title if self.__issue else ""

    @property
    def state(self) -> str:
        """Getter of the issue state."""
        return self.__issue.state if self.__issue else ""

    @property
    def created_at(self) -> str:
        """Getter of the info when issue was created."""
        return str(self.__issue.created_at) if self.__issue else ""

    @property
    def updated_at(self) -> str:
        """Getter of the info when issue was updated"""
        return str(self.__issue.updated_at) if self.__issue else ""

    @property
    def closed_at(self) -> str:
        """Getter of the info when issue was closed."""
        return str(self.__issue.closed_at) if self.__issue else ""

    @property
    def html_url(self) -> str:
        """Getter of the issue GitHub HTML URL."""
        return self.__issue.html_url if self.__issue else ""

    @property
    def body(self) -> str:
        """Getter of the issue description."""
        return self.__issue.body if self.__issue else ""

    @property
    def labels(self) -> list[str]:
        """Getter of the issue labels."""
        if self.__issue_labels:
            return self.__issue_labels

        if self.__issue:
            self.__issue_labels = [label.name for label in self.__issue.labels]
        return self.__issue_labels

    # Project properties
    @property
    def linked_to_project(self) -> bool:
        """Getter of the info if the issue is linked to a project."""
        return self.__linked_to_project

    @property
    def project_issue_statuses(self) -> list[ProjectStatus]:
        """Getter of the project issue statuses."""
        return self.__project_issue_statuses

    @property
    def errors(self) -> dict[str, str]:
        """Getter of the errors that occurred during the issue processing."""
        return self.__errors

    def update_with_project_data(self, project_issue_status: ProjectStatus) -> None:
        """
        Update the consolidated issue with Project Status data.

        @param project_issue_status: The extra issue project data per project.
        @return: None
        """
        self.__linked_to_project = True
        self.__project_issue_statuses.append(project_issue_status)

    def convert_to_issue_for_persist(self) -> Issue:
        """
        Convert the consolidated issue to a standard Issue object for persistence.

        @return: The converted Issue.
        """
        values: dict[str, Any] = {
            Issue.REPOSITORY_ID: self.repository_id,
            Issue.TITLE: self.title,
            Issue.ISSUE_NUMBER: self.number,
        }

        issue = IssueFactory.get(self.issue_type, values)
        issue.state = self.state
        issue.created_at = self.created_at
        issue.updated_at = self.updated_at
        issue.closed_at = self.closed_at
        issue.html_url = self.html_url
        issue.body = self.body
        issue.labels = self.labels

        issue.linked_to_project = self.linked_to_project
        issue.project_statuses = self.project_issue_statuses

        issue.add_errors(errors=self.errors)

        return issue
